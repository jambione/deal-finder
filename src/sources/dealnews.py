import feedparser
import re
from datetime import datetime, timezone
from dateutil import parser as dateparser

FEEDS = [
    ("https://www.dealnews.com/rss/", "dealnews", None),
    ("https://www.dealnews.com/c196/Electronics/?rss=1", "dealnews", "electronics"),
    ("https://www.dealnews.com/c760/Clothing-Apparel/?rss=1", "dealnews", "apparel"),
    ("https://www.dealnews.com/c204/Travel/?rss=1", "dealnews", "travel"),
    ("https://www.dealnews.com/c399/Video-Games/?rss=1", "dealnews", "games"),
    ("https://www.dealnews.com/c116/Software/?rss=1", "dealnews", "software"),
]

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
    seen = set()
    deals = []
    for url, source_name, forced_category in FEEDS:
        try:
            feed = feedparser.parse(url, request_headers=HEADERS)
            count = 0
            for entry in feed.entries:
                link = entry.get("link", "")
                if link in seen:
                    continue
                seen.add(link)

                title = entry.get("title", "")
                summary = entry.get("summary", "")
                try:
                    posted_at = dateparser.parse(entry.get("published", "")).astimezone(timezone.utc).isoformat()
                except Exception:
                    posted_at = datetime.now(timezone.utc).isoformat()

                combined = f"{title} {summary}"
                price = _parse_price(title) or _parse_price(summary)
                discount_hint = _parse_discount(combined)

                deal = {
                    "title": title,
                    "url": link,
                    "price": price,
                    "original_price": None,
                    "discount_hint_pct": discount_hint,
                    "source": source_name,
                    "votes": 0,
                    "posted_at": posted_at,
                    "image_url": None,
                }
                if forced_category:
                    deal["category"] = forced_category
                deals.append(deal)
                count += 1
            print(f"[dealnews] {url.split('/')[-2] or 'frontpage'}: {count} deals")
        except Exception as e:
            print(f"[dealnews] failed {url}: {e}")
    return deals
