from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Player


class CurrentPlayerAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="test_player",
            password="test1234",
            display_name="Test Player",
        )

    def test_anonymous_user_cannot_access_current_player(self):
        response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_authenticated_user_can_access_current_player(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.player.id,
        )

        self.assertEqual(
            response.data["username"],
            "test_player",
        )

        self.assertEqual(
            response.data["display_name"],
            "Test Player",
        )

        self.assertNotIn(
            "password",
            response.data,
        )

    def test_user_can_login(self):
        response = self.client.post(
            "/api/accounts/login/",
            {
                "username": "test_player",
                "password": "test1234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["username"],
            "test_player",
        )

        self.assertEqual(
            response.data["display_name"],
            "Test Player",
        )

        self.assertNotIn(
            "password",
            response.data,
        )

        me_response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            me_response.status_code,
            200,
        )

        self.assertEqual(
            me_response.data["username"],
            "test_player",
        )

    def test_user_cannot_login_with_invalid_password(self):
        response = self.client.post(
            "/api/accounts/login/",
            {
                "username": "test_player",
                "password": "password_incorrecta",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "non_field_errors",
            response.data,
        )

        me_response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            me_response.status_code,
            403,
        )
    
    
    def test_user_can_logout(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.post(
            "/api/accounts/logout/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["detail"],
            "Sesión cerrada correctamente.",
        )

        self.client.force_authenticate(
            user=None
        )

        me_response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            me_response.status_code,
            403,
        )