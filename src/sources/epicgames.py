import requests
from datetime import datetime, timezone

API_URL = (
    "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    "?locale=en-US&country=US&allowCountries=US"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
STORE_BASE = "https://store.epicgames.com/en-US/p/"


def fetch():
    deals = []
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        elements = (
            data.get("data", {})
            .get("Catalog", {})
            .get("searchStore", {})
            .get("elements", [])
        )
        now = datetime.now(timezone.utc).isoformat()

        for elem in elements:
            promotions = elem.get("promotions") or {}
            promo_offers = promotions.get("promotionalOffers", [])
            if not promo_offers:
                continue  # only include items currently free/discounted

            title = elem.get("title", "")
            slug = elem.get("productSlug") or elem.get("urlSlug") or ""
            url = f"{STORE_BASE}{slug}" if slug else "https://store.epicgames.com/en-US/free-games"

            price_info = elem.get("price", {}).get("totalPrice", {})
            original_cents = price_info.get("originalPrice", 0)
            discount_cents = price_info.get("discountPrice", 0)
            original_price = original_cents / 100 if original_cents else None
            price = discount_cents / 100

            images = elem.get("keyImages", [])
            image_url = next(
                (img["url"] for img in images if img.get("type") == "Thumbnail"),
                None,
            )

            deals.append({
                "title": title,
                "url": url,
                "price": price,
                "original_price": original_price,
                "source": "epicgames",
                "votes": 0,
                "posted_at": now,
                "image_url": image_url,
                "category": "games",
            })

        print(f"[epicgames] {len(deals)} free/discounted games")
    except Exception as e:
        print(f"[epicgames] failed: {e}")
    return deals
