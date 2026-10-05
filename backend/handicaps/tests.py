from datetime import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest.mock import patch
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Player
from decks.models import Deck
from league.models import LeagueWeek, Season
from matches.models import Match, MatchPlayer

from .models import Handicap, HandicapCategoryConfig, HandicapDefinition, HandicapGrant
from .services import HandicapService


class HandicapServiceTest(TestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(
            username="admin_handicap",
            password="test1234",
            display_name="Admin",
            is_staff=True,
        )
        self.holder = Player.objects.create_user(
            username="holder_handicap",
            password="test1234",
            display_name="Jugador Premio",
        )
        self.target = Player.objects.create_user(
            username="target_handicap",
            password="test1234",
            display_name="Jugador Objetivo",
        )
        self.deck_target = Deck.objects.create(
            owner=self.target,
            name="Mazo Target",
            commander="Comandante T",
        )
        self.season = Season.objects.create(
            name="Temporada handicap",
            start_date="2026-01-01",
            active=True,
        )
        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )
        for category, weight in (("WEAK", 60), ("MEDIUM", 30), ("STRONG", 10)):
            HandicapCategoryConfig.objects.create(
                category=category,
                selection_weight=weight,
            )
        self.definition = HandicapDefinition.objects.create(
            code="test-handicap",
            name="No te flipes de prueba",
            description="Descripción secreta de prueba.",
            category="WEAK",
            selection_weight=1,
            grace_games=3,
            penalty_points=2,
            reversal_base_percent=0,
            reversal_rank_step_percent=0,
            reversal_min_percent=0,
            reversal_max_percent=0,
        )

    def create_closed_target_match(self, hour):
        match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=timezone.make_aware(datetime(2026, 1, 5, hour, 0)),
            closed=True,
        )
        return MatchPlayer.objects.create(
            match=match,
            player=self.target,
            deck=self.deck_target,
            final_position=1,
        )

    def test_admin_grants_power_instead_of_penalty(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio.",
        )
        self.assertEqual(grant.holder_id, self.holder.id)
        self.assertFalse(grant.used)
        self.assertIsNone(grant.definition_id)
        self.assertFalse(Handicap.objects.filter(player=self.holder).exists())

    def test_holder_can_launch_grant_to_another_player(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Remontada espectacular.",
        )
        handicap = HandicapService.use_grant(
            grant=grant,
            target_player=self.target,
            actor=self.holder,
        )
        grant.refresh_from_db()

        self.assertEqual(handicap.player_id, self.target.id)
        self.assertEqual(handicap.assigned_by_player_id, self.holder.id)
        self.assertEqual(handicap.source_grant_id, grant.id)
        self.assertEqual(grant.target_player_id, self.target.id)
        self.assertTrue(grant.used)

    def test_holder_cannot_launch_to_self(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio.",
        )
        with self.assertRaises(ValidationError):
            HandicapService.use_grant(
                grant=grant,
                target_player=self.holder,
                actor=self.holder,
            )

    def test_other_player_cannot_use_grant(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio.",
        )
        with self.assertRaises(ValidationError):
            HandicapService.use_grant(
                grant=grant,
                target_player=self.target,
                actor=self.target,
            )

    def test_target_gets_grace_games_then_penalty(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio.",
        )
        handicap = HandicapService.use_grant(
            grant=grant,
            target_player=self.target,
            actor=self.holder,
        )
        for hour in (20, 21, 22):
            self.create_closed_target_match(hour)

        current = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=timezone.make_aware(datetime(2026, 1, 6, 20, 0)),
            closed=True,
        )
        result = MatchPlayer.objects.create(
            match=current,
            player=self.target,
            deck=self.deck_target,
            final_position=1,
        )

        self.assertEqual(
            HandicapService.get_penalty_points_for_match_player(result),
            2,
        )
        self.assertEqual(
            HandicapService.get_status(handicap)["games_played"],
            4,
        )


    def test_used_handicap_is_marked_and_removed_from_active_statuses(self):
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio.",
        )
        handicap = HandicapService.use_grant(
            grant=grant,
            target_player=self.target,
            actor=self.holder,
        )

        match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=timezone.make_aware(datetime(2026, 1, 6, 20, 0)),
            closed=False,
        )
        match_player = MatchPlayer.objects.create(
            match=match,
            player=self.target,
            deck=self.deck_target,
        )

        HandicapService.use_handicap(
            handicap=handicap,
            match_player=match_player,
            administrator=self.admin,
        )

        status = HandicapService.get_status(handicap)

        self.assertTrue(status["used"])
        self.assertIsNotNone(status["used_at"])
        self.assertEqual(status["used_match_id"], match.id)
        self.assertEqual(
            HandicapService.get_active_handicaps(self.target, self.season),
            [],
        )


    def test_launch_selects_from_weighted_catalog_at_launch_time(self):
        second = HandicapDefinition.objects.create(
            code="test-handicap-2",
            name="Segundo handicap",
            description="Segunda opción.",
            category="WEAK",
            selection_weight=1,
            grace_games=3,
            penalty_points=2,
        )
        grant = HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            award_reason="Premio aleatorio.",
        )
        with patch(
            "handicaps.services.random.SystemRandom.choices",
            return_value=[second],
        ) as chooser:
            handicap = HandicapService.use_grant(
                grant=grant,
                target_player=self.target,
                actor=self.holder,
            )

        self.assertEqual(handicap.definition_id, second.id)
        chooser.assert_called_once()
        weights = chooser.call_args.kwargs["weights"]
        self.assertEqual(len(weights), 2)
        self.assertEqual(weights[0], weights[1])
        self.assertGreater(weights[0], 0)



class HandicapGrantAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Player.objects.create_user(
            username="api_admin",
            password="test1234",
            display_name="Admin API",
            is_staff=True,
        )
        self.holder = Player.objects.create_user(
            username="api_holder",
            password="test1234",
            display_name="Holder API",
        )
        self.target = Player.objects.create_user(
            username="api_target",
            password="test1234",
            display_name="Target API",
        )
        self.other = Player.objects.create_user(
            username="api_other",
            password="test1234",
            display_name="Other API",
        )
        self.season = Season.objects.create(
            name="API Season",
            start_date="2026-02-01",
            active=True,
        )
        self.definition = HandicapDefinition.objects.create(
            code="api-handicap",
            name="Handicap API",
            description="Descripción que no debe ver el titular.",
            category="WEAK",
            grace_games=3,
            penalty_points=2,
            reversal_base_percent=0,
            reversal_rank_step_percent=0,
            reversal_min_percent=0,
            reversal_max_percent=0,
        )
        HandicapCategoryConfig.objects.create(
            category="WEAK",
            selection_weight=100,
        )

    def create_grant(self):
        return HandicapService.grant_handicap(
            holder=self.holder,
            season=self.season,
            administrator=self.admin,
            definition=self.definition,
            award_reason="Premio API.",
        )

    def test_admin_creates_grant_and_sees_secret_definition(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/handicaps/create/",
            {
                "player": self.holder.id,
                "season": self.season.id,
                "award_reason": "Premio por una jugada inusual.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["definition_name"], "🎲 Aleatoria al lanzar")
        self.assertEqual(HandicapGrant.objects.count(), 1)
        self.assertEqual(Handicap.objects.count(), 0)

    def test_holder_endpoint_does_not_reveal_definition(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)

        response = self.client.get("/api/handicaps/grants/mine/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        payload = response.data[0]
        self.assertEqual(payload["id"], grant.id)
        self.assertTrue(payload["available"])
        self.assertNotIn("definition", payload)
        self.assertNotIn("definition_name", payload)
        self.assertNotIn("description", payload)
        self.assertNotIn("category", payload)
        self.assertNotIn("category_display", payload)
        self.assertNotIn("penalty_points", payload)
        self.assertNotIn("grace_games", payload)

    def test_other_player_cannot_read_holder_grant(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.other)

        response = self.client.get(f"/api/handicaps/grants/{grant.id}/")

        # No detail endpoint exists for grants: the list is holder-scoped.
        self.assertIn(response.status_code, (404, 405))
        response = self.client.get("/api/handicaps/grants/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_holder_can_use_grant_and_receives_reveal_in_response(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)

        response = self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.target.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("grant", response.data)
        self.assertIn("handicap", response.data)
        self.assertEqual(response.data["handicap"]["name"], self.definition.name)
        self.assertEqual(response.data["handicap"]["description"], self.definition.description)
        self.assertEqual(len(response.data["roulette_options"]), 1)
        self.assertEqual(response.data["roulette_options"][0]["id"], self.definition.id)
        self.assertNotIn("definition_name", response.data["grant"])
        self.assertNotIn("description", response.data["grant"])

        handicap = Handicap.objects.get()
        self.assertEqual(handicap.player_id, self.target.id)
        self.assertEqual(handicap.assigned_by_player_id, self.holder.id)

        self.client.force_authenticate(self.holder)
        mine = self.client.get("/api/handicaps/grants/mine/")
        self.assertEqual(mine.status_code, 200)
        self.assertNotIn("definition_name", mine.data[0])
        self.assertNotIn("description", mine.data[0])

    def test_holder_cannot_use_grant_twice(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)

        first = self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.target.id},
            format="json",
        )
        second = self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.other.id},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(Handicap.objects.count(), 1)

    def test_holder_cannot_read_other_players_handicap(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)
        self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.target.id},
            format="json",
        )
        handicap = Handicap.objects.get()

        response = self.client.get(f"/api/handicaps/{handicap.id}/")

        self.assertEqual(response.status_code, 404)

    def test_target_can_read_own_handicap_and_see_type(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)
        self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.target.id},
            format="json",
        )
        handicap = Handicap.objects.get()

        self.client.force_authenticate(self.target)
        response = self.client.get(f"/api/handicaps/{handicap.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["definition_name"], self.definition.name)
        self.assertEqual(response.data["description"], self.definition.description)

    def test_target_cannot_use_someone_elses_grant(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.target)

        response = self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.other.id},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Handicap.objects.count(), 0)

    def test_player_cannot_query_another_players_handicaps(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)
        self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.target.id},
            format="json",
        )

        self.client.force_authenticate(self.other)
        response = self.client.get(
            f"/api/handicaps/players/{self.target.id}/"
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_see_everything(self):
        grant = self.create_grant()
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/handicaps/grants/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["definition_name"], "🎲 Aleatoria al lanzar")
        self.assertEqual(response.data[0]["holder"], self.holder.id)

    def test_direct_limit_is_two_per_target_and_season(self):
        self.client.force_authenticate(self.holder)
        for _ in range(2):
            grant = self.create_grant()
            response = self.client.post(
                f"/api/handicaps/grants/{grant.id}/use/",
                {"target_player": self.target.id}, format="json",
            )
            self.assertEqual(response.status_code, 201)
        third = self.create_grant()
        response = self.client.post(
            f"/api/handicaps/grants/{third.id}/use/",
            {"target_player": self.target.id}, format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Límite antiacoso", str(response.data))

    @patch("handicaps.services.random.SystemRandom.uniform", return_value=0)
    def test_reverse_returns_penalty_to_holder_and_does_not_count_as_direct(self, _mock_uniform):
        self.definition.reversal_base_percent = 100
        self.definition.reversal_min_percent = 100
        self.definition.reversal_max_percent = 100
        self.definition.save(update_fields=["reversal_base_percent", "reversal_min_percent", "reversal_max_percent"])
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)
        response = self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.target.id}, format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["handicap"]["reversed"])
        grant.refresh_from_db()
        self.assertTrue(grant.reversed)
        self.assertEqual(grant.handicap.player_id, self.holder.id)
        direct_count = HandicapGrant.objects.filter(
            holder=self.holder, target_player=self.target, reversed=False, used_at__isnull=False
        ).count()
        self.assertEqual(direct_count, 0)
    def test_inactive_player_cannot_be_target(self):
        self.target.is_active = False
        self.target.save(update_fields=["is_active"])
        grant = self.create_grant()
        self.client.force_authenticate(self.holder)
        response = self.client.post(
            f"/api/handicaps/grants/{grant.id}/use/",
            {"target_player": self.target.id}, format="json",
        )
        self.assertIn(response.status_code, (400, 404))
        self.assertFalse(Handicap.objects.exists())




class NoTeFlipesMilestoneAPITest(TestCase):
    def test_authenticated_player_can_read_active_milestones(self):
        from .models import NoTeFlipesMilestone

        player = Player.objects.create_user(
            username="milestone-player",
            password="test1234",
            display_name="Milestone Player",
        )
        NoTeFlipesMilestone.objects.create(
            name="Golpe de prueba",
            description="Hacer una jugada extraordinaria.",
            example="Ejemplo de prueba.",
            active=True,
            sort_order=1,
        )
        NoTeFlipesMilestone.objects.create(
            name="Oculto",
            description="No debe mostrarse.",
            active=False,
            sort_order=2,
        )
        client = APIClient()
        client.force_authenticate(player)
        response = client.get("/api/handicaps/milestones/")
        self.assertEqual(response.status_code, 200)
        names = [row["name"] for row in response.data]
        self.assertIn("Golpe de prueba", names)
        self.assertNotIn("Oculto", names)
