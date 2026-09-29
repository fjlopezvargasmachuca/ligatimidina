from decimal import Decimal, InvalidOperation

import requests
from django.core.exceptions import ValidationError
from django.utils import timezone


class CardMarketReferenceService:
    """Obtiene la referencia EUR publicada por Scryfall para Magic.

    Scryfall expone precio EUR y enlace de compra de Cardmarket por impresión.
    Es una referencia orientativa, no una cotización ni una transacción de la liga.
    """

    BASE_URL = "https://api.scryfall.com/cards/named"
    HEADERS = {
        "User-Agent": "LigaTimidina/1.0 (community binder; contact: league-admin)",
        "Accept": "application/json;q=0.9,*/*;q=0.8",
    }

    @classmethod
    def lookup(cls, card_name, foil=False):
        try:
            response = requests.get(
                cls.BASE_URL,
                params={"exact": card_name},
                headers=cls.HEADERS,
                timeout=8,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ValidationError("No se ha podido consultar la carta en este momento.") from exc

        data = response.json()
        image = (data.get("image_uris") or {}).get("normal")
        if not image:
            faces = data.get("card_faces") or []
            if faces:
                image = (faces[0].get("image_uris") or {}).get("normal")

        price_key = "eur_foil" if foil else "eur"
        raw_price = (data.get("prices") or {}).get(price_key)
        price = None
        if raw_price not in (None, ""):
            try:
                price = Decimal(str(raw_price)).quantize(Decimal("0.01"))
            except (InvalidOperation, ValueError):
                price = None

        return {
            "card_name": data.get("name") or card_name,
            "image_url": image or "",
            "market_url": (data.get("purchase_uris") or {}).get("cardmarket") or "",
            "reference_price_eur": price,
            "price_checked_at": timezone.now(),
        }
