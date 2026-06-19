import feedparser
import re
from datetime import datetime, timezone
from dateutil import parser as dateparser

FEED_URL = "https://9to5toys.com/feed/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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


def fetch():
    deals = []
    try:
        feed = feedparser.parse(FEED_URL, request_headers=HEADERS)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")

            try:
                posted_at = dateparser.parse(entry.get("published", "")).astimezone(timezone.utc).isoformat()
            except Exception:
                posted_at = datetime.now(timezone.utc).isoformat()

            combined = f"{title} {summary}"
            price = _parse_price(title) or _parse_price(summary)
            discount_hint = _parse_discount(combined)

            deals.append({
                "title": title,
                "url": link,
                "price": price,
                "original_price": None,
                "discount_hint_pct": discount_hint,
                "source": "9to5toys",
                "votes": 0,
                "posted_at": posted_at,
                "image_url": None,
                "category": "electronics",
            })
        print(f"[9to5toys] {len(deals)} deals")
    except Exception as e:
        print(f"[9to5toys] failed: {e}")
    return deals
