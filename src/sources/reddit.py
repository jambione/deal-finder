import requests
import re
from datetime import datetime, timezone

SUBREDDITS = ["deals", "frugal", "buildapcsales"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}


def _parse_price(text):
    if not text:
        return None
    m = re.search(r"\$([0-9,]+(?:\.[0-9]{1,2})?)", text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _parse_discount(text):
    if not text:
        return None
    m = re.search(r"(\d+)\s*%\s*off", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def _fetch_rss(sub):
    import feedparser
    feed = feedparser.parse(
        f"https://www.reddit.com/r/{sub}/hot.rss?limit=50",
        request_headers=HEADERS,
    )
    deals = []
    for entry in feed.entries:
        title = entry.get("title", "")
        url = entry.get("link", "")
        summary = entry.get("summary", "")
        try:
            from dateutil import parser as dateparser
            posted_at = dateparser.parse(entry.get("published", "")).astimezone(timezone.utc).isoformat()
        except Exception:
            posted_at = datetime.now(timezone.utc).isoformat()
        price = _parse_price(title)
        discount_hint = _parse_discount(f"{title} {summary}")
        deals.append({
            "title": title,
            "url": url,
            "price": price,
            "original_price": None,
            "discount_hint_pct": discount_hint,
            "source": f"reddit/r/{sub}",
            "votes": 0,
            "posted_at": posted_at,
            "image_url": None,
        })
    return deals


def fetch():
    deals = []
    for sub in SUBREDDITS:
        try:
            fetched = _fetch_rss(sub)
            print(f"[reddit] r/{sub}: {len(fetched)} posts via RSS")
            deals.extend(fetched)
        except Exception as e:
            print(f"[reddit] failed r/{sub}: {e}")
    return deals
