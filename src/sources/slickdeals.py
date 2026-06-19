import feedparser
import re
from datetime import datetime, timezone
from dateutil import parser as dateparser

FEED_URL = "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&pp=40&rss=1"


def _parse_price(text):
    if not text:
        return None
    m = re.search(r"\$([0-9,]+(?:\.[0-9]{1,2})?)", text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _parse_original_price(text):
    patterns = [
        r"(?:was|reg(?:ular)?|retail|orig(?:inal)?|msrp)[:\s]*\$([0-9,]+(?:\.[0-9]{1,2})?)",
        r"\$([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:->|→|to)\s*\$",
    ]
    if not text:
        return None
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", ""))
    return None


def fetch():
    feed = feedparser.parse(FEED_URL)
    deals = []
    for entry in feed.entries:
        title = entry.get("title", "")
        url = entry.get("link", "")
        summary = entry.get("summary", "")
        combined = f"{title} {summary}"

        price = _parse_price(title) or _parse_price(summary)
        original_price = _parse_original_price(combined)

        try:
            posted_at = dateparser.parse(entry.get("published", "")).astimezone(timezone.utc).isoformat()
        except Exception:
            posted_at = datetime.now(timezone.utc).isoformat()

        deals.append({
            "title": title,
            "url": url,
            "price": price,
            "original_price": original_price,
            "source": "slickdeals",
            "votes": 0,
            "posted_at": posted_at,
            "image_url": None,
        })
    return deals
