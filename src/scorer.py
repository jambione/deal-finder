from datetime import datetime, timezone
from dateutil import parser as dateparser


def score_deals(deals):
    max_votes = max((d.get("votes") or 0 for d in deals), default=1) or 1

    scored = []
    for d in deals:
        discount_pct = d.get("discount_pct") or 0
        votes = d.get("votes") or 0
        posted_at = d.get("posted_at", "")

        normalized_votes = (votes / max_votes) * 100

        recency = 0
        try:
            posted = dateparser.parse(posted_at)
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - posted).total_seconds() / 3600
            if age_hours < 6:
                recency = 100
            elif age_hours < 24:
                recency = 50
        except Exception:
            pass

        score = round((discount_pct * 0.5) + (normalized_votes * 0.3) + (recency * 0.2), 1)
        scored.append({**d, "score": score})

    return sorted(scored, key=lambda x: x["score"], reverse=True)


def why_text(deal):
    parts = []
    disc = deal.get("discount_pct") or 0
    votes = deal.get("votes") or 0
    score = deal.get("score") or 0

    if disc >= 50:
        parts.append(f"{disc}% off — unusually high discount")
    elif disc >= 30:
        parts.append(f"{disc}% off")

    if votes >= 200:
        parts.append(f"{votes} community upvotes")
    elif votes >= 50:
        parts.append(f"{votes} upvotes")

    parts.append(f"score {score}")
    return " · ".join(parts)
