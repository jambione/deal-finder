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


def _walmart():
    api_key = os.environ.get("WALMART_API_KEY")
    if not api_key:
        print("[walmart] skipping — WALMART_API_KEY not set")
        return []

    # Walmart Affiliate API (Open API)
    # https://developer.walmart.com/home/us-mp/
    now = datetime.now(timezone.utc).isoformat()
    deals = []
    try:
        resp = requests.get(
            "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/trending",
            headers={"WM_SEC.KEY_VERSION": "1", "WM_CONSUMER.ID": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        for item in resp.json().get("items", []):
            deals.append({
                "title": item.get("name", ""),
                "url": item.get("productUrl", ""),
                "price": item.get("salePrice"),
                "original_price": item.get("msrp") or item.get("price"),
                "source": "walmart",
                "votes": 0,
                "posted_at": now,
                "image_url": item.get("thumbnailImage"),
            })
    except Exception as e:
        print(f"[walmart] error: {e}")
    return deals


def _newegg():
    api_key = os.environ.get("NEWEGG_API_KEY")
    if not api_key:
        print("[newegg] skipping — NEWEGG_API_KEY not set")
        return []

    # Newegg Marketplace API
    # https://developer.newegg.com/
    now = datetime.now(timezone.utc).isoformat()
    deals = []
    try:
        resp = requests.get(
            "https://api.newegg.com/marketplace/seller/v2/item/search",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            params={"PageSize": 20, "SortType": "PriceAscending"},
            timeout=10,
        )
        resp.raise_for_status()
        for item in resp.json().get("NeweggItem", {}).get("ItemList", []):
            deals.append({
                "title": item.get("Description", ""),
                "url": f"https://www.newegg.com/p/{item.get('NeweggItemNumber', '')}",
                "price": item.get("UnitPrice"),
                "original_price": item.get("OriginalPrice"),
                "source": "newegg",
                "votes": 0,
                "posted_at": now,
                "image_url": None,
            })
    except Exception as e:
        print(f"[newegg] error: {e}")
    return deals


def fetch():
    return _bestbuy() + _walmart() + _newegg()
