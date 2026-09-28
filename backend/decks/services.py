import requests
from urllib.parse import urlparse
from django.core.exceptions import ValidationError

from .models import DeckAnalysis


class DeckCheckService:
    BASE_URL = "https://deckcheck.co/api/external"

    @classmethod
    def get_deck(cls, deck_id=None, deck_url=None):
        params = {}

        if deck_id:
            params["deck_id"] = deck_id
        elif deck_url:
            params["deck_url"] = deck_url
        else:
            raise ValueError("Se necesita deck_id o deck_url.")

        response = requests.get(
            f"{cls.BASE_URL}/deck",
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    @classmethod
    def get_deck_id_from_url(cls, deck_url):
        data = cls.get_deck(deck_url=deck_url)
        return data.get("id")

    @classmethod
    def save_analysis(cls, deck, data):
        dti = data.get("dti") or {}
        analysis, _ = DeckAnalysis.objects.update_or_create(
            deck=deck,
            defaults={
                "bracket": str(data.get("bracket") or dti.get("bracket") or ""),
                "win_conditions": int(data.get("winConditions") or data.get("win_conditions") or 0),
                "game_changers": int(data.get("gameChangers") or data.get("game_changers") or 0),
                "crispi_score": data.get("threatIndex") or dti.get("score"),
                "raw_data": data,
            },
        )

        return analysis
    
    @classmethod
    def analyze_deck(cls, deck):
        data = None
        if deck.deck_url:
            parsed = urlparse(deck.deck_url)
            if parsed.netloc.lower() in {"deckcheck.co", "www.deckcheck.co"}:
                try:
                    # Consultar por URL evita confundir el id local de Liga Timidina con el id público de DeckCheck.
                    data = cls.get_deck(deck_url=deck.deck_url)
                except requests.RequestException as exc:
                    status = getattr(getattr(exc, "response", None), "status_code", None)
                    if status == 400:
                        raise ValidationError("DeckCheck no reconoce esa URL pública. Comprueba que sea una URL /app/decklist/, /app/builder/ o /app/deckview/ compartible.") from exc
                    raise ValidationError("No se ha podido consultar DeckCheck en este momento.") from exc
            elif not deck.deckcheck_id:
                # deck_url puede ser un enlace informativo no perteneciente a DeckCheck.
                return None

        if data is None and deck.deckcheck_id:
            try:
                data = cls.get_deck(deck_id=deck.deckcheck_id)
            except requests.RequestException as exc:
                raise ValidationError("No se ha podido consultar DeckCheck en este momento.") from exc

        if data is None:
            return None

        external_id = data.get("publicId") or data.get("id") or deck.deckcheck_id or ""
        public_url = data.get("publicUrl")
        update_fields = []
        if str(external_id) != deck.deckcheck_id:
            deck.deckcheck_id = str(external_id)
            update_fields.append("deckcheck_id")
        if public_url:
            normalized_url = public_url if public_url.startswith("http") else f"https://deckcheck.co{public_url}"
            if normalized_url != deck.deck_url:
                deck.deck_url = normalized_url
                update_fields.append("deck_url")
        if update_fields:
            deck.save(update_fields=update_fields)
        return cls.save_analysis(deck, data)
