from rest_framework.test import APITestCase
from accounts.models import Player
from .models import Deck


class DeckListAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="deck_player",
            password="test1234",
            display_name="Deck Player",
        )

        Deck.objects.create(
            owner=self.player,
            name="Mazo activo",
            commander="Comandante activo",
            active=True,
        )

        Deck.objects.create(
            owner=self.player,
            name="Mazo inactivo",
            commander="Comandante inactivo",
            active=False,
        )

    def test_deck_list_returns_only_active_decks(self):
        response = self.client.get("/api/decks/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        deck = response.data[0]

        self.assertEqual(deck["name"], "Mazo activo")
        self.assertEqual(deck["commander"], "Comandante activo")
        self.assertEqual(deck["owner_name"], "Deck Player")
        self.assertTrue(deck["active"])
        self.assertNotIn("is_original", deck)