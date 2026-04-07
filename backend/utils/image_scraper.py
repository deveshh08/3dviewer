"""
iPromo image scraper.
CloudFront product image URLs are embedded directly in the raw HTML (RSC payload).
No browser or _next/data endpoint needed.
"""
import re
import httpx

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def fetch_product_images(page_url: str) -> list[str]:
    """
    Fetch the product page HTML and extract all CloudFront product image URLs.
    Returns a deduplicated, ordered list.
    """
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=_HEADERS) as client:
        resp = await client.get(page_url)
        resp.raise_for_status()

    # Truncate at "you_may_also_like" to exclude recommended product images
    html = resp.text
    cutoff = html.find('"you_may_also_like"')
    if cutoff > 0:
        html = html[:cutoff]

    seen: set[str] = set()
    return list(dict.fromkeys(
        re.findall(
            r'https://dcridil0zrtkb\.cloudfront\.net/catalog/product/[^"\s\\]+', html
        )
    ))
