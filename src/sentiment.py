"""
Oil & aviation sentiment from RSS headlines.
Scores -1.0 (very bearish on oil = good for flights) to +1.0 (bullish on oil = bad for flights).
"""

import feedparser
from datetime import datetime, timezone

FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.ft.com/rss/home/uk",  # FT has energy coverage
    "https://feeds.bloomberg.com/markets/news.rss",
]

OIL_BULLISH = [
    "oil rises", "crude rises", "oil gains", "opec cuts", "supply cut", "output cut",
    "oil surges", "crude surges", "oil rally", "jet fuel", "aviation fuel rises",
    "oil price up", "wti rises", "brent rises",
]
OIL_BEARISH = [
    "oil falls", "crude falls", "oil drops", "oil slides", "opec increases",
    "supply glut", "oil slump", "crude slump", "oil tumbles", "oversupply",
    "oil price down", "wti falls", "brent falls", "recession fears",
]
AVIATION_POSITIVE = [
    "airfare drops", "flight prices fall", "cheap flights", "airline sale",
    "airfare deals", "flight deals", "ticket prices fall",
]
AVIATION_NEGATIVE = [
    "airfare rises", "flight prices rise", "airfare surge", "airline fuel surcharge",
    "ticket prices rise", "flight costs rise",
]


def _score_headline(text):
    t = text.lower()
    score = 0
    for phrase in OIL_BULLISH:
        if phrase in t:
            score += 1
    for phrase in OIL_BEARISH:
        if phrase in t:
            score -= 1
    for phrase in AVIATION_NEGATIVE:
        if phrase in t:
            score += 0.5
    for phrase in AVIATION_POSITIVE:
        if phrase in t:
            score -= 0.5
    return score


def fetch():
    now = datetime.now(timezone.utc).isoformat()
    headlines = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                if title:
                    headlines.append(title)
        except Exception:
            continue

    if not headlines:
        print("[sentiment] no headlines fetched")
        return {"fetched_at": now, "score": 0, "signal": "neutral", "headline_count": 0, "top_headlines": []}

    scored = [(h, _score_headline(h)) for h in headlines]
    scored.sort(key=lambda x: abs(x[1]), reverse=True)
    total = sum(s for _, s in scored)
    normalized = max(-1.0, min(1.0, total / max(len(scored), 1)))

    if normalized > 0.2:
        signal = "bullish_oil"   # oil prices rising → flights likely to rise → buy soon
    elif normalized < -0.2:
        signal = "bearish_oil"   # oil prices falling → flights may drop → can wait
    else:
        signal = "neutral"

    top = [{"headline": h, "score": s} for h, s in scored[:5] if s != 0]

    print(f"[sentiment] {len(headlines)} headlines, score={normalized:.2f}, signal={signal}")
    return {
        "fetched_at": now,
        "score": round(normalized, 3),
        "signal": signal,
        "headline_count": len(headlines),
        "top_headlines": top,
    }
