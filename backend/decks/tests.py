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

class DeckDetailAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="detail_player",
            password="test1234",
            display_name="Detail Player",
        )

        self.deck = Deck.objects.create(
            owner=self.player,
            name="Mazo detalle",
            commander="Comandante detalle",
            active=True,
        )

        self.inactive_deck = Deck.objects.create(
            owner=self.player,
            name="Mazo inactivo",
            commander="Comandante inactivo",
            active=False,
        )

    def test_deck_detail_returns_active_deck(self):
        response = self.client.get(
            f"/api/decks/{self.deck.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["name"],
            "Mazo detalle",
        )
        self.assertEqual(
            response.data["commander"],
            "Comandante detalle",
        )
        self.assertEqual(
            response.data["owner_name"],
            "Detail Player",
        )
        self.assertTrue(response.data["active"])
        self.assertNotIn("is_original", response.data)

    def test_deck_detail_does_not_return_inactive_deck(self):
        response = self.client.get(
            f"/api/decks/{self.inactive_deck.id}/"
        )

        self.assertEqual(response.status_code, 404)


class DeckCreateAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="create_player",
            password="test1234",
            display_name="Create Player",
        )

        self.payload = {
            "name": "Mazo nuevo",
            "commander": "Comandante nuevo",
            "description": "Descripción del mazo",
            "deck_url": "https://example.com/deck",
            "deckcheck_id": "deckcheck-123",
        }

    def test_anonymous_user_cannot_create_deck(self):
        response = self.client.post(
            "/api/decks/create/",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Deck.objects.count(),
            0,
        )

    def test_authenticated_user_creates_deck_with_own_owner(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.post(
            "/api/decks/create/",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        deck = Deck.objects.get(
            name="Mazo nuevo",
        )

        self.assertEqual(
            deck.owner,
            self.player,
        )
        self.assertEqual(
            deck.commander,
            "Comandante nuevo",
        )
    def test_authenticated_user_cannot_set_is_original(self):
        self.client.force_authenticate(user=self.player)

        payload = {
            **self.payload,
            "is_original": True,
        }

        response = self.client.post(
            "/api/decks/create/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        deck = Deck.objects.get(name="Mazo nuevo")
        self.assertFalse(deck.is_original)

class DeckUpdateAPITest(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create_user(
            username="deck_owner",
            password="test1234",
            display_name="Deck Owner",
        )
        self.other_player = Player.objects.create_user(
            username="other_player",
            password="test1234",
            display_name="Other Player",
        )
        self.deck = Deck.objects.create(
            owner=self.owner,
            name="Mazo original",
            commander="Comandante original",
            description="Descripción original",
        )

    def test_owner_can_update_own_deck(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/decks/{self.deck.id}/update/",
            {
                "name": "Mazo actualizado",
                "description": "Nueva descripción",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.deck.refresh_from_db()
        self.assertEqual(self.deck.name, "Mazo actualizado")
        self.assertEqual(self.deck.description, "Nueva descripción")

    def test_user_cannot_update_another_users_deck(self):
        self.client.force_authenticate(user=self.other_player)

        response = self.client.patch(
            f"/api/decks/{self.deck.id}/update/",
            {
                "name": "Intento de modificación",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        self.deck.refresh_from_db()
        self.assertEqual(self.deck.name, "Mazo original")
        
    def test_owner_cannot_set_is_original(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/decks/{self.deck.id}/update/",
            {
                "name": "Mazo actualizado",
                "is_original": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.deck.refresh_from_db()
        self.assertEqual(self.deck.name, "Mazo actualizado")
        self.assertFalse(self.deck.is_original)

class DeckDeleteAPITest(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create_user(
            username="delete_owner",
            password="test1234",
            display_name="Delete Owner",
        )
        self.other_player = Player.objects.create_user(
            username="delete_other",
            password="test1234",
            display_name="Delete Other",
        )
        self.deck = Deck.objects.create(
            owner=self.owner,
            name="Mazo para borrar",
            commander="Comandante",
        )

    def test_owner_can_delete_own_deck(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(
            f"/api/decks/{self.deck.id}/delete/"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Deck.objects.filter(id=self.deck.id).exists()
        )

    def test_user_cannot_delete_another_users_deck(self):
        self.client.force_authenticate(user=self.other_player)

        response = self.client.delete(
            f"/api/decks/{self.deck.id}/delete/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Deck.objects.filter(id=self.deck.id).exists()
        )