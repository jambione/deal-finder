import feedparser
import re
from datetime import datetime, timezone
from dateutil import parser as dateparser

FEEDS = [
    ("https://www.bitsdujour.com/rss/deals", "bitsdujour"),
    ("https://www.reddit.com/r/softwaredeals/hot.rss?limit=50", "reddit/r/softwaredeals"),
    ("https://www.reddit.com/r/learnprogramming/hot.rss?limit=25", "reddit/r/learnprogramming"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SOFTWARE_KEYWORDS = [
    "software", "app", "license", "lifetime", "saas", "tool", "plugin",
    "subscription", "productivity", "vpn", "antivirus", "editor", "ide",
    "design", "video editor", "photo editor", "password manager",
]


def _is_software_deal(title):
    t = title.lower()
    return any(kw in t for kw in SOFTWARE_KEYWORDS)


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
    for url, source_name in FEEDS:
        try:
            feed = feedparser.parse(url, request_headers=HEADERS)
            count = 0
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")

                if "reddit" in source_name and not _is_software_deal(title):
                    continue

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
                    "source": source_name,
                    "votes": 0,
                    "posted_at": posted_at,
                    "image_url": None,
                    "category": "software",
                })
                count += 1
            print(f"[software] {source_name}: {count} deals")
        except Exception as e:
            print(f"[software] failed {source_name}: {e}")
    return deals
