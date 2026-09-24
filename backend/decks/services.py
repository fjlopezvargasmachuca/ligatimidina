import requests


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