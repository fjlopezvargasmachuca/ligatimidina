from django.test import TestCase
from rest_framework.test import APITestCase

from accounts.models import Player


class WatchesModuleTest(TestCase):

    def test_watches_app_is_available(self):
        from django.apps import apps

        config = apps.get_app_config("watches")

        self.assertEqual(
            config.name,
            "watches",
        )


class WatchesHealthAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="jugador",
            password="test1234",
            display_name="Jugador",
        )

    def test_anonymous_user_cannot_access_health(self):
        response = self.client.get(
            "/api/watches/health/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_authenticated_user_can_access_health(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.get(
            "/api/watches/health/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "ok",
        )

        self.assertEqual(
            response.data["module"],
            "watches",
        )