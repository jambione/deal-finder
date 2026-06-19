KEYWORDS = {
    "electronics": [
        "laptop", "macbook", "dell xps", "lenovo", "thinkpad", "chromebook",
        "tv", "4k", "oled", "monitor", "gpu", "cpu", "processor", "ram", "ssd",
        "headphones", "earbuds", "airpods", "speaker", "tablet", "ipad",
        "phone", "iphone", "samsung galaxy", "pixel", "charger", "keyboard",
        "mouse", "router", "camera", "drone", "ps5", "xbox", "nintendo",
        "gaming", "graphics card", "motherboard",
    ],
    "apparel": [
        "shirt", "pants", "jeans", "jacket", "hoodie", "sweater", "dress",
        "shoes", "sneakers", "boots", "sandals", "running shoes", "nike",
        "adidas", "under armour", "lululemon", "north face", "patagonia",
        "coat", "suit", "leggings", "shorts", "socks", "hat", "cap", "scarf",
        "gloves", "backpack", "bag", "luggage", "hoka", "brooks", "asics",
        "new balance", "puma", "reebok",
    ],
    "travel": [
        "flight", "flights", "airline", "airfare", "roundtrip", "round trip",
        "hotel", "resort", "motel", "airbnb", "vrbo",
        "rental car", "car rental", "hertz", "enterprise", "avis",
        "cruise", "vacation", "trip", "travel deal", "expedia", "kayak",
        "priceline", "southwest", "delta", "united", "american airlines",
        "spirit", "frontier", "jetblue", "nonstop", "layover",
    ],
}


def categorize(deal):
    title = (deal.get("title") or "").lower()
    for category, keywords in KEYWORDS.items():
        if any(kw in title for kw in keywords):
            return category
    return "other"


def assign_categories(deals):
    result = {"electronics": [], "apparel": [], "travel": [], "other": []}
    for deal in deals:
        cat = categorize(deal)
        deal["category"] = cat
        result[cat].append(deal)
    return result
