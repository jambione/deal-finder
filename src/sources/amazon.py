import os


def fetch():
    access_key = os.environ.get("AMAZON_ACCESS_KEY")
    secret_key = os.environ.get("AMAZON_SECRET_KEY")
    partner_tag = os.environ.get("AMAZON_PARTNER_TAG")

    if not all([access_key, secret_key, partner_tag]):
        print("[amazon] skipping — AMAZON_ACCESS_KEY / AMAZON_SECRET_KEY / AMAZON_PARTNER_TAG not set")
        return []

    try:
        from paapi5_python_sdk.api.default_api import DefaultApi
        from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
        from paapi5_python_sdk.models.partner_type import PartnerType
        from paapi5_python_sdk.rest import ApiException
    except ImportError:
        print("[amazon] skipping — paapi5_python_sdk not installed")
        return []

    searches = [
        ("Electronics", "Electronics"),
        ("Clothing", "Apparel"),
        ("Travel", "Travel"),
    ]

    api = DefaultApi(
        access_key=access_key,
        secret_key=secret_key,
        host="webservices.amazon.com",
        region="us-east-1",
    )

    deals = []
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    for keywords, category in searches:
        try:
            req = SearchItemsRequest(
                partner_tag=partner_tag,
                partner_type=PartnerType.ASSOCIATES,
                keywords=keywords,
                search_index="All",
                item_count=10,
                resources=["ItemInfo.Title", "Offers.Listings.Price", "Images.Primary.Medium"],
            )
            resp = api.search_items(req)
            if not resp.search_result:
                continue
            for item in resp.search_result.items:
                title = item.item_info.title.display_value if item.item_info and item.item_info.title else ""
                url = item.detail_page_url or ""
                price = None
                original_price = None
                if item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if listing.price:
                        price = listing.price.amount
                    if listing.saving_basis:
                        original_price = listing.saving_basis.amount
                image_url = None
                if item.images and item.images.primary and item.images.primary.medium:
                    image_url = item.images.primary.medium.url
                deals.append({
                    "title": title,
                    "url": url,
                    "price": price,
                    "original_price": original_price,
                    "source": "amazon",
                    "votes": 0,
                    "posted_at": now,
                    "image_url": image_url,
                })
        except ApiException as e:
            print(f"[amazon] API error for {keywords}: {e}")

    return deals
