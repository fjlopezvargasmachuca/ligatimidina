from rest_framework import serializers


class WatchSerializer(serializers.Serializer):
    """
    Serializer base para futuras entidades de seguimiento.

    La estructura definitiva se definirá cuando establezcamos
    qué información debe monitorizar la aplicación.
    """

    name = serializers.CharField(max_length=100)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    active = serializers.BooleanField(default=True)