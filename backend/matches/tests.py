from django.test import TestCase

from accounts.models import Player
from decks.models import Deck
from league.models import LeagueWeek, ScoringRule, Season
from .models import Match, MatchPlayer
from .services import MatchService


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