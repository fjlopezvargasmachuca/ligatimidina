from django.test import TestCase

from accounts.models import Player
from decks.models import Deck
from matches.models import Elimination, Match, MatchPlayer
from .models import LeagueWeek, Season, ScoringRule


class ScoringServiceTest(TestCase):

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
            played_at="2026-01-05 20:00",
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

    def test_victory_gives_points(self):
        from .services import ScoringService

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            5,
        )

    def test_save_stores_points(self):
        from .services import ScoringService

        service = ScoringService(self.match_player)

        service.save()

        self.match_player.refresh_from_db()

        self.assertEqual(
            self.match_player.points,
            5,
        )

    def test_first_elimination_gives_points(self):
        from .services import ScoringService

        ScoringRule.objects.create(
            season=self.season,
            code="FIRST_ELIMINATION",
            name="Primera eliminación",
            points=2,
        )

        player2 = Player.objects.create_user(
            username="jugador2",
            password="test1234",
            display_name="Jugador 2",
        )

        Elimination.objects.create(
            match=self.match,
            killer=self.player,
            victim=player2,
            turn=5,
            first_elimination=True,
        )

        service = ScoringService(self.match_player)

        self.assertEqual(
            service.calculate(),
            7,
        )

    def test_match_player_stores_deck_snapshot(self):
        self.assertEqual(
            self.match_player.deck_name,
            "Mazo de prueba",
        )

        self.assertEqual(
            self.match_player.commander_name,
            "Comandante de prueba",
        )
        def test_match_player_copies_deck_snapshot_on_creation(self):
            self.assertEqual(self.match_player.deck_name, "Mazo de prueba")
        self.assertEqual(
            self.match_player.commander_name,
            "Comandante de prueba",
        )

    def test_match_player_snapshot_does_not_change_when_deck_changes(self):
        original_deck_name = self.match_player.deck_name
        original_commander = self.match_player.commander_name

        self.deck.name = "Mazo cambiado"
        self.deck.commander = "Comandante cambiado"
        self.deck.save()

        self.match_player.refresh_from_db()

        self.assertEqual(self.match_player.deck_name, original_deck_name)
        self.assertEqual(
            self.match_player.commander_name,
            original_commander,
        )


class RankingServiceTest(TestCase):

    def setUp(self):
        self.player1 = Player.objects.create_user(
            username="ranking1",
            password="test1234",
            display_name="Ranking 1",
        )

        self.player2 = Player.objects.create_user(
            username="ranking2",
            password="test1234",
            display_name="Ranking 2",
        )

        self.deck1 = Deck.objects.create(
            owner=self.player1,
            name="Mazo Ranking 1",
            commander="Comandante 1",
        )

        self.deck2 = Deck.objects.create(
            owner=self.player2,
            name="Mazo Ranking 2",
            commander="Comandante 2",
        )

        self.season = Season.objects.create(
            name="Temporada Ranking",
            start_date="2026-01-01",
        )

        self.week = LeagueWeek.objects.create(
            season=self.season,
            number=1,
            date="2026-01-05",
        )

        self.match = Match.objects.create(
            league_week=self.week,
            administrator=self.player1,
            played_at="2026-01-05 20:00",
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

        Elimination.objects.create(
            match=self.match,
            killer=self.player1,
            victim=self.player2,
            turn=5,
            first_elimination=True,
        )

    def test_ranking_uses_closed_matches(self):
        from .services import RankingService

        standings = RankingService.get_standings(
            self.season
        )

        self.assertEqual(
            len(standings),
            2,
        )

        self.assertEqual(
            standings[0]["display_name"],
            "Ranking 1",
        )

        self.assertEqual(
            standings[0]["points"],
            10,
        )

        self.assertEqual(
            standings[0]["wins"],
            1,
        )

        self.assertEqual(
            standings[0]["eliminations"],
            1,
        )

        self.assertEqual(
            standings[1]["display_name"],
            "Ranking 2",
        )

        self.assertEqual(
            standings[1]["points"],
            3,
        )

        self.assertEqual(
            standings[1]["eliminations"],
            0,
        )

    def test_week_ranking_uses_only_closed_matches_from_week(self):
        from .services import RankingService

        standings = RankingService.get_week_standings(
            self.week
        )

        self.assertEqual(
            len(standings),
            2,
        )

        self.assertEqual(
            standings[0]["display_name"],
            "Ranking 1",
        )

        self.assertEqual(
            standings[0]["points"],
            10,
        )

        self.assertEqual(
            standings[0]["wins"],
            1,
        )

        self.assertEqual(
            standings[0]["eliminations"],
            1,
        )

        self.assertEqual(
            standings[1]["display_name"],
            "Ranking 2",
        )

        self.assertEqual(
            standings[1]["points"],
            3,
        )

    def test_player_history_returns_closed_matches(self):
        from .services import RankingService

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
            history[0]["deck_name"],
            "Mazo Ranking 1",
        )

        self.assertEqual(
            history[0]["commander"],
            "Comandante 1",
        )

        self.assertEqual(
            history[0]["final_position"],
            1,
        )

        self.assertEqual(
            history[0]["points"],
            10,
        )

        self.assertEqual(
            history[0]["eliminations"],
            1,
        )
    