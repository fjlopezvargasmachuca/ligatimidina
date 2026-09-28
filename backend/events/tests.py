from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from league.models import LeagueWeek, Season

from .models import WeeklyEvent


User = get_user_model()


class WeeklyEventAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.player = User.objects.create_user(
            username="player",
            password="testpass123",
            display_name="Jugador",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            display_name="Administrador",
            is_staff=True,
        )

        self.event = WeeklyEvent.objects.create(
            name="Archenemy",
            description="Todos contra el Archenemy.",
            rules="Reglas del evento.",
            extra_points=3,
            active=True,
        )

    def test_anonymous_user_cannot_list_events(self):
        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_can_list_events(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Archenemy")

    def test_non_admin_cannot_create_event(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.post(
            "/api/events/create/",
            {
                "name": "Planechase",
                "description": "Evento Planechase.",
                "rules": "Reglas.",
                "extra_points": 2,
                "active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            WeeklyEvent.objects.filter(name="Planechase").exists()
        )

    def test_admin_can_create_event(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/events/create/",
            {
                "name": "Planechase",
                "description": "Evento Planechase.",
                "rules": "Reglas.",
                "extra_points": 2,
                "active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            WeeklyEvent.objects.filter(name="Planechase").exists()
        )

    def test_non_admin_cannot_update_event(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.patch(
            f"/api/events/{self.event.id}/",
            {
                "name": "Evento modificado",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Archenemy")

    def test_admin_cannot_update_event_after_creation(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/events/{self.event.id}/",
            {
                "name": "Archenemy actualizado",
                "extra_points": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)

        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Archenemy")
        self.assertEqual(self.event.extra_points, 3)

    def create_closed_week(self):
        season = Season.objects.create(
            name="Temporada de pruebas",
            start_date=date.today(),
            active=True,
        )

        return LeagueWeek.objects.create(
            season=season,
            number=1,
            date=date.today(),
            weekly_event=self.event,
            closed=True,
        )

    def test_admin_cannot_change_content_of_event_used_by_closed_week(self):
        self.create_closed_week()

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/events/{self.event.id}/",
            {
                "name": "Evento cambiado",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)

        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Archenemy")

    def test_admin_cannot_change_rules_of_event_used_by_closed_week(self):
        self.create_closed_week()

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/events/{self.event.id}/",
            {
                "rules": "Reglas nuevas.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)

        self.event.refresh_from_db()
        self.assertEqual(self.event.rules, "Reglas del evento.")

    def test_admin_cannot_change_extra_points_of_event_used_by_closed_week(self):
        self.create_closed_week()

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/events/{self.event.id}/",
            {
                "extra_points": 10,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)

        self.event.refresh_from_db()
        self.assertEqual(self.event.extra_points, 3)

    def test_admin_cannot_deactivate_event_used_by_closed_week(self):
        self.create_closed_week()

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/events/{self.event.id}/",
            {
                "active": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)

        self.event.refresh_from_db()
        self.assertTrue(self.event.active)

    def test_negative_extra_points_are_rejected(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/events/create/",
            {
                "name": "Evento inválido",
                "description": "Descripción.",
                "rules": "Reglas.",
                "extra_points": -1,
                "active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            WeeklyEvent.objects.filter(name="Evento inválido").exists()
        )