from rest_framework import serializers
from django.db.models import Max

from .models import LeagueSettings, LeagueWeek, PrizePoolMonth, ScoringRule, Season


class StandingSerializer(serializers.Serializer):
    position = serializers.IntegerField()
    player_id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    avatar = serializers.CharField(allow_null=True, required=False)
    points = serializers.IntegerField()
    games = serializers.IntegerField()
    wins = serializers.IntegerField()
    weeks = serializers.IntegerField()
    eliminations = serializers.IntegerField()
    penalties_count = serializers.IntegerField()
    penalty_points = serializers.IntegerField()
    status_icons = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )


class WeeklyEventSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    rules = serializers.CharField()
    extra_points = serializers.IntegerField()
    active = serializers.BooleanField()


class LeagueWeekSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.IntegerField()
    date = serializers.DateField()
    closed = serializers.BooleanField()
    weekly_event = WeeklyEventSerializer(allow_null=True)
    ends_on = serializers.SerializerMethodField()

    def get_ends_on(self, obj):
        from datetime import timedelta
        return obj.date + timedelta(days=6)


class LeagueWeekAdminSerializer(serializers.ModelSerializer):
    season_name = serializers.CharField(source="season.name", read_only=True)
    weekly_event_name = serializers.CharField(
        source="weekly_event.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = LeagueWeek
        fields = [
            "id",
            "season",
            "season_name",
            "number",
            "date",
            "weekly_event",
            "weekly_event_name",
            "closed",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "season",
            "season_name",
            "number",
            "date",
            "weekly_event_name",
            "closed",
            "created_at",
        ]


class LeagueWeekCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueWeek
        fields = ["season", "date", "weekly_event"]
        extra_kwargs = {"weekly_event": {"required": False, "allow_null": True}}

    def validate(self, attrs):
        season = attrs.get("season")
        date = attrs.get("date")
        if season is None:
            raise serializers.ValidationError({"season": "La temporada es obligatoria."})
        if date is None:
            raise serializers.ValidationError({"date": "La fecha de la jornada es obligatoria."})
        if season.finalized_at is not None:
            raise serializers.ValidationError({"season": "No se pueden añadir jornadas a una temporada finalizada."})
        if LeagueWeek.objects.filter(season=season, date=date).exists():
            raise serializers.ValidationError({"date": "Ya existe una jornada en esa fecha."})
        if season.end_date is not None and date > season.end_date:
            raise serializers.ValidationError({"date": "La jornada no puede quedar fuera de la temporada."})
        if date < season.start_date:
            raise serializers.ValidationError({"date": "La jornada no puede ser anterior al inicio de la temporada."})
        return attrs

    def create(self, validated_data):
        from .services import LeagueWeekService

        season = validated_data["season"]
        next_number = (
            LeagueWeek.objects.filter(season=season).aggregate(value=Max("number"))["value"] or 0
        ) + 1
        if not validated_data.get("weekly_event"):
            validated_data["weekly_event"] = LeagueWeekService._choose_balanced_event(season)
        return LeagueWeek.objects.create(number=next_number, **validated_data)


class PlayerDeckStatsSerializer(serializers.Serializer):
    deck_id = serializers.IntegerField()
    deck_name = serializers.CharField()
    commander = serializers.CharField()
    games = serializers.IntegerField()
    wins = serializers.IntegerField()
    points = serializers.IntegerField()
    win_conditions = serializers.IntegerField()


class PlayerHistorySerializer(serializers.Serializer):
    week_number = serializers.IntegerField()
    week_date = serializers.DateField()
    deck_id = serializers.IntegerField()
    deck_name = serializers.CharField()
    commander = serializers.CharField()
    final_position = serializers.IntegerField()
    points = serializers.IntegerField()
    eliminations = serializers.IntegerField()


class PlayerPenaltySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    league_week = serializers.IntegerField(
        allow_null=True,
    )
    week_number = serializers.IntegerField(
        allow_null=True,
    )
    reason = serializers.CharField()
    points = serializers.IntegerField()
    active = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class PlayerStatsSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    position = serializers.IntegerField(
        allow_null=True,
    )
    points = serializers.IntegerField()
    games = serializers.IntegerField()
    wins = serializers.IntegerField()
    weeks = serializers.IntegerField()
    eliminations = serializers.IntegerField()
    penalties_count = serializers.IntegerField()
    penalty_points = serializers.IntegerField()
    status_icons = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )
    decks_count = serializers.IntegerField()
    most_used_deck = PlayerDeckStatsSerializer(
        allow_null=True,
    )
    decks = PlayerDeckStatsSerializer(
        many=True,
    )
    history = PlayerHistorySerializer(
        many=True,
    )
    penalties = PlayerPenaltySerializer(
        many=True,
    )


class SeasonSerializer(serializers.ModelSerializer):
    weeks_count = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = [
            "id",
            "name",
            "start_date",
            "end_date",
            "active",
            "finalized_at",
            "weeks_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "finalized_at",
            "weeks_count",
            "created_at",
        ]

    def get_weeks_count(self, obj):
        return obj.weeks.count()

    def validate(self, attrs):
        start_date = attrs.get(
            "start_date",
            getattr(
                self.instance,
                "start_date",
                None,
            ),
        )

        end_date = attrs.get(
            "end_date",
            getattr(
                self.instance,
                "end_date",
                None,
            ),
        )

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            raise serializers.ValidationError(
                {
                    "end_date": (
                        "La fecha de finalización no puede ser "
                        "anterior a la fecha de inicio."
                    )
                }
            )

        return attrs


class LeagueSettingsSerializer(serializers.ModelSerializer):
    mode_display = serializers.CharField(source="get_mode_display", read_only=True)

    class Meta:
        model = LeagueSettings
        fields = [
            "mode",
            "mode_display",
            "subscription_fee",
            "prize_pool_percent",
            "paypal_url",
            "free_league_notice",
            "updated_at",
        ]
        read_only_fields = ["mode_display", "updated_at"]

    def validate_prize_pool_percent(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 0 y 100.")
        return value


class PrizePoolSummarySerializer(serializers.Serializer):
    month = serializers.DateField()
    premium_participants = serializers.IntegerField()
    subscription_fee = serializers.DecimalField(max_digits=6, decimal_places=2)
    prize_pool_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    carry_in = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_contribution = serializers.DecimalField(max_digits=10, decimal_places=2)
    manual_adjustment = serializers.DecimalField(max_digits=10, decimal_places=2)
    distributed_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_1 = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_2 = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_3 = serializers.DecimalField(max_digits=10, decimal_places=2)


class ScoringRuleSerializer(serializers.ModelSerializer):
    code_display = serializers.CharField(
        source="get_code_display",
        read_only=True,
    )

    season_name = serializers.CharField(
        source="season.name",
        read_only=True,
    )

    class Meta:
        model = ScoringRule
        fields = [
            "id",
            "season",
            "season_name",
            "code",
            "code_display",
            "name",
            "points",
            "description",
            "active",
        ]
        read_only_fields = [
            "id",
            "season_name",
            "code_display",
        ]

    def validate(self, attrs):
        season = attrs.get(
            "season",
            getattr(
                self.instance,
                "season",
                None,
            ),
        )

        code = attrs.get(
            "code",
            getattr(
                self.instance,
                "code",
                None,
            ),
        )

        if season is None:
            raise serializers.ValidationError(
                {
                    "season": (
                        "La temporada es obligatoria."
                    )
                }
            )

        if code is None:
            raise serializers.ValidationError(
                {
                    "code": (
                        "El código de la regla "
                        "es obligatorio."
                    )
                }
            )

        queryset = ScoringRule.objects.filter(
            season=season,
            code=code,
        )

        if self.instance is not None:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                {
                    "code": (
                        "Ya existe una regla con este código "
                        "en esta temporada."
                    )
                }
            )

        return attrs