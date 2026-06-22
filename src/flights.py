"""
Fetch flight prices via SerpAPI Google Flights.

Routes monitored:
  JFK → MXP (Milan Malpensa)
  JFK → LIN (Milan Linate)
  EWR → MXP

Cabin classes: Business (3), Premium Economy (2)
Travel window:  June & July 2027, 12-night trips
"""

import os
import requests
from datetime import datetime, timezone

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
BASE_URL = "https://serpapi.com/search"

# (origin, destination, label)
ROUTES = [
    ("JFK", "MXP", "JFK → Milan Malpensa"),
    ("JFK", "LIN", "JFK → Milan Linate"),
    ("EWR", "MXP", "EWR → Milan Malpensa"),
]

# Representative Saturday departures, 12-night trips (return on Thursday)
JUNE_DATES = [("2027-06-07", "2027-06-19"), ("2027-06-14", "2027-06-26"), ("2027-06-21", "2027-07-03")]
JULY_DATES = [("2027-07-06", "2027-07-18"), ("2027-07-13", "2027-07-25"), ("2027-07-20", "2027-08-01")]

CABINS = [
    (3, "business"),
    (2, "premium_economy"),
]


def _search(origin, dest, outbound, ret, cabin_code):
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": dest,
        "outbound_date": outbound,
        "return_date": ret,
        "travel_class": cabin_code,
        "type": "1",  # round trip
        "adults": "1",
        "currency": "USD",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _best_price(data):
    """Return (price, airline, duration_min) for the cheapest option."""
    best = None
    for key in ("best_flights", "other_flights"):
        for flight in data.get(key, []):
            price = flight.get("price")
            if price and (best is None or price < best[0]):
                legs = flight.get("flights", [{}])
                airline = legs[0].get("airline", "")
                total_dur = flight.get("total_duration", 0)
                best = (price, airline, total_dur)
    return best


def fetch():
    if not SERPAPI_KEY:
        print("[flights] skipping — SERPAPI_KEY not set")
        return []

    now = datetime.now(timezone.utc).isoformat()
    results = []

    for origin, dest, route_label in ROUTES:
        for month_label, date_pairs in [("june", JUNE_DATES), ("july", JULY_DATES)]:
            cabin_bests = {}  # cabin -> (price, airline, dur, outbound, ret)
            for outbound, ret in date_pairs:
                for cabin_code, cabin_label in CABINS:
                    try:
                        data = _search(origin, dest, outbound, ret, cabin_code)
                        hit = _best_price(data)
                        if hit:
                            price, airline, dur = hit
                            prev = cabin_bests.get(cabin_label)
                            if prev is None or price < prev[0]:
                                cabin_bests[cabin_label] = (price, airline, dur, outbound, ret)
                        # price_insights from SerpAPI
                        insights = data.get("price_insights", {})
                        typical_low = insights.get("typical_price_range", [None, None])[0]
                        typical_high = insights.get("typical_price_range", [None, None])[1]
                    except Exception as e:
                        print(f"[flights] error {origin}->{dest} {outbound} {cabin_label}: {e}")

            for cabin_label, (price, airline, dur, outbound, ret) in cabin_bests.items():
                results.append({
                    "origin": origin,
                    "dest": dest,
                    "route_label": route_label,
                    "cabin": cabin_label,
                    "month": month_label,
                    "price": price,
                    "airline": airline,
                    "duration_min": dur,
                    "outbound_date": outbound,
                    "return_date": ret,
                    "fetched_at": now,
                })

    print(f"[flights] {len(results)} price points fetched")
    return results
