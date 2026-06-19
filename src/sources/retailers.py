import os
import requests
from datetime import datetime, timezone


def _bestbuy():
    api_key = os.environ.get("BESTBUY_API_KEY")
    if not api_key:
        print("[bestbuy] skipping — BESTBUY_API_KEY not set")
        return []

    now = datetime.now(timezone.utc).isoformat()
    deals = []
    searches = [
        ("laptop", "electronics"),
        ("tv 4k", "electronics"),
        ("headphones", "electronics"),
    ]

    for query, _ in searches:
        try:
            resp = requests.get(
                "https://api.bestbuy.com/v1/products",
                params={
                    "apiKey": api_key,
                    "format": "json",
                    "show": "name,url,salePrice,regularPrice,thumbnailImage",
                    "sort": "salePrice.asc",
                    "pageSize": 10,
                    "search": query,
                },
                timeout=10,
            )
            resp.raise_for_status()
            for p in resp.json().get("products", []):
                sale = p.get("salePrice")
                reg = p.get("regularPrice")
                deals.append({
                    "title": p.get("name", ""),
                    "url": p.get("url", ""),
                    "price": sale,
                    "original_price": reg if reg and reg != sale else None,
                    "source": "bestbuy",
                    "votes": 0,
                    "posted_at": now,
                    "image_url": p.get("thumbnailImage"),
                })
        except Exception as e:
            print(f"[bestbuy] error for '{query}': {e}")

    return deals


def fetch():
    return _bestbuy()
