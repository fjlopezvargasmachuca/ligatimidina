from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Player
from handicaps.models import Handicap, HandicapCategoryConfig, HandicapDefinition, HandicapGrant
from handicaps.services import HandicapService
from league.models import LeagueWeek, Season
from league.services import RankingService
from penalties.models import Penalty


class StandingStatusTest(TestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(
            username="status_admin",
            password="test1234",
            display_name="Admin",
            is_staff=True,
        )
        self.holder = Player.objects.create_user(
            username="status_holder",
            password="test1234",
            display_name="Titular",
        )
        self.target = Player.objects.create_user(
            username="status_target",
            password="test1234",
            display_name="Objetivo",
        )
        self.other = Player.objects.create_user(
            username="status_other",
            password="test1234",
            display_name="Otro",
        )
        self.season = Season.objects.create(
            name="Temporada estados",
            start_date="2026-01-01",
            active=True,
        )
        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )
        HandicapCategoryConfig.objects.create(
            category="WEAK",
            selection_weight=100,
        )
        self.definition = HandicapDefinition.objects.create(
            code="status-handicap",
            name="Mano izquierda",
            description="Juega todas las tierras con la mano izquierda.",
            category="WEAK",
            grace_games=3,
            penalty_points=2,
            reversal_base_percent=0, reversal_rank_step_percent=0,
            reversal_min_percent=0, reversal_max_percent=0,
        )

    def _standing(self, standings, player_id):
        return next(item for item in standings if item["player_id"] == player_id)

    def test_available_grant_adds_player_and_public_icon(self):
        HandicapGrant.objects.create(
            holder=self.holder,
            definition=self.definition,
            season=self.season,
            awarded_by=self.admin,
            award_reason="Premio de prueba",
        )

        standings = RankingService.get_standings(self.season)
        from league.standing_status import StandingStatusService

        result = StandingStatusService.enrich(
            standings,
            season=self.season,
            viewer=None,
        )
        holder = self._standing(result, self.holder.id)

        self.assertEqual(holder["games"], 0)
        self.assertEqual(holder["status_icons"][0]["type"], "NO_TE_FLIPES_AVAILABLE")
        self.assertIn("disponible", holder["status_icons"][0]["description"])

    def test_handicap_description_is_hidden_from_other_players(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio secreto",
        )
        HandicapService.use_grant(
            grant=grant,
            target_player=self.target,
            actor=self.holder,
        )

        from league.standing_status import StandingStatusService

        result = StandingStatusService.enrich(
            RankingService.get_standings(self.season),
            season=self.season,
            viewer=self.other,
        )
        target = self._standing(result, self.target.id)
        icon = next(
            item for item in target["status_icons"]
            if item["type"] == "HANDICAP_ACTIVE"
        )

        self.assertEqual(icon["label"], "Penalización de No te flipes")
        self.assertNotIn(self.definition.description, icon["description"])

    def test_handicap_description_is_visible_to_recipient(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio secreto",
        )
        HandicapService.use_grant(
            grant=grant,
            target_player=self.target,
            actor=self.holder,
        )

        from league.standing_status import StandingStatusService

        result = StandingStatusService.enrich(
            RankingService.get_standings(self.season),
            season=self.season,
            viewer=self.target,
        )
        target = self._standing(result, self.target.id)
        icon = next(
            item for item in target["status_icons"]
            if item["type"] == "HANDICAP_ACTIVE"
        )

        self.assertEqual(icon["label"], self.definition.name)
        self.assertIn(self.definition.description, icon["description"])

    def test_normal_penalty_adds_public_icon(self):
        Penalty.objects.create(
            player=self.other,
            season=self.season,
            league_week=self.week,
            reason="No presentó la lista a tiempo.",
            points=2,
            administrator=self.admin,
            active=True,
        )

        from league.standing_status import StandingStatusService

        result = StandingStatusService.enrich(
            RankingService.get_standings(self.season),
            season=self.season,
            viewer=None,
        )
        other = self._standing(result, self.other.id)
        icon = next(
            item for item in other["status_icons"]
            if item["type"] == "LEAGUE_PENALTY"
        )

        self.assertEqual(icon["description"], "No presentó la lista a tiempo.")
        self.assertEqual(icon["points"], 2)


class StandingStatusAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Player.objects.create_user(
            username="api_status_admin",
            password="test1234",
            display_name="Admin",
            is_staff=True,
        )
        self.holder = Player.objects.create_user(
            username="api_status_holder",
            password="test1234",
            display_name="Titular API",
        )
        self.target = Player.objects.create_user(
            username="api_status_target",
            password="test1234",
            display_name="Objetivo API",
        )
        self.season = Season.objects.create(
            name="Temporada API estados",
            start_date="2026-01-01",
            active=True,
        )
        HandicapCategoryConfig.objects.create(
            category="WEAK",
            selection_weight=100,
        )
        self.definition = HandicapDefinition.objects.create(
            code="api-status-handicap",
            name="Penalización privada",
            description="Descripción privada que no debe filtrar el ranking.",
            category="WEAK",
            reversal_base_percent=0, reversal_rank_step_percent=0,
            reversal_min_percent=0, reversal_max_percent=0,
        )

    def test_public_standings_contains_status_icons_without_secret(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio API",
        )
        HandicapService.use_grant(
            grant=grant,
            target_player=self.target,
            actor=self.holder,
        )

        self.client.force_authenticate(self.holder)
        response = self.client.get("/api/league/standings/")

        self.assertEqual(response.status_code, 200)
        target = next(
            item for item in response.data["standings"]
            if item["player_id"] == self.target.id
        )
        icon = next(
            item for item in target["status_icons"]
            if item["type"] == "HANDICAP_ACTIVE"
        )
        self.assertEqual(icon["label"], "Penalización de No te flipes")
        self.assertNotIn(self.definition.description, icon["description"])
