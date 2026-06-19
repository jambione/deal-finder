import feedparser
import re
from datetime import datetime, timezone
from dateutil import parser as dateparser

FEEDS = [
    ("https://www.theflightdeal.com/feed/", "theflightdeal"),
    ("https://www.secretflying.com/feed/", "secretflying"),
    ("https://www.airfarewatchdog.com/blog/feed/", "airfarewatchdog"),
    ("https://www.travelzoo.com/rss/", "travelzoo"),
    ("https://www.travelpirates.com/feed", "travelpirates"),
    ("https://thepointsguy.com/feed/", "thepointsguy"),
    ("https://www.reddit.com/r/TravelDeals/hot.rss?limit=50", "r/traveldeals"),
    ("https://www.reddit.com/r/flightdeals/hot.rss?limit=50", "r/flightdeals"),
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


def _parse_roundtrip(title):
    m = re.search(r"\$(\d+(?:,\d+)?)\s*(?:round\s*trip|r/?t\b)", title, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def fetch():
    deals = []
    for url, source_name in FEEDS:
        try:
            feed = feedparser.parse(url, request_headers=HEADERS)
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                try:
                    posted_at = dateparser.parse(entry.get("published", "")).astimezone(timezone.utc).isoformat()
                except Exception:
                    posted_at = datetime.now(timezone.utc).isoformat()

                price = _parse_roundtrip(title) or _parse_price(title) or _parse_price(summary)

                deals.append({
                    "title": title,
                    "url": link,
                    "price": price,
                    "original_price": None,
                    "source": source_name,
                    "votes": 0,
                    "posted_at": posted_at,
                    "image_url": None,
                    "category": "travel",
                })
            print(f"[flights] {source_name}: {len(feed.entries)} deals")
        except Exception as e:
            print(f"[flights] failed {source_name}: {e}")
    return deals
