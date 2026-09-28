from datetime import date

from django.test import TestCase
from rest_framework.test import APITestCase

from accounts.models import Player
from league.models import LeagueWeek, Season

from .models import Penalty
from .services import PenaltyService


class PenaltyServiceTest(TestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(
            username="admin",
            password="test1234",
            display_name="Administrador",
            is_staff=True,
        )

        self.player = Player.objects.create_user(
            username="player",
            password="test1234",
            display_name="Jugador",
        )

        self.season = Season.objects.create(
            name="Temporada Penalizaciones",
            start_date=date(2026, 1, 1),
            active=True,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date=date(2026, 1, 5),
        )

    def test_penalty_points_are_calculated(self):
        Penalty.objects.create(
            player=self.player,
            season=self.season,
            league_week=self.week,
            administrator=self.admin,
            reason="Llegar tarde",
            points=2,
        )

        Penalty.objects.create(
            player=self.player,
            season=self.season,
            league_week=self.week,
            administrator=self.admin,
            reason="Otra penalización",
            points=3,
        )

        self.assertEqual(
            PenaltyService.get_player_penalty_points(
                self.player,
                self.season,
            ),
            5,
        )

    def test_inactive_penalties_are_not_counted(self):
        Penalty.objects.create(
            player=self.player,
            season=self.season,
            administrator=self.admin,
            reason="Penalización anulada",
            points=5,
            active=False,
        )

        self.assertEqual(
            PenaltyService.get_player_penalty_points(
                self.player,
                self.season,
            ),
            0,
        )

    def test_penalty_count_only_includes_active_penalties(self):
        Penalty.objects.create(
            player=self.player,
            season=self.season,
            administrator=self.admin,
            reason="Activa",
            points=2,
        )

        Penalty.objects.create(
            player=self.player,
            season=self.season,
            administrator=self.admin,
            reason="Anulada",
            points=3,
            active=False,
        )

        self.assertEqual(
            PenaltyService.get_player_penalty_count(
                self.player,
                self.season,
            ),
            1,
        )


class PenaltyAPITest(APITestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(
            username="admin_api",
            password="test1234",
            display_name="Admin API",
            is_staff=True,
        )

        self.player = Player.objects.create_user(
            username="player_api",
            password="test1234",
            display_name="Player API",
        )

        self.season = Season.objects.create(
            name="Temporada API",
            start_date=date(2026, 1, 1),
            active=True,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date=date(2026, 1, 5),
        )

    def penalty_payload(self):
        return {
            "player": self.player.id,
            "season": self.season.id,
            "league_week": self.week.id,
            "reason": "Llegar tarde",
            "points": 2,
        }

    def test_anonymous_user_cannot_list_penalties(self):
        response = self.client.get(
            "/api/penalties/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_authenticated_user_can_list_penalties(self):
        Penalty.objects.create(
            player=self.player,
            season=self.season,
            league_week=self.week,
            administrator=self.admin,
            reason="Llegar tarde",
            points=2,
        )

        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.get(
            "/api/penalties/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_non_admin_cannot_create_penalty(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.post(
            "/api/penalties/create/",
            self.penalty_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_admin_can_create_penalty(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/penalties/create/",
            self.penalty_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["player"],
            self.player.id,
        )

        self.assertEqual(
            response.data["points"],
            2,
        )

        self.assertEqual(
            response.data["administrator"],
            self.admin.id,
        )

        self.assertEqual(
            Penalty.objects.count(),
            1,
        )

    def test_admin_can_update_penalty(self):
        penalty = Penalty.objects.create(
            player=self.player,
            season=self.season,
            league_week=self.week,
            administrator=self.admin,
            reason="Motivo inicial",
            points=2,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/penalties/{penalty.id}/",
            {
                "reason": "Motivo actualizado",
                "points": 4,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        penalty.refresh_from_db()

        self.assertEqual(
            penalty.reason,
            "Motivo actualizado",
        )

        self.assertEqual(
            penalty.points,
            4,
        )

    def test_non_admin_cannot_update_penalty(self):
        penalty = Penalty.objects.create(
            player=self.player,
            season=self.season,
            administrator=self.admin,
            reason="Motivo",
            points=2,
        )

        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.patch(
            f"/api/penalties/{penalty.id}/",
            {
                "points": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_player_can_view_own_active_penalties(self):
        Penalty.objects.create(
            player=self.player,
            season=self.season,
            league_week=self.week,
            administrator=self.admin,
            reason="Activa",
            points=2,
        )

        Penalty.objects.create(
            player=self.player,
            season=self.season,
            administrator=self.admin,
            reason="Anulada",
            points=5,
            active=False,
        )

        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.get(
            f"/api/penalties/players/{self.player.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["reason"],
            "Activa",
        )

    def test_penalty_rejects_mismatched_week_and_season(self):
        other_season = Season.objects.create(
            name="Otra temporada",
            start_date=date(2025, 1, 1),
            active=False,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/penalties/create/",
            {
                "player": self.player.id,
                "season": other_season.id,
                "league_week": self.week.id,
                "reason": "Temporada incorrecta",
                "points": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "league_week",
            response.data,
        )

    def test_penalty_rejects_zero_points(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/penalties/create/",
            {
                "player": self.player.id,
                "season": self.season.id,
                "league_week": self.week.id,
                "reason": "Sin puntos",
                "points": 0,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "points",
            response.data,
        )