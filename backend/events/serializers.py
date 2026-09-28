from rest_framework import serializers

from .models import WeeklyEvent


class WeeklyEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = WeeklyEvent
        fields = [
            "id",
            "name",
            "description",
            "rules",
            "extra_points",
            "active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_extra_points(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Los puntos extra no pueden ser negativos."
            )

        return value