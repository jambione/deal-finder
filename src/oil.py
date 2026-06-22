"""
Fetch WTI crude oil spot price from EIA (free, no key required for DEMO_KEY).
Also pulls 52 weeks of history for trend analysis.
"""

import requests
from datetime import datetime, timezone

EIA_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"


def fetch():
    now = datetime.now(timezone.utc).isoformat()
    params = {
        "api_key": "DEMO_KEY",
        "frequency": "weekly",
        "data[0]": "value",
        "facets[product][]": "EPCWTI",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 52,
    }
    try:
        resp = requests.get(EIA_URL, params=params, timeout=15)
        resp.raise_for_status()
        rows = resp.json().get("response", {}).get("data", [])
        if not rows:
            print("[oil] no data returned")
            return {}

        history = [{"date": r["period"], "price": float(r["value"])} for r in rows if r.get("value")]
        history.sort(key=lambda x: x["date"])

        current = history[-1]["price"] if history else None
        week_ago = history[-2]["price"] if len(history) >= 2 else None
        month_ago = history[-5]["price"] if len(history) >= 5 else None
        year_ago = history[0]["price"] if history else None

        week_chg = round((current - week_ago) / week_ago * 100, 2) if week_ago else None
        month_chg = round((current - month_ago) / month_ago * 100, 2) if month_ago else None
        year_chg = round((current - year_ago) / year_ago * 100, 2) if year_ago else None

        result = {
            "fetched_at": now,
            "current_price": current,
            "week_change_pct": week_chg,
            "month_change_pct": month_chg,
            "year_change_pct": year_chg,
            "history": history[-52:],
        }
        print(f"[oil] WTI ${current}/bbl  week:{week_chg:+.1f}%  month:{month_chg:+.1f}%")
        return result
    except Exception as e:
        print(f"[oil] failed: {e}")
        return {}
