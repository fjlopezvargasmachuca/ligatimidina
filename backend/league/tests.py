from django.test import TestCase
from rest_framework.test import APITestCase
from accounts.models import Player
from penalties.models import Penalty
from decks.models import Deck
from matches.models import Elimination, Match, MatchPlayer
from datetime import date, datetime
from django.utils import timezone
from .models import LeagueWeek, ScoringRule, Season
from .services import RankingService, ScoringService
from events.models import WeeklyEvent
from django.core.exceptions import ValidationError
from league.services import LeagueWeekService


def aware_datetime(year, month, day, hour, minute=0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))

class ScoringServiceTest(TestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="jugador1",
            password="test1234",
            display_name="Jugador 1",
        )

        self.player2 = Player.objects.create_user(
            username="jugador2",
            password="test1234",
            display_name="Jugador 2",
        )

        self.deck = Deck.objects.create(
            owner=self.player,
            name="Mazo de prueba",
            commander="Comandante de prueba",
        )

        self.deck2 = Deck.objects.create(
            owner=self.player2,
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

        self.match_player = MatchPlayer.objects.create(
            match=self.match,
            player=self.player,
            deck=self.deck,
            final_position=1,
        )

        self.match_player2 = MatchPlayer.objects.create(
            match=self.match,
            player=self.player2,
            deck=self.deck2,
            final_position=2,
        )

    def create_rule(self, code, points):
        return ScoringRule.objects.create(
            season=self.season,
            code=code,
            name=code,
            points=points,
        )

    def test_win_points(self):
        self.create_rule("WIN", 5)

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            5,
        )

    def test_second_place_points(self):
        self.create_rule("SECOND_PLACE", 3)

        service = ScoringService(self.match_player2)

        self.assertEqual(
            service.calculate(),
            3,
        )

    def test_third_place_points(self):
        self.match_player.final_position = 3
        self.match_player.save(
            update_fields=["final_position"],
        )

        self.create_rule("THIRD_PLACE", 2)

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            2,
        )

    def test_first_deck_play_points(self):
        self.create_rule("WIN", 5)
        self.create_rule("FIRST_DECK_PLAY", 2)

        self.match_player.first_play_of_deck = True
        self.match_player.save(
            update_fields=["first_play_of_deck"],
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            7,
        )

    def test_original_deck_points(self):
        self.create_rule("WIN", 5)
        self.create_rule("ORIGINAL_DECK", 2)

        self.deck.is_original = True
        self.deck.save(
            update_fields=["is_original"],
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            7,
        )

    def test_weekly_event_points(self):
        self.create_rule("WIN", 5)
        self.create_rule("WEEKLY_EVENT", 3)

        self.match_player.participates_in_weekly_event = True
        self.match_player.save(
            update_fields=["participates_in_weekly_event"],
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            8,
        )

    def test_concession_penalty(self):
        self.create_rule("WIN", 5)
        self.create_rule("CONCESSION", -2)

        self.match_player.concession_penalty = True
        self.match_player.save(
            update_fields=["concession_penalty"],
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            3,
        )

    def test_elimination_points(self):
        self.create_rule("WIN", 5)
        self.create_rule("ELIMINATION", 2)

        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=self.player2,
            turn=7,
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            7,
        )

    def test_first_elimination_points(self):
        self.create_rule("WIN", 5)
        self.create_rule("FIRST_ELIMINATION", 3)

        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=self.player2,
            turn=7,
            first_elimination=True,
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            8,
        )

    def test_multiple_eliminations_are_counted(self):
        player3 = Player.objects.create_user(
            username="jugador3",
            password="test1234",
            display_name="Jugador 3",
        )

        deck3 = Deck.objects.create(
            owner=player3,
            name="Mazo 3",
            commander="Comandante 3",
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=player3,
            deck=deck3,
            final_position=3,
        )

        self.create_rule("WIN", 5)
        self.create_rule("ELIMINATION", 2)

        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=self.player2,
            turn=5,
        )

        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=player3,
            turn=8,
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            9,
        )

    def test_all_bonus_points_are_combined(self):
        self.create_rule("WIN", 5)
        self.create_rule("FIRST_DECK_PLAY", 2)
        self.create_rule("ORIGINAL_DECK", 3)
        self.create_rule("WEEKLY_EVENT", 4)
        self.create_rule("FIRST_ELIMINATION", 2)
        self.create_rule("ELIMINATION", 1)

        self.deck.is_original = True
        self.deck.save(
            update_fields=["is_original"],
        )

        self.match_player.first_play_of_deck = True
        self.match_player.participates_in_weekly_event = True
        self.match_player.save(
            update_fields=[
                "first_play_of_deck",
                "participates_in_weekly_event",
            ],
        )

        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=self.player2,
            turn=6,
            first_elimination=True,
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            17,
        )

    def test_save_persists_calculated_points(self):
        self.create_rule("WIN", 5)

        service = ScoringService(self.match_player)

        result = service.save()

        self.assertEqual(
            result,
            5,
        )

        self.match_player.refresh_from_db()

        self.assertEqual(
            self.match_player.points,
            5,
        )

    def test_missing_rule_is_zero_points(self):
        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            0,
        )


class RankingServiceTest(TestCase):

    def setUp(self):
        self.player1 = Player.objects.create_user(
            username="jugador1",
            password="test1234",
            display_name="Jugador 1",
        )

        self.player2 = Player.objects.create_user(
            username="jugador2",
            password="test1234",
            display_name="Jugador 2",
        )

        self.deck1 = Deck.objects.create(
            owner=self.player1,
            name="Mazo 1",
            commander="Comandante 1",
        )

        self.deck2 = Deck.objects.create(
            owner=self.player2,
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

        self.create_rule("WIN", 5)
        self.create_rule("ELIMINATION", 2)

    def create_rule(self, code, points):
        return ScoringRule.objects.create(
            season=self.season,
            code=code,
            name=code,
            points=points,
        )

    def create_match(
        self,
        player1_position=1,
        player2_position=2,
        closed=True,
    ):
        match = Match.objects.create(
            league_week=self.week,
            administrator=self.player1,
            played_at=aware_datetime(2026, 1, 5, 20),
            closed=closed,
        )

        result1 = MatchPlayer.objects.create(
            match=match,
            player=self.player1,
            deck=self.deck1,
            final_position=player1_position,
        )

        result2 = MatchPlayer.objects.create(
            match=match,
            player=self.player2,
            deck=self.deck2,
            final_position=player2_position,
        )

        if closed:
            ScoringService(result1).save()
            ScoringService(result2).save()

        return match

    def test_closed_matches_are_included(self):
        self.create_match()

        standings = RankingService.get_standings(
            self.season,
        )

        player1 = next(
            player
            for player in standings
            if player["player_id"] == self.player1.id
        )

        self.assertEqual(
            player1["points"],
            5,
        )

        self.assertEqual(
            player1["games"],
            1,
        )

        self.assertEqual(
            player1["wins"],
            1,
        )

    def test_open_matches_are_ignored(self):
        self.create_match(
            closed=False,
        )

        standings = RankingService.get_standings(
            self.season,
        )

        self.assertEqual(len(standings), 2)
        self.assertTrue(all(item["games"] == 0 for item in standings))
        self.assertTrue(all(item["points"] == 0 for item in standings))

    def test_eliminations_are_counted_without_inflating_points(self):
        match = self.create_match()

        Elimination.objects.create(
            match=match,
            killer=self.player1,
            victim=self.player2,
            turn=5,
        )

        result = MatchPlayer.objects.get(
            match=match,
            player=self.player1,
        )

        ScoringService(result).save()

        standings = RankingService.get_standings(
            self.season,
        )

        player1 = next(
            player
            for player in standings
            if player["player_id"] == self.player1.id
        )

        self.assertEqual(
            player1["points"],
            7,
        )

        self.assertEqual(
            player1["eliminations"],
            1,
        )

    def test_week_standings_only_include_selected_week(self):
        self.create_match()

        week2 = LeagueWeek.objects.create(
            season=self.season,
            number=2,
            date="2026-01-12",
        )

        match2 = Match.objects.create(
            league_week=week2,
            administrator=self.player1,
            played_at=aware_datetime(2026, 1, 12, 20),
            closed=True,
        )

        result = MatchPlayer.objects.create(
            match=match2,
            player=self.player1,
            deck=self.deck1,
            final_position=1,
        )

        MatchPlayer.objects.create(
            match=match2,
            player=self.player2,
            deck=self.deck2,
            final_position=2,
        )

        ScoringService(result).save()

        standings = RankingService.get_week_standings(
            self.week,
        )

        self.assertEqual(
            len(standings),
            2,
        )

        player1 = next(
            player
            for player in standings
            if player["player_id"] == self.player1.id
        )

        self.assertEqual(
            player1["games"],
            1,
        )

        self.assertEqual(
            player1["points"],
            5,
        )

    def test_player_history_returns_closed_matches(self):
        match = self.create_match()

        Elimination.objects.create(
            match=match,
            killer=self.player1,
            victim=self.player2,
            turn=6,
        )

        result = MatchPlayer.objects.get(
            match=match,
            player=self.player1,
        )

        ScoringService(result).save()

        history = RankingService.get_player_history(
            self.player1,
            self.season,
        )

        self.assertEqual(
            len(history),
            1,
        )

        self.assertEqual(
            history[0]["week_number"],
            1,
        )

        self.assertEqual(
            history[0]["deck_id"],
            self.deck1.id,
        )

        self.assertEqual(
            history[0]["final_position"],
            1,
        )

        self.assertEqual(
            history[0]["points"],
            7,
        )

        self.assertEqual(
            history[0]["eliminations"],
            1,
        )


class StandingsAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="jugador1",
            password="test1234",
            display_name="Jugador 1",
        )

        self.season = Season.objects.create(
            name="Temporada API",
            start_date="2026-01-01",
            active=True,
        )

        self.client.force_authenticate(user=self.player)

    def test_standings_endpoint_returns_active_season(self):
        response = self.client.get(
            "/api/league/standings/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["season"]["id"],
            self.season.id,
        )

        self.assertEqual(
            response.data["season"]["name"],
            "Temporada API",
        )

        self.assertEqual(len(response.data["standings"]), 1)
        self.assertEqual(response.data["standings"][0]["player_id"], self.player.id)
        self.assertEqual(response.data["standings"][0]["games"], 0)

    def test_standings_endpoint_returns_404_without_active_season(self):
        self.season.active = False
        self.season.save(
            update_fields=["active"],
        )

        response = self.client.get(
            "/api/league/standings/",
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class CurrentWeekAPITest(APITestCase):

    def setUp(self):
        from django.utils import timezone
        from datetime import timedelta
        self.player = Player.objects.create_user(
            username="week_viewer", password="test1234", display_name="Week Viewer"
        )
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        self.season = Season.objects.create(
            name="Temporada API", start_date=monday, end_date=monday + timedelta(days=6), active=True,
        )
        self.event = WeeklyEvent.objects.create(
            name="Archenemy", description="Evento de prueba", rules="Reglas del evento", extra_points=3,
        )
        self.week = LeagueWeek.objects.create(
            season=self.season, number=1, date=monday, weekly_event=self.event, closed=False,
        )
        self.client.force_authenticate(user=self.player)

    def test_current_week_endpoint_returns_week_and_event(self):
        response = self.client.get(
            "/api/league/current-week/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.week.id,
        )

        self.assertEqual(
            response.data["number"],
            1,
        )

        self.assertFalse(
            response.data["closed"],
        )

        self.assertEqual(
            response.data["weekly_event"]["id"],
            self.event.id,
        )

        self.assertEqual(
            response.data["weekly_event"]["name"],
            "Archenemy",
        )

        self.assertEqual(
            response.data["weekly_event"]["extra_points"],
            3,
        )

    def test_current_week_endpoint_returns_404_when_week_is_closed(self):
        self.week.closed = True
        self.week.save(
            update_fields=["closed"],
        )

        response = self.client.get(
            "/api/league/current-week/",
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class LeagueWeekAdminAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="jugador",
            password="test1234",
            display_name="Jugador",
        )

        self.admin = Player.objects.create_user(
            username="admin",
            password="test1234",
            display_name="Administrador",
            is_staff=True,
        )

        self.season = Season.objects.create(
            name="Temporada API",
            start_date="2026-01-01",
            active=True,
        )

        self.event1 = WeeklyEvent.objects.create(
            name="Archenemy",
            description="Evento Archenemy",
            rules="Reglas Archenemy",
            extra_points=3,
        )

        self.event2 = WeeklyEvent.objects.create(
            name="Planechase",
            description="Evento Planechase",
            rules="Reglas Planechase",
            extra_points=4,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
            weekly_event=self.event1,
            closed=False,
        )

    def test_authenticated_user_can_view_week(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.get(
            f"/api/league/weeks/{self.week.id}/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.week.id,
        )

        self.assertEqual(
            response.data["weekly_event"],
            self.event1.id,
        )

        self.assertEqual(
            response.data["weekly_event_name"],
            "Archenemy",
        )

    def test_anonymous_user_cannot_view_week(self):
        response = self.client.get(
            f"/api/league/weeks/{self.week.id}/",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_non_admin_cannot_change_week_event(self):
        self.client.force_authenticate(
            user=self.player,
        )

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {
                "weekly_event": self.event2.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.week.refresh_from_db()

        self.assertEqual(
            self.week.weekly_event_id,
            self.event1.id,
        )

    def test_admin_can_change_week_event(self):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {
                "weekly_event": self.event2.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.week.refresh_from_db()

        self.assertEqual(
            self.week.weekly_event_id,
            self.event2.id,
        )

        self.assertEqual(
            response.data["weekly_event_name"],
            "Planechase",
        )

    def test_admin_can_remove_week_event(self):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {
                "weekly_event": None,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.week.refresh_from_db()

        self.assertIsNone(
            self.week.weekly_event_id,
        )

    def test_admin_cannot_change_closed_week(self):
        self.week.closed = True
        self.week.save(
            update_fields=["closed"],
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {
                "weekly_event": self.event2.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.week.refresh_from_db()

        self.assertEqual(
            self.week.weekly_event_id,
            self.event1.id,
        )

    def test_admin_cannot_assign_nonexistent_event(self):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {
                "weekly_event": 999999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "weekly_event",
            response.data,
        )

class LeagueWeekAdminAPITest(APITestCase):
    def setUp(self):
        from datetime import date, datetime

        from accounts.models import Player
        from events.models import WeeklyEvent
        from league.models import LeagueWeek, Season

        self.player = Player.objects.create_user(
            username="jugador_jornada",
            password="test1234",
            display_name="Jugador Jornada",
        )

        self.admin = Player.objects.create_user(
            username="admin_jornada",
            password="test1234",
            display_name="Administrador Jornada",
            is_staff=True,
        )

        self.season = Season.objects.create(
            name="Temporada jornadas",
            start_date=date(2026, 1, 1),
            active=True,
        )

        self.event = WeeklyEvent.objects.create(
            name="Archenemy",
            description="Un jugador será Archenemy.",
            rules="El Archenemy juega contra los demás.",
            extra_points=3,
            active=True,
        )

        self.event_2 = WeeklyEvent.objects.create(
            name="Planechase",
            description="Evento Planechase.",
            rules="Reglas de Planechase.",
            extra_points=4,
            active=True,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date=date(2026, 1, 5),
            weekly_event=self.event,
            closed=False,
        )

    def test_authenticated_user_can_retrieve_week(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.get(
            f"/api/league/weeks/{self.week.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.week.id)
        self.assertEqual(response.data["number"], 1)
        self.assertEqual(
            response.data["weekly_event"],
            self.event.id,
        )
        self.assertEqual(
            response.data["weekly_event_name"],
            "Archenemy",
        )

    def test_unauthenticated_user_cannot_retrieve_week(self):
        response = self.client.get(
            f"/api/league/weeks/{self.week.id}/"
        )

        self.assertEqual(response.status_code, 403)

    def test_authenticated_non_admin_cannot_update_week(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {"weekly_event": self.event_2.id},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.week.refresh_from_db()

        self.assertEqual(
            self.week.weekly_event_id,
            self.event.id,
        )

    def test_admin_can_assign_weekly_event(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {"weekly_event": self.event_2.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.week.refresh_from_db()

        self.assertEqual(
            self.week.weekly_event_id,
            self.event_2.id,
        )

        self.assertEqual(
            response.data["weekly_event_name"],
            "Planechase",
        )

    def test_admin_can_remove_weekly_event(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {"weekly_event": None},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.week.refresh_from_db()

        self.assertIsNone(
            self.week.weekly_event_id,
        )

        self.assertIsNone(
            response.data["weekly_event_name"],
        )

    def test_admin_cannot_assign_nonexistent_event(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {"weekly_event": 999999},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("weekly_event", response.data)

        self.week.refresh_from_db()

        self.assertEqual(
            self.week.weekly_event_id,
            self.event.id,
        )

    def test_admin_cannot_modify_closed_week(self):
        self.week.closed = True
        self.week.save(update_fields=["closed"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/league/weeks/{self.week.id}/",
            {"weekly_event": self.event_2.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.week.refresh_from_db()

        self.assertTrue(self.week.closed)
        self.assertEqual(
            self.week.weekly_event_id,
            self.event.id,
        )

class PlayerStatsAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="jugador1",
            password="test1234",
            display_name="Jugador 1",
        )

        self.player1 = self.player

        self.player2 = Player.objects.create_user(
            username="jugador2",
            password="test1234",
            display_name="Jugador 2",
        )

        self.deck1 = Deck.objects.create(
            owner=self.player1,
            name="Mazo 1",
            commander="Comandante 1",
        )

        self.deck2 = Deck.objects.create(
            owner=self.player2,
            name="Mazo 2",
            commander="Comandante 2",
        )

        self.season = Season.objects.create(
            name="Temporada API",
            start_date="2026-01-01",
            active=True,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.player1,
            played_at=aware_datetime(2026, 1, 5, 20),
            closed=True,
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.player1,
            deck=self.deck1,
            final_position=1,
            points=10,
        )

        MatchPlayer.objects.create(
            match=self.match,
            player=self.player2,
            deck=self.deck2,
            final_position=2,
            points=3,
        )

    def test_active_penalties_are_subtracted_from_ranking(self):
        penalty = Penalty.objects.create(
            player=self.player1,
            season=self.season,
            league_week=self.week,
            reason="Penalización de prueba",
            points=2,
            administrator=self.player1,
            active=True,
        )

        from .services import RankingService

        standings = RankingService.get_standings(
            self.season,
        )

        player1 = next(
            player
            for player in standings
            if player["player_id"] == self.player1.id
        )

        self.assertEqual(
            player1["points"],
            8,
        )

        self.assertEqual(
            player1["penalty_points"],
            2,
        )

        self.assertEqual(
            player1["penalties_count"],
            1,
        )

    def test_inactive_penalties_do_not_affect_ranking(self):
        Penalty.objects.create(
            player=self.player1,
            season=self.season,
            league_week=self.week,
            reason="Penalización anulada",
            points=2,
            administrator=self.player1,
            active=False,
        )

        from .services import RankingService

        standings = RankingService.get_standings(
            self.season,
        )

        player1 = next(
            player
            for player in standings
            if player["player_id"] == self.player1.id
        )

        self.assertEqual(
            player1["points"],
            10,
        )

        self.assertEqual(
            player1["penalty_points"],
            0,
        )

        self.assertEqual(
            player1["penalties_count"],
            0,
        )

    def test_player_with_only_penalty_appears_in_ranking(self):
        player3 = Player.objects.create_user(
            username="jugador3",
            password="test1234",
            display_name="Jugador 3",
        )

        Penalty.objects.create(
            player=player3,
            season=self.season,
            league_week=self.week,
            reason="Penalización sin partida",
            points=3,
            administrator=self.player1,
            active=True,
        )

        from .services import RankingService

        standings = RankingService.get_standings(
            self.season,
        )

        player3_standing = next(
            player
            for player in standings
            if player["player_id"] == player3.id
        )

        self.assertEqual(
            player3_standing["points"],
            -3,
        )

        self.assertEqual(
            player3_standing["games"],
            0,
        )

        self.assertEqual(
            player3_standing["wins"],
            0,
        )

        self.assertEqual(
            player3_standing["penalty_points"],
            3,
        )

        self.assertEqual(
            player3_standing["penalties_count"],
            1,
        )

    def test_player_stats_include_penalties(self):
        Penalty.objects.create(
            player=self.player1,
            season=self.season,
            league_week=self.week,
            reason="Penalización de estadísticas",
            points=2,
            administrator=self.player1,
            active=True,
        )

        self.client.force_authenticate(
            user=self.player1,
        )

        response = self.client.get(
            f"/api/league/players/{self.player.id}/stats/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["penalties_count"],
            1,
        )

        self.assertEqual(
            response.data["penalty_points"],
            2,
        )

        self.assertEqual(
            response.data["points"],
            8,
        )

        self.assertEqual(
            len(response.data["penalties"]),
            1,
        )

        self.assertEqual(
            response.data["penalties"][0]["reason"],
            "Penalización de estadísticas",
        )

        self.assertEqual(
            response.data["penalties"][0]["points"],
            2,
        )

        self.assertTrue(
            response.data["penalties"][0]["active"],
        )

class LeagueWeekCloseServiceTest(TestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(
            username="week_admin",
            password="testpass123",
            display_name="Administrador Jornada",
            is_staff=True,
        )

        self.player1 = Player.objects.create_user(
            username="week_player1",
            password="testpass123",
            display_name="Jugador 1",
        )

        self.player2 = Player.objects.create_user(
            username="week_player2",
            password="testpass123",
            display_name="Jugador 2",
        )

        self.season = Season.objects.create(
            name="Temporada cierre",
            start_date=date.today(),
            active=True,
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date=date.today(),
        )

        self.deck1 = Deck.objects.create(
            owner=self.player1,
            name="Mazo 1",
            commander="Comandante 1",
        )

        self.deck2 = Deck.objects.create(
            owner=self.player2,
            name="Mazo 2",
            commander="Comandante 2",
        )

    def create_match(self, closed=False):
        match = Match.objects.create(
            league_week=self.week,
            administrator=self.admin,
            played_at=timezone.now(),
            closed=closed,
        )

        MatchPlayer.objects.create(
            match=match,
            player=self.player1,
            deck=self.deck1,
            final_position=1,
        )

        MatchPlayer.objects.create(
            match=match,
            player=self.player2,
            deck=self.deck2,
            final_position=2,
        )

        return match

    def test_cannot_close_week_without_matches(self):
        with self.assertRaises(ValidationError):
            LeagueWeekService.close_week(self.week)

        self.week.refresh_from_db()
        self.assertFalse(self.week.closed)

    def test_cannot_close_week_with_open_match(self):
        self.create_match(closed=False)

        with self.assertRaises(ValidationError):
            LeagueWeekService.close_week(self.week)

        self.week.refresh_from_db()
        self.assertFalse(self.week.closed)

    def test_can_close_week_when_all_matches_are_closed(self):
        self.create_match(closed=True)

        LeagueWeekService.close_week(self.week)

        self.week.refresh_from_db()
        self.assertTrue(self.week.closed)

    def test_cannot_close_week_twice(self):
        self.create_match(closed=True)

        LeagueWeekService.close_week(self.week)

        with self.assertRaises(ValidationError):
            LeagueWeekService.close_week(self.week)

class AutomaticLeagueCalendarTest(TestCase):
    def setUp(self):
        self.event1 = WeeklyEvent.objects.create(name="Evento A", description="A", rules="A")
        self.event2 = WeeklyEvent.objects.create(name="Evento B", description="B", rules="B")
        self.event3 = WeeklyEvent.objects.create(name="Evento C", description="C", rules="C")

    def test_generates_complete_monday_to_sunday_weeks_and_balances_events(self):
        from datetime import date, datetime
        season = Season.objects.create(
            name="Calendario", start_date=date(2026, 9, 1), end_date=date(2026, 10, 4), active=True
        )
        weeks = list(LeagueWeekService.generate_weeks(season))
        self.assertEqual([week.date.isoformat() for week in weeks], [
            "2026-09-07", "2026-09-14", "2026-09-21", "2026-09-28"
        ])
        first_three = [week.weekly_event_id for week in weeks[:3]]
        self.assertEqual(len(set(first_three)), 3)
        counts = {}
        for week in season.weeks.all():
            counts[week.weekly_event_id] = counts.get(week.weekly_event_id, 0) + 1
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_inactive_player_is_excluded_and_active_zero_game_player_is_included(self):
        from datetime import date, datetime
        season = Season.objects.create(name="Ranking", start_date=date(2026, 9, 1), active=True)
        active = Player.objects.create_user(username="active_zero", password="pass12345", display_name="Activo")
        inactive = Player.objects.create_user(username="inactive_zero", password="pass12345", display_name="Inactivo", is_active=False)
        standings = RankingService.get_standings(season)
        ids = {item["player_id"] for item in standings}
        self.assertIn(active.id, ids)
        self.assertNotIn(inactive.id, ids)



class LeagueModeAndPrizePoolTest(APITestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(
            username="mode-admin", password="test1234", display_name="Admin", is_staff=True,
        )
        self.standard = Player.objects.create_user(
            username="mode-standard", password="test1234", display_name="Standard",
        )
        self.premium = Player.objects.create_user(
            username="mode-premium", password="test1234", display_name="Premium",
            membership_plan=Player.MembershipPlan.SUPPORTER,
            subscription_paid_until=date(2026, 9, 30),
        )

    def test_free_mode_allows_three_weekly_games_for_everyone(self):
        from .models import LeagueSettings
        settings = LeagueSettings.load()
        settings.mode = LeagueSettings.LeagueMode.FREE
        settings.save()
        self.assertEqual(self.standard.weekly_match_limit(on_date=date(2026, 9, 15)), 3)

    def test_premium_mode_distinguishes_standard_and_premium(self):
        from .models import LeagueSettings
        settings = LeagueSettings.load()
        settings.mode = LeagueSettings.LeagueMode.PREMIUM
        settings.save()
        self.assertEqual(self.standard.weekly_match_limit(on_date=date(2026, 9, 15)), 1)
        self.assertEqual(self.premium.weekly_match_limit(on_date=date(2026, 9, 15)), 3)

    def test_premium_without_end_date_counts_as_active_and_in_prize_pool(self):
        from .models import LeagueSettings
        from .services import PrizePoolService
        self.premium.subscription_paid_until = None
        self.premium.save(update_fields=["subscription_paid_until"])
        settings = LeagueSettings.load()
        settings.mode = LeagueSettings.LeagueMode.PREMIUM
        settings.subscription_fee = 10
        settings.prize_pool_percent = 20
        settings.save()
        self.assertTrue(self.premium.has_active_subscription(on_date=date(2026, 9, 15)))
        self.assertEqual(self.premium.weekly_match_limit(on_date=date(2026, 9, 15)), 3)
        summary = PrizePoolService.summary(on_date=date(2026, 9, 15))
        self.assertEqual(summary["premium_participants"], 1)
        self.assertEqual(summary["monthly_contribution"], 2)

    def test_prize_pool_uses_configured_twenty_percent(self):
        from .models import LeagueSettings
        from .services import PrizePoolService
        settings = LeagueSettings.load()
        settings.mode = LeagueSettings.LeagueMode.PREMIUM
        settings.subscription_fee = 10
        settings.prize_pool_percent = 20
        settings.save()
        summary = PrizePoolService.summary(on_date=date(2026, 9, 15))
        self.assertEqual(summary["premium_participants"], 1)
        self.assertEqual(summary["monthly_contribution"], 2)
        self.assertEqual(summary["top_1"], 1)
        self.assertEqual(str(summary["top_2"]), "0.60")
        self.assertEqual(str(summary["top_3"]), "0.40")

    def test_only_admin_can_change_league_mode(self):
        self.client.force_authenticate(user=self.standard)
        denied = self.client.patch("/api/league/settings/", {"mode": "FREE"}, format="json")
        self.assertEqual(denied.status_code, 403)
        self.client.force_authenticate(user=self.admin)
        allowed = self.client.patch("/api/league/settings/", {"mode": "FREE"}, format="json")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.data["mode"], "FREE")


class SeasonFinalizationTest(APITestCase):
    def test_finalizing_season_removes_it_from_active_competition(self):
        admin = Player.objects.create_user(username="final-admin", password="test1234", is_staff=True)
        season = Season.objects.create(name="Final", start_date=date(2026, 9, 1), active=True)
        self.client.force_authenticate(user=admin)
        response = self.client.post(f"/api/league/seasons/{season.id}/finalize/")
        self.assertEqual(response.status_code, 200)
        season.refresh_from_db()
        self.assertFalse(season.active)
        self.assertIsNotNone(season.finalized_at)


class WeeklyEventSpecificPointsTest(TestCase):
    def test_weekly_event_uses_event_extra_points_when_event_is_assigned(self):
        player = Player.objects.create_user(username="event-points", password="test1234")
        deck = Deck.objects.create(owner=player, name="Deck", commander="Commander")
        season = Season.objects.create(name="Event points", start_date=date(2026, 9, 1))
        event = WeeklyEvent.objects.create(name="Especial", description="x", rules="x", extra_points=7)
        week = LeagueWeek.objects.create(season=season, number=1, date=date(2026, 9, 7), weekly_event=event)
        match = Match.objects.create(league_week=week, administrator=player, played_at=aware_datetime(2026, 9, 7, 20))
        result = MatchPlayer.objects.create(match=match, player=player, deck=deck, final_position=1, participates_in_weekly_event=True)
        ScoringRule.objects.create(season=season, code="WIN", name="Win", points=5)
        ScoringRule.objects.create(season=season, code="WEEKLY_EVENT", name="Legacy", points=3)
        self.assertEqual(ScoringService(result).calculate(), 12)

class ScoringRuleDeleteAPITest(APITestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(username="rule-admin", password="test1234", is_staff=True)
        self.season = Season.objects.create(name="Reglas", start_date=date(2026, 9, 1), active=True)
        self.rule = ScoringRule.objects.create(season=self.season, code="WIN", name="Victoria", points=3)
        self.client.force_authenticate(user=self.admin)

    def test_admin_can_delete_rule_before_closed_weeks(self):
        response = self.client.delete(f"/api/league/scoring-rules/{self.rule.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ScoringRule.objects.filter(pk=self.rule.id).exists())

    def test_admin_cannot_delete_rule_after_closed_week(self):
        LeagueWeek.objects.create(season=self.season, number=1, date=date(2026, 9, 7), closed=True)
        response = self.client.delete(f"/api/league/scoring-rules/{self.rule.id}/")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ScoringRule.objects.filter(pk=self.rule.id).exists())
