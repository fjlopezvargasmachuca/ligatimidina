from datetime import datetime

from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import Player
from decks.models import Deck
from league.models import LeagueWeek, ScoringRule, Season
from .models import Elimination, Match, MatchPlayer
from .services import MatchService
from handicaps.models import Handicap, HandicapCategoryConfig, HandicapDefinition
from handicaps.services import HandicapService
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone


def aware_datetime(year, month, day, hour, minute=0):
    """Construye datetimes conscientes de zona horaria para tests con USE_TZ=True."""
    return timezone.make_aware(datetime(year, month, day, hour, minute))



class MatchServiceTest(TestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="jugador1",
            password="test1234",
            display_name="Jugador 1",
        )

        self.deck = Deck.objects.create(
            owner=self.player,
            name="Mazo de prueba",
            commander="Comandante de prueba",
        )

        self.season = Season.objects.create(
            name="Temporada de prueba",
            start_date="2026-01-01",
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.player,
            played_at=aware_datetime(2026, 1, 5, 20),
        )

        self.match_player = MatchPlayer.objects.create(
            match=self.match,
            player=self.player,
            deck=self.deck,
            final_position=1,
        )

        ScoringRule.objects.create(
            season=self.season,
            code="WIN",
            name="Victoria",
            points=5,
        )

    def test_close_match_calculates_points(self):
        MatchService.close_match(self.match)

        self.match_player.refresh_from_db()
        self.match.refresh_from_db()

        self.assertEqual(
            self.match_player.points,
            5,
        )

        self.assertTrue(
            self.match.closed
        )

    def test_cannot_close_match_twice(self):
        MatchService.close_match(self.match)

        with self.assertRaises(Exception):
            MatchService.close_match(self.match)


class MatchAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.player = Player.objects.create_user(
            username="jugador1",
            password="test1234",
            display_name="Jugador 1",
            is_staff=True,
        )

        self.other_player = Player.objects.create_user(
            username="jugador2",
            password="test1234",
            display_name="Jugador 2",
            is_staff=True,
        )

        self.deck = Deck.objects.create(
            owner=self.player,
            name="Mazo de prueba",
            commander="Comandante de prueba",
        )

        self.other_deck = Deck.objects.create(
            owner=self.other_player,
            name="Mazo rival",
            commander="Comandante rival",
        )

        self.season = Season.objects.create(
            name="Temporada de prueba",
            start_date="2026-01-01",
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.player,
            played_at=aware_datetime(2026, 1, 5, 20),
        )

    def test_anonymous_cannot_list_matches(self):
        response = self.client.get("/api/matches/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_authenticated_can_list_matches(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.get("/api/matches/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_authenticated_can_retrieve_match(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.get(
            f"/api/matches/{self.match.id}/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.match.id,
        )

    def test_authenticated_can_create_match(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            "/api/matches/create/",
            {
                "league_week": self.week.id,
                "played_at": "2026-01-06T20:00:00Z",
                "notes": "Partida nueva",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        match = Match.objects.get(
            id=response.data["id"],
        )

        self.assertEqual(
            match.administrator_id,
            self.player.id,
        )

    def test_cannot_create_match_in_closed_week(self):
        self.week.closed = True
        self.week.save(
            update_fields=["closed"],
        )

        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            "/api/matches/create/",
            {
                "league_week": self.week.id,
                "played_at": "2026-01-06T20:00:00Z",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_can_add_player_to_match(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/players/create/",
            {
                "player": self.player.id,
                "deck": self.deck.id,
                "final_position": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            MatchPlayer.objects.filter(
                match=self.match,
                player=self.player,
            ).exists()
        )

    def test_cannot_add_deck_owned_by_another_player(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/players/create/",
            {
                "player": self.player.id,
                "deck": self.other_deck.id,
                "final_position": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_cannot_add_same_player_twice(self):
        MatchPlayer.objects.create(
            match=self.match,
            player=self.player,
            deck=self.deck,
            final_position=1,
        )

        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/players/create/",
            {
                "player": self.player.id,
                "deck": self.deck.id,
                "final_position": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_player_snapshot_is_created(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/players/create/",
            {
                "player": self.player.id,
                "deck": self.deck.id,
                "final_position": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        match_player = MatchPlayer.objects.get(
            match=self.match,
            player=self.player,
        )

        self.assertEqual(
            match_player.deck_name,
            "Mazo de prueba",
        )

        self.assertEqual(
            match_player.commander_name,
            "Comandante de prueba",
        )
    def test_cannot_close_match_as_non_administrator(self):
        self.client.force_authenticate(
            user=self.other_player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/close/",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.match.refresh_from_db()

        self.assertFalse(
            self.match.closed,
        )


    def test_administrator_can_close_match(self):
        MatchPlayer.objects.create(
            match=self.match,
            player=self.player,
            deck=self.deck,
            final_position=1,
        )

        ScoringRule.objects.create(
            season=self.season,
            code="WIN",
            name="Victoria",
            points=5,
        )

        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/close/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.match.refresh_from_db()

        self.assertTrue(
            self.match.closed,
        )

        match_player = MatchPlayer.objects.get(
            match=self.match,
            player=self.player,
        )

        self.assertEqual(
            match_player.points,
            5,
        )

class EliminationAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.player = Player.objects.create_user(
            username="jugador1",
            password="test1234",
            display_name="Jugador 1",
        )

        self.other_player = Player.objects.create_user(
            username="jugador2",
            password="test1234",
            display_name="Jugador 2",
        )

        self.deck = Deck.objects.create(
            owner=self.player,
            name="Mazo 1",
            commander="Comandante 1",
        )

        self.other_deck = Deck.objects.create(
            owner=self.other_player,
            name="Mazo 2",
            commander="Comandante 2",
        )

        self.season = Season.objects.create(
            name="Temporada de prueba",
            start_date="2026-01-01",
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.player,
            played_at=aware_datetime(2026, 1, 5, 20),
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.player,
            deck=self.deck,
            final_position=1,
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.other_player,
            deck=self.other_deck,
            final_position=2,
        )

    def test_authenticated_can_create_elimination(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/eliminations/create/",
            {
                "killer": self.player.id,
                "victim": self.other_player.id,
                "turn": 7,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["killer"],
            self.player.id,
        )

        self.assertEqual(
            response.data["victim"],
            self.other_player.id,
        )

        self.assertTrue(
            Elimination.objects.filter(
                match=self.match,
                killer=self.player,
                victim=self.other_player,
            ).exists()
        )

    def test_cannot_self_eliminate(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/eliminations/create/",
            {
                "killer": self.player.id,
                "victim": self.player.id,
                "turn": 7,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_cannot_create_elimination_in_closed_match(self):
        self.match.closed = True
        self.match.save(
            update_fields=["closed"],
        )

        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/eliminations/create/",
            {
                "killer": self.player.id,
                "victim": self.other_player.id,
                "turn": 7,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_match_detail_includes_eliminations(self):
        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=self.other_player,
            turn=7,
        )

        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.get(
            f"/api/matches/{self.match.id}/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data["eliminations"]),
            1,
        )

        self.assertEqual(
            response.data["eliminations"][0]["killer"],
            self.player.id,
        )

        self.assertEqual(
            response.data["eliminations"][0]["victim"],
            self.other_player.id,
        )
    
    def test_non_administrator_cannot_create_elimination(self):
        self.client.force_authenticate(
            user=self.other_player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/eliminations/create/",
            {
                "killer": self.player.id,
                "victim": self.other_player.id,
                "turn": 7,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            Elimination.objects.filter(
                match=self.match,
            ).exists()
        )

    def test_cannot_create_elimination_for_non_player(self):
        outsider = Player.objects.create_user(
            username="jugador3",
            password="test1234",
            display_name="Jugador 3",
        )

        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/eliminations/create/",
            {
                "killer": self.player.id,
                "victim": outsider.id,
                "turn": 7,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_elimination_points_are_calculated_when_match_closes(self):
        ScoringRule.objects.create(
            season=self.season,
            code="ELIMINATION",
            name="Eliminación",
            points=2,
        )

        ScoringRule.objects.create(
            season=self.season,
            code="FIRST_ELIMINATION",
            name="Primera eliminación",
            points=3,
        )

        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=self.other_player,
            turn=7,
            first_elimination=True,
        )

        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.post(
            f"/api/matches/{self.match.id}/close/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        match_player = MatchPlayer.objects.get(
            match=self.match,
            player=self.player,
        )

        self.assertEqual(
            match_player.points,
            5,
        )


class MatchClosingValidationTest(TestCase):
    def setUp(self):
        from datetime import date

        from accounts.models import Player
        from decks.models import Deck
        from league.models import LeagueWeek, Season

        self.admin = Player.objects.create_user(
            username="admin_cierre",
            password="test1234",
            display_name="Admin Cierre",
            is_staff=True,
        )

        self.player_2 = Player.objects.create_user(
            username="jugador_cierre_2",
            password="test1234",
            display_name="Jugador 2",
        )

        self.player_3 = Player.objects.create_user(
            username="jugador_cierre_3",
            password="test1234",
            display_name="Jugador 3",
        )

        self.season = Season.objects.create(
            name="Temporada cierre",
            start_date=date(2026, 1, 1),
            active=True,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date=date(2026, 1, 5),
            closed=False,
        )

        self.deck_1 = Deck.objects.create(
            owner=self.admin,
            name="Mazo Admin",
            commander="Comandante Admin",
        )

        self.deck_2 = Deck.objects.create(
            owner=self.player_2,
            name="Mazo Jugador 2",
            commander="Comandante 2",
        )

        self.deck_3 = Deck.objects.create(
            owner=self.player_3,
            name="Mazo Jugador 3",
            commander="Comandante 3",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=aware_datetime(2026, 1, 5, 20),
        )

    def test_cannot_close_match_without_players(self):
        with self.assertRaises(DjangoValidationError):
            MatchService.close_match(self.match)

    def test_cannot_close_match_without_final_positions(self):
        MatchPlayer.objects.create(
            match=self.match,
            player=self.admin,
            deck=self.deck_1,
        )

        with self.assertRaises(DjangoValidationError):
            MatchService.close_match(self.match)

    def test_can_close_match_with_final_positions(self):
        MatchPlayer.objects.create(
            match=self.match,
            player=self.admin,
            deck=self.deck_1,
            final_position=1,
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.player_2,
            deck=self.deck_2,
            final_position=2,
        )

        MatchService.close_match(self.match)

        self.match.refresh_from_db()

        self.assertTrue(self.match.closed)

    def test_cannot_close_match_if_week_is_closed(self):
        MatchPlayer.objects.create(
            match=self.match,
            player=self.admin,
            deck=self.deck_1,
            final_position=1,
        )

        self.week.closed = True
        self.week.save(update_fields=["closed"])

        with self.assertRaises(DjangoValidationError):
            MatchService.close_match(self.match)


    def test_only_one_first_elimination_is_allowed(self):
        MatchPlayer.objects.create(
            match=self.match,
            player=self.admin,
            deck=self.deck_1,
            final_position=1,
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.player_2,
            deck=self.deck_2,
            final_position=2,
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.player_3,
            deck=self.deck_3,
            final_position=3,
        )

        Elimination.objects.create(
            match=self.match,
            killer=self.admin,
            victim=self.player_2,
            first_elimination=True,
        )

        Elimination.objects.create(
            match=self.match,
            killer=self.player_3,
            victim=self.admin,
            first_elimination=True,
        )

        with self.assertRaises(DjangoValidationError):
            MatchService.close_match(self.match)

    def test_multiple_players_can_have_same_final_position(self):
        MatchPlayer.objects.create(
            match=self.match,
            player=self.admin,
            deck=self.deck_1,
            final_position=1,
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.player_2,
            deck=self.deck_2,
            final_position=1,
        )

        MatchService.close_match(self.match)

        self.match.refresh_from_db()

        self.assertTrue(self.match.closed)

class MatchPlayerUpdateAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = Player.objects.create_user(
            username="admin_resultados",
            password="test1234",
            display_name="Admin Resultados",
            is_staff=True,
        )

        self.other_player = Player.objects.create_user(
            username="jugador_resultados",
            password="test1234",
            display_name="Jugador Resultados",
            is_staff=True,
        )

        self.deck = Deck.objects.create(
            owner=self.admin,
            name="Mazo Admin Resultados",
            commander="Comandante Admin Resultados",
        )

        self.season = Season.objects.create(
            name="Temporada resultados",
            start_date="2026-01-01",
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=aware_datetime(2026, 1, 5, 20),
        )

        self.match_player = MatchPlayer.objects.create(
            match=self.match,
            player=self.admin,
            deck=self.deck,
            final_position=None,
        )

    def test_administrator_can_update_final_position(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/matches/{self.match.id}/players/"
            f"{self.match_player.id}/",
            {
                "final_position": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.match_player.refresh_from_db()

        self.assertEqual(
            self.match_player.final_position,
            1,
        )

        self.assertEqual(
            response.data["final_position"],
            1,
        )

    def test_non_administrator_cannot_update_match_player(self):
        self.client.force_authenticate(user=self.other_player)

        response = self.client.patch(
            f"/api/matches/{self.match.id}/players/"
            f"{self.match_player.id}/",
            {
                "final_position": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.match_player.refresh_from_db()

        self.assertIsNone(self.match_player.final_position)

    def test_cannot_update_match_player_in_closed_match(self):
        self.match.closed = True
        self.match.save(update_fields=["closed"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/matches/{self.match.id}/players/"
            f"{self.match_player.id}/",
            {
                "final_position": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.match_player.refresh_from_db()

        self.assertIsNone(self.match_player.final_position)

    def test_cannot_update_match_player_in_closed_week(self):
        self.week.closed = True
        self.week.save(update_fields=["closed"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/matches/{self.match.id}/players/"
            f"{self.match_player.id}/",
            {
                "final_position": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.match_player.refresh_from_db()

        self.assertIsNone(self.match_player.final_position)

    def test_cannot_update_player_result_from_another_match(self):
        other_match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=aware_datetime(2026, 1, 6, 20),
        )

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/matches/{other_match.id}/players/"
            f"{self.match_player.id}/",
            {
                "final_position": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        self.match_player.refresh_from_db()

        self.assertIsNone(self.match_player.final_position)

class EliminationDeleteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = Player.objects.create_user(
            username="admin_eliminaciones",
            password="test1234",
            display_name="Admin Eliminaciones",
            is_staff=True,
        )

        self.other_player = Player.objects.create_user(
            username="jugador_eliminaciones",
            password="test1234",
            display_name="Jugador Eliminaciones",
        )

        self.victim = Player.objects.create_user(
            username="victima_eliminaciones",
            password="test1234",
            display_name="Víctima Eliminaciones",
        )

        self.admin_deck = Deck.objects.create(
            owner=self.admin,
            name="Mazo Admin",
            commander="Comandante Admin",
        )

        self.other_deck = Deck.objects.create(
            owner=self.other_player,
            name="Mazo Otro",
            commander="Comandante Otro",
        )

        self.victim_deck = Deck.objects.create(
            owner=self.victim,
            name="Mazo Víctima",
            commander="Comandante Víctima",
        )

        self.season = Season.objects.create(
            name="Temporada eliminaciones",
            start_date="2026-01-01",
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=aware_datetime(2026, 1, 5, 20),
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.admin,
            deck=self.admin_deck,
            final_position=1,
        )
        MatchPlayer.objects.create(
            match=self.match,
            player=self.other_player,
            deck=self.other_deck,
            final_position=2,
        )
        MatchPlayer.objects.create(
            match=self.match,
            player=self.victim,
            deck=self.victim_deck,
            final_position=3,
        )

        self.elimination = Elimination.objects.create(
            match=self.match,
            killer=self.admin,
            victim=self.victim,
            turn=7,
            first_elimination=True,
        )

    def test_administrator_can_delete_elimination(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/matches/{self.match.id}/eliminations/"
            f"{self.elimination.id}/",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Elimination.objects.filter(id=self.elimination.id).exists()
        )

    def test_non_administrator_cannot_delete_elimination(self):
        self.client.force_authenticate(user=self.other_player)

        response = self.client.delete(
            f"/api/matches/{self.match.id}/eliminations/"
            f"{self.elimination.id}/",
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Elimination.objects.filter(id=self.elimination.id).exists()
        )

    def test_cannot_delete_elimination_from_another_match(self):
        other_match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=aware_datetime(2026, 1, 6, 20),
        )

        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/matches/{other_match.id}/eliminations/"
            f"{self.elimination.id}/",
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Elimination.objects.filter(id=self.elimination.id).exists()
        )

    def test_cannot_delete_elimination_from_closed_match(self):
        self.match.closed = True
        self.match.save(update_fields=["closed"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/matches/{self.match.id}/eliminations/"
            f"{self.elimination.id}/",
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            Elimination.objects.filter(id=self.elimination.id).exists()
        )

    def test_cannot_delete_elimination_from_closed_week(self):
        self.week.closed = True
        self.week.save(update_fields=["closed"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/matches/{self.match.id}/eliminations/"
            f"{self.elimination.id}/",
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            Elimination.objects.filter(id=self.elimination.id).exists()
        )

class MatchDeleteHistoricalHandicapTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = Player.objects.create_user(
            username="admin_delete_handicap",
            password="test1234",
            display_name="Admin Delete",
            is_staff=True,
        )

        self.player = Player.objects.create_user(
            username="player_delete_handicap",
            password="test1234",
            display_name="Jugador Delete",
        )

        self.deck = Deck.objects.create(
            owner=self.player,
            name="Mazo Delete",
            commander="Comandante Delete",
        )

        self.season = Season.objects.create(
            name="Temporada borrado handicap",
            start_date="2026-01-01",
            active=True,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
            closed=False,
        )

        HandicapCategoryConfig.objects.create(
            category="WEAK",
            selection_weight=60,
        )
        HandicapCategoryConfig.objects.create(
            category="MEDIUM",
            selection_weight=30,
        )
        HandicapCategoryConfig.objects.create(
            category="STRONG",
            selection_weight=10,
        )

        self.definition = HandicapDefinition.objects.create(
            code="delete-test-handicap",
            name="No te flipes borrado",
            category="WEAK",
            selection_weight=1,
            grace_games=3,
            penalty_points=2,
            # Estas pruebas validan únicamente la reconstrucción del anchor
            # histórico. Desactivamos la reversión para que el resultado no
            # dependa del azar y el handicap se asigne siempre al jugador.
            reversal_base_percent=0,
            reversal_rank_step_percent=0,
            reversal_min_percent=0,
            reversal_max_percent=0,
        )

    def create_closed_match(self, hour):
        match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=aware_datetime(2026, 1, 5, hour),
            closed=True,
        )

        MatchPlayer.objects.create(
            match=match,
            player=self.player,
            deck=self.deck,
            final_position=1,
        )

        return match

    def test_deleting_handicap_anchor_rebuilds_previous_anchor(self):
        first = self.create_closed_match(20)
        anchor = self.create_closed_match(21)
        later = self.create_closed_match(22)

        grant = HandicapService.grant_handicap(
            holder=self.admin,
            season=self.season,
            administrator=self.admin,
            award_reason="Prueba de reconstrucción histórica",
        )
        handicap = HandicapService.use_grant(
            grant=grant,
            target_player=self.player,
            actor=self.admin,
        )

        self.assertEqual(
            handicap.awarded_after_match_id,
            later.id,
        )

        # Simulamos que el handicap fue asignado justo después
        # de la partida que vamos a borrar.
        handicap.awarded_after_match = anchor
        handicap.save(update_fields=["awarded_after_match"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/matches/{anchor.id}/delete/",
            {
                "confirmation": "ELIMINAR PARTIDA",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        handicap.refresh_from_db()

        self.assertEqual(
            handicap.awarded_after_match_id,
            first.id,
        )

        self.assertFalse(
            Match.objects.filter(id=anchor.id).exists()
        )

        self.assertTrue(
            Match.objects.filter(id=first.id).exists()
        )

        self.assertTrue(
            Match.objects.filter(id=later.id).exists()
        )

    def test_deleting_anchor_without_previous_match_sets_anchor_to_none(self):
        anchor = self.create_closed_match(20)
        later = self.create_closed_match(21)

        grant = HandicapService.grant_handicap(
            holder=self.admin,
            season=self.season,
            administrator=self.admin,
            award_reason="Prueba de reconstrucción histórica",
        )
        handicap = HandicapService.use_grant(
            grant=grant,
            target_player=self.player,
            actor=self.admin,
        )

        handicap.awarded_after_match = anchor
        handicap.save(update_fields=["awarded_after_match"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/matches/{anchor.id}/delete/",
            {
                "confirmation": "ELIMINAR PARTIDA",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        handicap.refresh_from_db()

        self.assertIsNone(
            handicap.awarded_after_match_id,
        )

        self.assertFalse(
            Match.objects.filter(id=anchor.id).exists()
        )

        self.assertTrue(
            Match.objects.filter(id=later.id).exists()
        )