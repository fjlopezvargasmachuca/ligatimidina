from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from handicaps.models import Handicap
from handicaps.services import HandicapService

from .models import Elimination, Match, MatchPlayer


def _lock_and_validate_weekly_event_bonus(*, match, player, exclude_pk=None):
    """Serializa la concesión del bonus para evitar dobles premios concurrentes."""
    week_model = type(match.league_week)
    week_model.objects.select_for_update().get(pk=match.league_week_id)
    queryset = MatchPlayer.objects.filter(
        player=player,
        match__league_week_id=match.league_week_id,
        participates_in_weekly_event=True,
    )
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.exists():
        raise serializers.ValidationError({
            "participates_in_weekly_event": (
                "La bonificación del evento semanal solo puede concederse una vez "
                "por jugador y jornada."
            )
        })


class MatchPlayerSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(
        source="player.display_name",
        read_only=True,
    )
    deck_name_snapshot = serializers.CharField(
        source="deck_name",
        read_only=True,
    )
    commander_name_snapshot = serializers.CharField(
        source="commander_name",
        read_only=True,
    )
    handicap_used = serializers.SerializerMethodField()
    handicap_used_name = serializers.SerializerMethodField()

    class Meta:
        model = MatchPlayer
        fields = [
            "id",
            "player",
            "player_name",
            "deck",
            "deck_name_snapshot",
            "commander_name_snapshot",
            "starting_position",
            "final_position",
            "first_play_of_deck",
            "participates_in_weekly_event",
            "conceded",
            "concession_penalty",
            "extra_points",
            "extra_points_reason",
            "points",
            "notes",
            "handicap_used",
            "handicap_used_name",
        ]
        read_only_fields = [
            "id",
            "player_name",
            "deck_name_snapshot",
            "commander_name_snapshot",
            "points",
            "handicap_used",
            "handicap_used_name",
        ]

    def get_handicap_used(self, obj):
        usage = getattr(obj, "handicap_usage", None)
        return usage.handicap_id if usage else None

    def get_handicap_used_name(self, obj):
        usage = getattr(obj, "handicap_usage", None)
        return usage.handicap.name_snapshot if usage else None


class MatchPlayerUpdateSerializer(serializers.ModelSerializer):
    used_handicap = serializers.PrimaryKeyRelatedField(
        source="_used_handicap",
        queryset=Handicap.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    completed_weekly_event = serializers.BooleanField(
        source="participates_in_weekly_event",
        required=False,
        write_only=True,
        help_text="Alias temporal compatible con la versión anterior de la API.",
    )

    class Meta:
        model = MatchPlayer
        fields = [
            "id",
            "starting_position",
            "final_position",
            "first_play_of_deck",
            "participates_in_weekly_event",
            "completed_weekly_event",
            "conceded",
            "concession_penalty",
            "extra_points",
            "extra_points_reason",
            "used_handicap",
            "points",
            "notes",
        ]
        read_only_fields = [
            "id",
            "points",
        ]

    def validate(self, attrs):
        match = self.context["match"]

        if match.closed:
            raise serializers.ValidationError(
                "No se puede modificar una partida cerrada."
            )

        if match.league_week.closed:
            raise serializers.ValidationError(
                "No se puede modificar una partida de una jornada cerrada."
            )

        participates = attrs.get(
            "participates_in_weekly_event",
            getattr(self.instance, "participates_in_weekly_event", False),
        )
        if participates:
            already_awarded = MatchPlayer.objects.filter(
                player=self.instance.player,
                match__league_week=match.league_week,
                participates_in_weekly_event=True,
            ).exclude(pk=self.instance.pk).exists()
            if already_awarded:
                raise serializers.ValidationError({
                    "participates_in_weekly_event": (
                        "La bonificación del evento semanal solo puede concederse una vez "
                        "por jugador y jornada."
                    )
                })

        extra_points = attrs.get("extra_points", getattr(self.instance, "extra_points", 0))
        reason = attrs.get(
            "extra_points_reason",
            getattr(self.instance, "extra_points_reason", ""),
        ).strip()
        if extra_points != 0 and not reason:
            raise serializers.ValidationError(
                {
                    "extra_points_reason": (
                        "Indica el motivo cuando los puntos extra son distintos de cero."
                    )
                }
            )

        handicap = attrs.get("_used_handicap")
        if handicap is not None:
            if handicap.player_id != self.instance.player_id:
                raise serializers.ValidationError(
                    {"used_handicap": "El handicap no pertenece a este jugador."}
                )
            if handicap.season_id != match.league_week.season_id:
                raise serializers.ValidationError(
                    {"used_handicap": "El handicap no pertenece a esta temporada."}
                )

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        handicap = validated_data.pop("_used_handicap", serializers.empty)
        participates = validated_data.get(
            "participates_in_weekly_event",
            instance.participates_in_weekly_event,
        )
        if participates:
            _lock_and_validate_weekly_event_bonus(
                match=self.context["match"],
                player=instance.player,
                exclude_pk=instance.pk,
            )
        instance = super().update(instance, validated_data)

        if handicap is not serializers.empty:
            HandicapService.set_match_player_usage(
                match_player=instance,
                handicap=handicap,
                administrator=self.context["request"].user,
            )

        return instance


class EliminationSerializer(serializers.ModelSerializer):
    killer_name = serializers.CharField(
        source="killer.display_name",
        read_only=True,
    )
    victim_name = serializers.CharField(
        source="victim.display_name",
        read_only=True,
    )

    class Meta:
        model = Elimination
        fields = [
            "id",
            "killer",
            "killer_name",
            "victim",
            "victim_name",
            "turn",
            "first_elimination",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "killer_name",
            "victim_name",
            "created_at",
        ]

    def validate(self, attrs):
        killer = attrs.get("killer")
        victim = attrs.get("victim")

        if killer and victim and killer.id == victim.id:
            raise serializers.ValidationError(
                "Un jugador no puede eliminarse a sí mismo."
            )

        return attrs


class MatchListSerializer(serializers.ModelSerializer):
    league_week_number = serializers.IntegerField(
        source="league_week.number",
        read_only=True,
    )
    administrator_name = serializers.CharField(
        source="administrator.display_name",
        read_only=True,
    )
    player_count = serializers.IntegerField(
        source="players.count",
        read_only=True,
    )

    class Meta:
        model = Match
        fields = [
            "id",
            "league_week",
            "league_week_number",
            "administrator",
            "administrator_name",
            "played_at",
            "notes",
            "closed",
            "player_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "administrator",
            "administrator_name",
            "player_count",
            "closed",
            "created_at",
        ]


class MatchDetailSerializer(serializers.ModelSerializer):
    league_week_number = serializers.IntegerField(
        source="league_week.number",
        read_only=True,
    )
    administrator_name = serializers.CharField(
        source="administrator.display_name",
        read_only=True,
    )
    players = MatchPlayerSerializer(many=True, read_only=True)
    eliminations = EliminationSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "league_week",
            "league_week_number",
            "administrator",
            "administrator_name",
            "played_at",
            "notes",
            "closed",
            "players",
            "eliminations",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "administrator",
            "administrator_name",
            "league_week_number",
            "closed",
            "players",
            "eliminations",
            "created_at",
        ]


class MatchCreateSerializer(serializers.ModelSerializer):
    played_at = serializers.DateTimeField(required=False, default=serializers.CreateOnlyDefault(timezone.now))

    class Meta:
        model = Match
        fields = [
            "id",
            "league_week",
            "administrator",
            "played_at",
            "notes",
            "closed",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "administrator",
            "closed",
            "created_at",
        ]

    def validate_league_week(self, league_week):
        if league_week.closed:
            raise serializers.ValidationError(
                "No se pueden registrar partidas en una jornada cerrada."
            )
        return league_week

    def create(self, validated_data):
        request = self.context["request"]
        return Match.objects.create(
            administrator=request.user,
            **validated_data,
        )


class MatchPlayerCreateSerializer(serializers.ModelSerializer):
    used_handicap = serializers.PrimaryKeyRelatedField(
        source="_used_handicap",
        queryset=Handicap.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    completed_weekly_event = serializers.BooleanField(
        source="participates_in_weekly_event",
        required=False,
        write_only=True,
        help_text="Alias temporal compatible con la versión anterior de la API.",
    )

    class Meta:
        model = MatchPlayer
        fields = [
            "id",
            "player",
            "deck",
            "deck_name",
            "commander_name",
            "starting_position",
            "final_position",
            "first_play_of_deck",
            "participates_in_weekly_event",
            "completed_weekly_event",
            "conceded",
            "concession_penalty",
            "extra_points",
            "extra_points_reason",
            "used_handicap",
            "points",
            "notes",
        ]
        read_only_fields = [
            "id",
            "deck_name",
            "commander_name",
            "points",
        ]

    def validate(self, attrs):
        match = self.context["match"]

        if match.closed:
            raise serializers.ValidationError(
                "No se puede modificar una partida cerrada."
            )

        if match.league_week.closed:
            raise serializers.ValidationError(
                "No se puede modificar una partida de una jornada cerrada."
            )

        player = attrs["player"]
        deck = attrs["deck"]

        if not deck.active:
            raise serializers.ValidationError(
                {"deck": "No se puede utilizar un mazo inactivo."}
            )

        if deck.owner_id != player.id:
            raise serializers.ValidationError(
                {"deck": "El mazo debe pertenecer al jugador seleccionado."}
            )

        if MatchPlayer.objects.filter(match=match, player=player).exists():
            raise serializers.ValidationError(
                {"player": "Este jugador ya está registrado en la partida."}
            )

        # El límite depende de la modalidad global de la liga y, cuando hay
        # suscripción, de la modalidad del jugador.
        week_games = MatchPlayer.objects.filter(
            player=player,
            match__league_week=match.league_week,
        ).exclude(match=match).count()
        limit = player.weekly_match_limit(on_date=match.league_week.date)
        if week_games >= limit:
            raise serializers.ValidationError({
                "player": f"Límite semanal alcanzado: {limit} partida(s) en esta jornada."
            })

        if attrs.get("participates_in_weekly_event", False):
            already_awarded = MatchPlayer.objects.filter(
                player=player,
                match__league_week=match.league_week,
                participates_in_weekly_event=True,
            ).exclude(match=match).exists()
            if already_awarded:
                raise serializers.ValidationError({
                    "participates_in_weekly_event": (
                        "La bonificación del evento semanal solo puede concederse una vez "
                        "por jugador y jornada."
                    )
                })

        extra_points = attrs.get("extra_points", 0)
        reason = attrs.get("extra_points_reason", "").strip()
        if extra_points != 0 and not reason:
            raise serializers.ValidationError(
                {
                    "extra_points_reason": (
                        "Indica el motivo cuando los puntos extra son distintos de cero."
                    )
                }
            )

        handicap = attrs.get("_used_handicap")
        if handicap is not None:
            if handicap.player_id != player.id:
                raise serializers.ValidationError(
                    {"used_handicap": "El handicap no pertenece a este jugador."}
                )
            if handicap.season_id != match.league_week.season_id:
                raise serializers.ValidationError(
                    {"used_handicap": "El handicap no pertenece a esta temporada."}
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        match = self.context["match"]
        handicap = validated_data.pop("_used_handicap", serializers.empty)
        if validated_data.get("participates_in_weekly_event", False):
            _lock_and_validate_weekly_event_bonus(
                match=match,
                player=validated_data["player"],
            )
        instance = MatchPlayer.objects.create(
            match=match,
            **validated_data,
        )

        if handicap is not serializers.empty and handicap is not None:
            HandicapService.use_handicap(
                handicap=handicap,
                match_player=instance,
                administrator=self.context["request"].user,
            )

        return instance
