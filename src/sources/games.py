import requests
import feedparser
from datetime import datetime, timezone
from dateutil import parser as dateparser

CHEAPSHARK_URL = "https://www.cheapshark.com/api/1.0/deals"
REDDIT_GAMEDEALS_RSS = "https://www.reddit.com/r/gamedeals/hot.rss?limit=50"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _cheapshark():
    deals = []
    now = datetime.now(timezone.utc).isoformat()
    try:
        resp = requests.get(
            CHEAPSHARK_URL,
            params={
                "pageSize": 60,
                "sortBy": "Deal Rating",
                "onSale": 1,
                "lowerPrice": 0,
            },
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        for item in resp.json():
            sale_price = float(item.get("salePrice", 0))
            normal_price = float(item.get("normalPrice", 0))
            savings_pct = float(item.get("savings", 0))
            metacritic = int(item.get("metacriticScore", 0))
            deal_id = item.get("dealID", "")

            deals.append({
                "title": item.get("title", ""),
                "url": f"https://www.cheapshark.com/redirect?dealID={deal_id}",
                "price": sale_price,
                "original_price": normal_price if normal_price > sale_price else None,
                "discount_pct": round(savings_pct, 1),
                "source": "cheapshark",
                "votes": metacritic,
                "posted_at": now,
                "image_url": item.get("thumb"),
                "category": "games",
            })
    except Exception as e:
        print(f"[games] CheapShark error: {e}")
    print(f"[games] cheapshark: {len(deals)} deals")
    return deals


def _reddit_gamedeals():
    deals = []
    try:
        feed = feedparser.parse(REDDIT_GAMEDEALS_RSS, request_headers=HEADERS)
        for entry in feed.entries:
            title = entry.get("title", "")
            url = entry.get("link", "")
            try:
                posted_at = dateparser.parse(entry.get("published", "")).astimezone(timezone.utc).isoformat()
            except Exception:
                posted_at = datetime.now(timezone.utc).isoformat()
            deals.append({
                "title": title,
                "url": url,
                "price": None,
                "original_price": None,
                "source": "reddit/r/gamedeals",
                "votes": 0,
                "posted_at": posted_at,
                "image_url": None,
                "category": "games",
            })
        print(f"[games] r/gamedeals: {len(feed.entries)} posts")
    except Exception as e:
        print(f"[games] r/gamedeals error: {e}")
    return deals


def fetch():
    return _cheapshark() + _reddit_gamedeals()
