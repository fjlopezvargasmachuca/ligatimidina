from rest_framework import serializers

from .models import LeagueWeek, ScoringRule, Season


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
            "number",
            "date",
            "weekly_event_name",
            "closed",
            "created_at",
        ]


class LeagueWeekCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueWeek
        fields = [
            "season",
            "number",
            "date",
            "weekly_event",
        ]

    def validate_number(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "El número de jornada debe ser mayor que 0."
            )

        return value

    def validate(self, attrs):
        season = attrs.get("season")
        number = attrs.get("number")
        date = attrs.get("date")

        if season is None:
            raise serializers.ValidationError(
                {
                    "season": (
                        "La temporada es obligatoria."
                    )
                }
            )

        if number is None:
            raise serializers.ValidationError(
                {
                    "number": (
                        "El número de jornada es obligatorio."
                    )
                }
            )

        if date is None:
            raise serializers.ValidationError(
                {
                    "date": (
                        "La fecha de la jornada es obligatoria."
                    )
                }
            )

        existing_week = LeagueWeek.objects.filter(
            season=season,
            number=number,
        )

        if self.instance is not None:
            existing_week = existing_week.exclude(
                pk=self.instance.pk,
            )

        if existing_week.exists():
            raise serializers.ValidationError(
                {
                    "number": (
                        "Ya existe una jornada con este número "
                        "en esta temporada."
                    )
                }
            )

        previous_week = (
            LeagueWeek.objects
            .filter(
                season=season,
                number__lt=number,
            )
            .order_by("-number")
            .first()
        )

        if previous_week is not None:
            if date <= previous_week.date:
                raise serializers.ValidationError(
                    {
                        "date": (
                            "La fecha de la jornada debe ser "
                            "posterior a la fecha de la jornada "
                            "anterior."
                        )
                    }
                )

        next_week = (
            LeagueWeek.objects
            .filter(
                season=season,
                number__gt=number,
            )
            .order_by("number")
            .first()
        )

        if next_week is not None:
            if date >= next_week.date:
                raise serializers.ValidationError(
                    {
                        "date": (
                            "La fecha de la jornada debe ser "
                            "anterior a la fecha de la jornada "
                            "siguiente."
                        )
                    }
                )

        return attrs


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
            "weeks_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
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