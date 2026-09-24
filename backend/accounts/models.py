from django.contrib.auth.models import AbstractUser
from django.db import models


class Player(AbstractUser):
    """
    Usuario/jugador de la Liga Timidina.
    """

    display_name = models.CharField(
        max_length=100,
        verbose_name="Nombre visible"
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Avatar"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )

    def __str__(self):
        return self.display_name or self.username