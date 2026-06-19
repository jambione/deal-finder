def match_searches(deals, searches):
    results = []
    for search in searches:
        sid = search["id"]
        label = search["label"]
        category = search.get("category")
        keywords = [k.lower() for k in search.get("keywords", [])]
        max_price = search.get("max_price")
        min_discount = search.get("min_discount_pct", 0)

        matches = []
        for deal in deals:
            title = (deal.get("title") or "").lower()
            cat = deal.get("category")
            price = deal.get("price")
            discount = deal.get("discount_pct") or 0

            if category and cat != category:
                continue
            if not any(kw in title for kw in keywords):
                continue
            if max_price and price and price > max_price:
                continue
            if discount < min_discount:
                continue

            matches.append(deal)

        results.append({
            "search_id": sid,
            "label": label,
            "matches": matches,
        })

    return results
