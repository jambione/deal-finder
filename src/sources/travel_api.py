import os
import requests
from datetime import datetime, timezone

# Amadeus Self-Service API (free test tier).
# Get keys at https://developers.amadeus.com — set AMADEUS_API_KEY + AMADEUS_API_SECRET.
# Uses the Flight Inspiration Search ("cheapest destinations from an origin") +
# Hotel offers, both of which return real structured pricing.

AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_DEST_URL = "https://test.api.amadeus.com/v1/shopping/flight-destinations"

# Origins to scan for cheap-flight inspiration
ORIGINS = ["JFK", "LAX", "ORD"]


def _get_token(key, secret):
    resp = requests.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": key,
            "client_secret": secret,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch():
    key = os.environ.get("AMADEUS_API_KEY")
    secret = os.environ.get("AMADEUS_API_SECRET")
    if not key or not secret:
        print("[amadeus] skipping — AMADEUS_API_KEY / AMADEUS_API_SECRET not set")
        return []

    now = datetime.now(timezone.utc).isoformat()
    deals = []
    try:
        token = _get_token(key, secret)
        headers = {"Authorization": f"Bearer {token}"}

        for origin in ORIGINS:
            try:
                resp = requests.get(
                    FLIGHT_DEST_URL,
                    headers=headers,
                    params={"origin": origin, "oneWay": "false"},
                    timeout=15,
                )
                resp.raise_for_status()
                for offer in resp.json().get("data", []):
                    dest = offer.get("destination", "")
                    price = offer.get("price", {}).get("total")
                    depart = offer.get("departureDate", "")
                    link = offer.get("links", {}).get("flightOffers", "")
                    deals.append({
                        "title": f"Flight {origin} → {dest} roundtrip from ${price} (depart {depart})",
                        "url": link or "https://www.amadeus.com",
                        "price": float(price) if price else None,
                        "original_price": None,
                        "source": "amadeus",
                        "votes": 0,
                        "posted_at": now,
                        "image_url": None,
                        "category": "travel",
                    })
            except Exception as e:
                print(f"[amadeus] error for origin {origin}: {e}")

        print(f"[amadeus] {len(deals)} flight deals")
    except Exception as e:
        print(f"[amadeus] failed: {e}")
    return deals
