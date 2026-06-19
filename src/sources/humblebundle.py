import feedparser
import requests
import re
from datetime import datetime, timezone
from dateutil import parser as dateparser

# Humble Bundle blog RSS announces new bundles with pricing context
BLOG_RSS = "https://blog.humblebundle.com/rss"
STORE_RSS = "https://www.humblebundle.com/store/deals?ajax=true"
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


def fetch():
    deals = []
    try:
        feed = feedparser.parse(BLOG_RSS, request_headers=HEADERS)
        for entry in feed.entries:
            title = entry.get("title", "")
            # Only include bundle/deal announcements
            if not any(kw in title.lower() for kw in ["bundle", "sale", "deal", "free"]):
                continue
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            try:
                posted_at = dateparser.parse(entry.get("published", "")).astimezone(timezone.utc).isoformat()
            except Exception:
                posted_at = datetime.now(timezone.utc).isoformat()

            price = _parse_price(title) or _parse_price(summary)
            # Humble bundles are pay-what-you-want; default to $1 minimum if no price found
            if price is None:
                price = 1.0

            bundle_title_lower = title.lower()
            if "software" in bundle_title_lower or "creative" in bundle_title_lower or "productivity" in bundle_title_lower:
                category = "software"
            else:
                category = "games"

            deals.append({
                "title": title,
                "url": link,
                "price": price,
                "original_price": None,
                "source": "humblebundle",
                "votes": 0,
                "posted_at": posted_at,
                "image_url": None,
                "category": category,
            })

        print(f"[humblebundle] {len(deals)} bundle announcements")
    except Exception as e:
        print(f"[humblebundle] failed: {e}")
    return deals
