from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Binder, BinderCard


User = get_user_model()


class BinderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username="binder-owner", password="testpass123", display_name="Owner")
        self.other = User.objects.create_user(username="binder-other", password="testpass123", display_name="Other")
        self.binder = Binder.objects.create(owner=self.owner, title="Cambios", public=True)
        self.card = BinderCard.objects.create(
            binder=self.binder,
            card_name="Sol Ring",
            condition="NM",
            foil=False,
            quantity=1,
            image_url="https://cards.scryfall.io/example.jpg",
            market_url="https://www.cardmarket.com/en/Magic/Products/Search?searchString=Sol+Ring",
            reference_price_eur=Decimal("1.25"),
            price_checked_at=timezone.now(),
        )

    def test_authenticated_players_can_see_public_binders(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get("/api/binders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["owner_username"], "binder-owner")

    def test_other_player_cannot_edit_someone_elses_card(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(f"/api/binders/mine/cards/{self.card.id}/", {"quantity": 4}, format="json")
        self.assertEqual(response.status_code, 404)
        self.card.refresh_from_db()
        self.assertEqual(self.card.quantity, 1)

    @patch("binders.serializers.CardMarketReferenceService.lookup")
    def test_owner_can_add_card_with_external_reference_snapshot(self, lookup):
        lookup.return_value = {
            "card_name": "Lightning Bolt",
            "image_url": "https://cards.scryfall.io/bolt.jpg",
            "market_url": "https://www.cardmarket.com/en/Magic/Products/Search?searchString=Lightning+Bolt",
            "reference_price_eur": Decimal("0.45"),
            "price_checked_at": timezone.now(),
        }
        self.client.force_authenticate(user=self.owner)
        response = self.client.post("/api/binders/mine/cards/", {
            "card_name": "Lightning Bolt", "condition": "EX", "foil": False, "quantity": 2,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["card_name"], "Lightning Bolt")
        self.assertEqual(str(response.data["reference_price_eur"]), "0.45")

    @patch("binders.views.CardMarketReferenceService.lookup")
    def test_owner_can_refresh_price_reference(self, lookup):
        lookup.return_value = {
            "card_name": "Sol Ring",
            "image_url": self.card.image_url,
            "market_url": self.card.market_url,
            "reference_price_eur": Decimal("1.50"),
            "price_checked_at": timezone.now(),
        }
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f"/api/binders/mine/cards/{self.card.id}/refresh/")
        self.assertEqual(response.status_code, 200)
        self.card.refresh_from_db()
        self.assertEqual(self.card.reference_price_eur, Decimal("1.50"))

    def test_private_binder_is_hidden_from_other_players(self):
        self.binder.public = False
        self.binder.save(update_fields=["public"])
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(f"/api/binders/{self.binder.id}/").status_code, 404)

    @patch("binders.serializers.CardMarketReferenceService.lookup")
    def test_owner_cannot_exceed_one_hundred_card_entries(self, lookup):
        lookup.return_value = {
            "card_name": "Overflow Card",
            "image_url": "https://cards.scryfall.io/overflow.jpg",
            "market_url": "https://www.cardmarket.com/en/Magic/Products/Search?searchString=Overflow+Card",
            "reference_price_eur": Decimal("0.10"),
            "price_checked_at": timezone.now(),
        }
        BinderCard.objects.bulk_create([
            BinderCard(
                binder=self.binder, card_name=f"Card {index}", condition="NM",
                foil=False, quantity=1,
            )
            for index in range(2, 101)
        ])
        self.assertEqual(self.binder.cards.count(), 100)

        self.client.force_authenticate(user=self.owner)
        response = self.client.post("/api/binders/mine/cards/", {
            "card_name": "Overflow Card", "condition": "NM", "foil": False, "quantity": 1,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("límite de 100", response.data["detail"])
        self.assertEqual(self.binder.cards.count(), 100)
        lookup.assert_not_called()

    def test_owner_can_bulk_delete_selected_cards(self):
        second = BinderCard.objects.create(
            binder=self.binder, card_name="Arcane Signet", condition="NM", foil=False, quantity=1,
        )
        third = BinderCard.objects.create(
            binder=self.binder, card_name="Command Tower", condition="EX", foil=False, quantity=1,
        )
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            "/api/binders/mine/cards/bulk-delete/",
            {"ids": [self.card.id, second.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted"], 2)
        self.assertFalse(BinderCard.objects.filter(pk__in=[self.card.id, second.id]).exists())
        self.assertTrue(BinderCard.objects.filter(pk=third.id).exists())

    def test_bulk_delete_cannot_remove_another_players_card(self):
        other_binder = Binder.objects.create(owner=self.other, title="Otra carpeta", public=True)
        foreign_card = BinderCard.objects.create(
            binder=other_binder, card_name="Counterspell", condition="NM", foil=False, quantity=1,
        )
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            "/api/binders/mine/cards/bulk-delete/",
            {"ids": [self.card.id, foreign_card.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(BinderCard.objects.filter(pk=self.card.id).exists())
        self.assertTrue(BinderCard.objects.filter(pk=foreign_card.id).exists())


class ContactDeletePermissionTest(TestCase):
    def setUp(self):
        from accounts.models import ContactMessage
        self.client = APIClient()
        self.player = User.objects.create_user(username="contact-player", password="testpass123")
        self.admin = User.objects.create_user(username="contact-admin", password="testpass123", is_staff=True)
        self.message = ContactMessage.objects.create(sender=self.player, subject="Spam", message="Mensaje")

    def test_player_cannot_delete_support_conversation(self):
        self.client.force_authenticate(user=self.player)
        response = self.client.delete(f"/api/accounts/contact/{self.message.id}/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete_support_conversation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/accounts/contact/{self.message.id}/")
        self.assertEqual(response.status_code, 204)
