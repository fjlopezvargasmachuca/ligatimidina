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