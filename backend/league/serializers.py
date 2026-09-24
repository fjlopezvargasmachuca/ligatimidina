from rest_framework import serializers


class StandingSerializer(serializers.Serializer):
    position = serializers.IntegerField()
    player_id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    points = serializers.IntegerField()
    games = serializers.IntegerField()
    wins = serializers.IntegerField()
    weeks = serializers.IntegerField()
    eliminations = serializers.IntegerField()


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