"""
Analyze flight price history vs oil price to generate a buy/wait signal
and surface insights (best month to fly, best month to book).
"""

import json
import os
from datetime import datetime, timezone

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "history.json")


def load_history():
    try:
        with open(HISTORY_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def _price_trend(entries, cabin, month, days=30):
    """Return (current_price, avg_price, trend_pct) for a cabin+month combo."""
    relevant = [
        e for e in entries
        if e.get("cabin") == cabin and e.get("month") == month and e.get("price")
    ]
    if not relevant:
        return None, None, None
    relevant.sort(key=lambda x: x.get("date", ""))
    recent = relevant[-days:]
    if not recent:
        return None, None, None
    current = recent[-1]["price"]
    avg = sum(r["price"] for r in recent) / len(recent)
    if len(recent) >= 2:
        earliest = recent[0]["price"]
        trend = (current - earliest) / earliest * 100
    else:
        trend = 0
    return current, round(avg, 0), round(trend, 1)


def analyze(flights_today, oil, sentiment):
    now = datetime.now(timezone.utc).isoformat()
    history = load_history()

    # Build today's snapshot entries for history append
    today_str = now[:10]
    oil_price = oil.get("current_price")

    snapshot_entries = []
    for f in flights_today:
        snapshot_entries.append({
            "date": today_str,
            "origin": f["origin"],
            "dest": f["dest"],
            "cabin": f["cabin"],
            "month": f["month"],
            "price": f["price"],
            "airline": f["airline"],
            "oil_price": oil_price,
        })

    # Append today (deduplicate by date)
    existing_dates = {(e["date"], e["origin"], e["dest"], e["cabin"], e["month"]) for e in history}
    for entry in snapshot_entries:
        key = (entry["date"], entry["origin"], entry["dest"], entry["cabin"], entry["month"])
        if key not in existing_dates:
            history.append(entry)

    # --- Generate signals ---
    signals = {}
    for cabin in ("business", "premium_economy"):
        for month in ("june", "july"):
            cur, avg, trend = _price_trend(history, cabin, month)
            if cur is None:
                continue
            vs_avg = round((cur - avg) / avg * 100, 1) if avg else 0
            signals[f"{cabin}_{month}"] = {
                "current_price": cur,
                "avg_30d": avg,
                "trend_30d_pct": trend,
                "vs_avg_pct": vs_avg,
            }

    # --- Buy/Wait recommendation ---
    oil_month_chg = oil.get("month_change_pct", 0) or 0
    oil_week_chg = oil.get("week_change_pct", 0) or 0
    sentiment_signal = sentiment.get("signal", "neutral")

    # Score factors: negative = lean BUY, positive = lean WAIT
    score = 0

    # Oil trending up → airlines will raise surcharges → buy soon
    if oil_month_chg > 5:
        score += 2
    elif oil_month_chg > 2:
        score += 1
    elif oil_month_chg < -5:
        score -= 2
    elif oil_month_chg < -2:
        score -= 1

    if sentiment_signal == "bullish_oil":
        score += 1
    elif sentiment_signal == "bearish_oil":
        score -= 1

    # Price vs 30-day average
    primary = signals.get("business_june") or signals.get("business_july")
    if primary:
        if primary["vs_avg_pct"] < -5:
            score -= 2  # price is below average → good time to buy
        elif primary["vs_avg_pct"] > 5:
            score += 1  # price above average → might want to wait

    if score >= 2:
        recommendation = "buy_now"
        reason = "Oil prices are rising and/or flight prices are near recent lows. Lock in now before surcharges increase."
    elif score <= -2:
        recommendation = "wait"
        reason = "Oil prices are falling. Flight prices may follow. Consider waiting 2-4 weeks."
    else:
        recommendation = "neutral"
        reason = "No strong signal either way. Monitor daily and buy if prices drop below your target."

    # Best month comparison
    biz_june = signals.get("business_june", {}).get("current_price")
    biz_july = signals.get("business_july", {}).get("current_price")
    if biz_june and biz_july:
        best_month = "june" if biz_june <= biz_july else "july"
        month_savings = abs((biz_june or 0) - (biz_july or 0))
    else:
        best_month = "june" if biz_june else "july"
        month_savings = 0

    result = {
        "generated_at": now,
        "recommendation": recommendation,
        "recommendation_score": score,
        "reason": reason,
        "best_month": best_month,
        "month_savings": round(month_savings, 0),
        "oil_month_change_pct": oil_month_chg,
        "oil_week_change_pct": oil_week_chg,
        "sentiment_signal": sentiment_signal,
        "signals": signals,
        "days_of_history": len(set(e["date"] for e in history)),
    }
    return result, history
