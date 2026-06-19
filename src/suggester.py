from scorer import why_text

THRESHOLD = 75
WATCHED_CATEGORIES = {"electronics", "apparel", "travel"}
MAX_SUGGESTIONS = 20


def get_suggestions(deals, search_results):
    matched_urls = set()
    for result in search_results:
        for deal in result.get("matches", []):
            matched_urls.add(deal.get("url", ""))

    suggestions = []
    for deal in deals:
        if deal.get("url") in matched_urls:
            continue
        if deal.get("category") not in WATCHED_CATEGORIES:
            continue
        if (deal.get("score") or 0) < THRESHOLD:
            continue
        suggestions.append({**deal, "why": why_text(deal)})

    return suggestions[:MAX_SUGGESTIONS]
