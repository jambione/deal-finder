import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from sources import slickdeals, reddit, amazon, retailers, flights, games, software
from scorer import score_deals
from categorizer import assign_categories
from matcher import match_searches
from suggester import get_suggestions

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")


def load_searches():
    path = os.path.join(CONFIG_DIR, "searches.json")
    with open(path) as f:
        return json.load(f).get("searches", [])


def compute_discount(deal):
    price = deal.get("price")
    original = deal.get("original_price")
    hint = deal.get("discount_hint_pct")
    if price and original and original > price:
        return round((original - price) / original * 100, 1)
    if hint:
        return hint
    return 0


def write_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"[output] wrote {path}")


def main():
    now = datetime.now(timezone.utc).isoformat()
    print(f"[main] starting run at {now}")

    raw = []
    for source_module in [slickdeals, reddit, amazon, retailers, flights, games, software]:
        try:
            fetched = source_module.fetch()
            print(f"[main] {source_module.__name__.split('.')[-1]}: {len(fetched)} deals")
            raw.extend(fetched)
        except Exception as e:
            print(f"[main] error in {source_module.__name__}: {e}")

    for deal in raw:
        deal["discount_pct"] = compute_discount(deal)

    categorized = assign_categories(raw)

    all_deals = []
    for cat_deals in categorized.values():
        all_deals.extend(cat_deals)

    scored = score_deals(all_deals)

    scored_by_url = {d["url"]: d for d in scored if d.get("url")}
    for deal in all_deals:
        if deal.get("url") in scored_by_url:
            deal["score"] = scored_by_url[deal["url"]]["score"]

    searches = load_searches()
    search_results = match_searches(all_deals, searches)
    suggestions = get_suggestions(scored, search_results)

    for cat in ["electronics", "apparel", "travel", "games", "software"]:
        cat_deals = [d for d in scored if d.get("category") == cat]
        write_json(f"{cat}.json", {
            "category": cat,
            "generated_at": now,
            "deals": cat_deals,
        })

    write_json("searches.json", {
        "generated_at": now,
        "results": search_results,
    })

    write_json("suggestions.json", {
        "generated_at": now,
        "suggestion_threshold": 75,
        "suggestions": suggestions,
    })

    total = sum(len(r["matches"]) for r in search_results)
    print(f"[main] done — {len(scored)} deals scored, {total} search matches, {len(suggestions)} suggestions")


if __name__ == "__main__":
    main()
