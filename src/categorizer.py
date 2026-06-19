KEYWORDS = {
    "games": [
        "steam", "xbox game", "playstation", "ps4", "ps5", "nintendo switch",
        "pc game", "video game", "game deal", "epic games", "humble bundle",
        "gog.com", "game pass", "gaming deal", "indie game", "rpg", "fps",
        "simulation", "strategy game",
    ],
    "software": [
        "software", "lifetime license", "lifetime deal", "saas deal", "app deal",
        "plugin", "vpn deal", "antivirus", "password manager", "video editor",
        "photo editor", "design tool", "productivity app", "subscription deal",
        "license key", "office suite", "cloud storage deal",
    ],
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
    result = {"electronics": [], "apparel": [], "travel": [], "games": [], "software": [], "other": []}
    for deal in deals:
        existing_cat = deal.get("category")
        if existing_cat and existing_cat in result:
            result[existing_cat].append(deal)
        else:
            cat = categorize(deal)
            deal["category"] = cat
            result[cat].append(deal)
    return result
