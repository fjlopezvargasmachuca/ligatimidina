import requests
from django.test import TestCase
from rest_framework.test import APITestCase
from accounts.models import Player
from .models import Deck, DeckAnalysis
from unittest.mock import patch
from decks.services import DeckCheckService

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

    def test_deck_analysis_returns_analysis(self):
        analysis = DeckAnalysis.objects.create(
            deck=self.deck,
            bracket="3",
            win_conditions=2,
            game_changers=1,
            crispi_score=7.50,
        )

        response = self.client.get(
            f"/api/decks/{self.deck.id}/analysis/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["bracket"], "3")
        self.assertEqual(response.data["win_conditions"], 2)
        self.assertEqual(response.data["game_changers"], 1)
        self.assertEqual(
            str(response.data["crispi_score"]),
            "7.50",
        )
        self.assertNotIn("raw_data", response.data)

    def test_deck_analysis_returns_404_when_analysis_does_not_exist(self):
        response = self.client.get(
            f"/api/decks/{self.deck.id}/analysis/"
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

    @patch("decks.views.DeckCheckService.get_deck")
    def test_authenticated_user_creates_deck_with_own_owner(
        self,
        mock_get_deck,
    ):
        mock_get_deck.return_value = {
            "id": "deckcheck-123",
            "bracket": 3,
            "name": "Mazo nuevo",
        }

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

        mock_get_deck.assert_called_once_with(
            deck_id="deckcheck-123"
        )

        self.assertTrue(
            DeckAnalysis.objects.filter(
                deck=deck,
                bracket="3",
            ).exists()
        )

    @patch("decks.views.DeckCheckService.get_deck")
    def test_authenticated_user_cannot_set_is_original(
        self,
        mock_get_deck,
    ):
        mock_get_deck.return_value = {
            "id": "deckcheck-123",
            "bracket": 3,
            "name": "Mazo nuevo",
        }
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

        mock_get_deck.assert_called_once_with(
            deck_id="deckcheck-123"
        )

        self.assertTrue(
            DeckAnalysis.objects.filter(
                deck=deck,
                bracket="3",
            ).exists()
        )

    @patch("decks.views.DeckCheckService.get_deck_id_from_url")
    def test_create_deck_without_deckcheck_id_when_deckcheck_returns_none(
        self,
        mock_get_deck_id,
    ):
        mock_get_deck_id.return_value = None

        self.client.force_authenticate(user=self.player)

        payload = {
            **self.payload,
            "deckcheck_id": "",
        }

        response = self.client.post(
            "/api/decks/create/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        deck = Deck.objects.get(name="Mazo nuevo")

        self.assertEqual(deck.deckcheck_id, "")

        mock_get_deck_id.assert_called_once_with(
            self.payload["deck_url"]
        )
    @patch("decks.views.DeckCheckService.get_deck")
    @patch("decks.views.DeckCheckService.get_deck_id_from_url")
    def test_create_deck_uses_existing_deckcheck_id(
        self,
        mock_get_deck_id,
        mock_get_deck,
    ):
        mock_get_deck.return_value = {
            "id": "deckcheck-123",
            "bracket": 3,
            "name": "Mazo nuevo",
        }

        self.client.force_authenticate(user=self.player)

        response = self.client.post(
            "/api/decks/create/",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        deck = Deck.objects.get(name="Mazo nuevo")

        self.assertEqual(
            deck.deckcheck_id,
            "deckcheck-123",
        )

        mock_get_deck_id.assert_not_called()

        mock_get_deck.assert_called_once_with(
            deck_id="deckcheck-123"
        )

        self.assertTrue(
            DeckAnalysis.objects.filter(
                deck=deck,
                bracket="3",
            ).exists()
        )

    @patch("decks.views.DeckCheckService.get_deck")
    @patch("decks.views.DeckCheckService.get_deck_id_from_url")
    def test_create_deck_gets_deckcheck_id_from_url(
        self,
        mock_get_deck_id,
        mock_get_deck,
    ):
        mock_get_deck_id.return_value = "deckcheck-999"
        mock_get_deck.return_value = {
            "id": "deckcheck-999",
            "bracket": 3,
            "name": "Mazo nuevo",
        }

        self.client.force_authenticate(user=self.player)

        payload = {
            **self.payload,
            "deckcheck_id": "",
        }

        response = self.client.post(
            "/api/decks/create/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        deck = Deck.objects.get(name="Mazo nuevo")

        self.assertEqual(
            deck.deckcheck_id,
            "deckcheck-999",
        )

        mock_get_deck_id.assert_called_once_with(
            self.payload["deck_url"]
        )

        mock_get_deck.assert_called_once_with(
            deck_id="deckcheck-999"
        )

        self.assertTrue(
            DeckAnalysis.objects.filter(
                deck=deck,
                bracket="3",
            ).exists()
        )


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
        self.assertEqual(
            self.deck.description,
            "Nueva descripción",
        )
    @patch("decks.views.DeckCheckService.get_deck")
    @patch("decks.views.DeckCheckService.get_deck_id_from_url")
    def test_owner_update_deck_url_refreshes_deckcheck_analysis(
        self,
        mock_get_deck_id,
        mock_get_deck,
    ):
        mock_get_deck_id.return_value = "deckcheck-456"
        mock_get_deck.return_value = {
            "id": "deckcheck-456",
            "bracket": 4,
            "name": "Mazo actualizado",
        }

        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/decks/{self.deck.id}/update/",
            {
                "deck_url": "https://deckcheck.co/decks/deckcheck-456",
                "deckcheck_id": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.deck.refresh_from_db()

        self.assertEqual(
            self.deck.deckcheck_id,
            "deckcheck-456",
        )

        mock_get_deck_id.assert_called_once_with(
            "https://deckcheck.co/decks/deckcheck-456"
        )

        mock_get_deck.assert_called_once_with(
            deck_id="deckcheck-456"
        )

        analysis = DeckAnalysis.objects.get(deck=self.deck)

        self.assertEqual(analysis.bracket, "4")

        @patch("decks.views.DeckCheckService.get_deck")
        @patch("decks.views.DeckCheckService.get_deck_id_from_url")
        def test_owner_update_without_deckcheck_change_does_not_refresh_analysis(
            self,
            mock_get_deck_id,
            mock_get_deck,
        ):
            self.client.force_authenticate(user=self.owner)

            response = self.client.patch(
                f"/api/decks/{self.deck.id}/update/",
                {
                    "name": "Nuevo nombre",
                },
                format="json",
            )

            self.assertEqual(response.status_code, 200)

            self.deck.refresh_from_db()

            self.assertEqual(
                self.deck.name,
                "Nuevo nombre",
            )

            mock_get_deck_id.assert_not_called()
            mock_get_deck.assert_not_called()

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
        self.assertEqual(
            self.deck.name,
            "Mazo original",
        )

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
        self.assertEqual(
            self.deck.name,
            "Mazo actualizado",
        )
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


class DeckCheckServiceTest(TestCase):

    @patch("decks.services.requests.get")
    def test_get_deck_by_id(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "id": "deck-123",
            "name": "Mazo de prueba",
        }

        result = DeckCheckService.get_deck(deck_id="deck-123")

        self.assertEqual(
            result,
            {
                "id": "deck-123",
                "name": "Mazo de prueba",
            },
        )

        mock_get.assert_called_once_with(
            "https://deckcheck.co/api/external/deck",
            params={"deck_id": "deck-123"},
            timeout=10,
        )

    def test_get_deck_requires_id_or_url(self):
        with self.assertRaises(ValueError):
            DeckCheckService.get_deck()

    @patch("decks.services.requests.get")
    def test_get_deck_by_url(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "id": "deck-456",
            "name": "Mazo desde URL",
        }

        result = DeckCheckService.get_deck(
            deck_url="https://deckcheck.co/decks/deck-456"
        )

        self.assertEqual(
            result,
            {
                "id": "deck-456",
                "name": "Mazo desde URL",
            },
        )

        mock_get.assert_called_once_with(
            "https://deckcheck.co/api/external/deck",
            params={
                "deck_url": "https://deckcheck.co/decks/deck-456"
            },
            timeout=10,
        )

    @patch("decks.services.requests.get")
    def test_get_deck_raises_http_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "DeckCheck error"
        )

        with self.assertRaises(requests.HTTPError):
            DeckCheckService.get_deck(deck_id="deck-error")

        mock_get.assert_called_once_with(
            "https://deckcheck.co/api/external/deck",
            params={"deck_id": "deck-error"},
            timeout=10,
        )

    @patch("decks.services.requests.get")
    def test_get_deck_propagates_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout(
            "DeckCheck timeout"
        )

        with self.assertRaises(requests.Timeout):
            DeckCheckService.get_deck(deck_id="deck-timeout")

        mock_get.assert_called_once_with(
            "https://deckcheck.co/api/external/deck",
            params={"deck_id": "deck-timeout"},
            timeout=10,
        )

    @patch("decks.services.requests.get")
    def test_get_deck_propagates_connection_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError(
            "No se pudo conectar con DeckCheck"
        )

        with self.assertRaises(requests.ConnectionError):
            DeckCheckService.get_deck(
                deck_id="deck-connection-error"
            )

        mock_get.assert_called_once_with(
            "https://deckcheck.co/api/external/deck",
            params={"deck_id": "deck-connection-error"},
            timeout=10,
        )

    @patch("decks.services.requests.get")
    def test_get_deck_id_from_url(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "id": "deck-789",
            "name": "Mazo identificado",
        }

        result = DeckCheckService.get_deck_id_from_url(
            "https://deckcheck.co/decks/deck-789"
        )

        self.assertEqual(result, "deck-789")

        mock_get.assert_called_once_with(
            "https://deckcheck.co/api/external/deck",
            params={
                "deck_url": "https://deckcheck.co/decks/deck-789"
            },
            timeout=10,
        )
    def test_save_analysis_creates_analysis(self):
        deck = Deck.objects.create(
            owner=Player.objects.create_user(
            username="analysis_test",
            password="testpass123",
            display_name="Analysis Test",
            ),
            name="Mazo de prueba",
            commander="Comandante de prueba",
        )

        data = {
            "id": "test123",
            "bracket": 3,
            "name": "Mazo de prueba",
            "format": "commander",
        }

        analysis = DeckCheckService.save_analysis(deck, data)

        self.assertEqual(analysis.deck, deck)
        self.assertEqual(analysis.bracket, "3")
        self.assertEqual(analysis.raw_data, data)
        self.assertEqual(analysis.win_conditions, 0)
        self.assertEqual(analysis.game_changers, 0)
        self.assertIsNone(analysis.crispi_score)
