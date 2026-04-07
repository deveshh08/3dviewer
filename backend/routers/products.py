import logging
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
import httpx
from bs4 import BeautifulSoup
import re
from sqlalchemy.orm import Session
from database import get_db
from models import ProductImage, ProductGLB
from utils.category_mapper import get_glb_for_category
from utils.image_scraper import fetch_product_images
from utils.tripo import generate_glb, poll_task

logger = logging.getLogger(__name__)
router = APIRouter()

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB_DIR   = os.path.join(os.getenv("DATA_DIR", os.path.join(BASE_DIR, "static")), "glbs")
os.makedirs(GLB_DIR, exist_ok=True)

_cache: dict = {}


async def _download_and_store_glb(task_id: str, meshy_url: str) -> str:
    """Download GLB from Meshy and save locally. Returns local static path."""
    local_path = os.path.join(GLB_DIR, f"{task_id}.glb")
    if os.path.exists(local_path):
        logger.info("[glb_store] Already on disk | task_id=%s", task_id)
        return f"/static/glbs/{task_id}.glb"
    logger.info("[glb_store] Downloading GLB | task_id=%s", task_id)
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        resp = await client.get(meshy_url)
        resp.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(resp.content)
    logger.info("[glb_store] Saved | path=%s size=%d bytes", local_path, len(resp.content))
    return f"/static/glbs/{task_id}.glb"


COLOR_CODE_MAP = {
    "AQ": {"name": "Aqua",     "hex": "#7ECECE"},
    "PK": {"name": "Pink",     "hex": "#F08080"},
    "SN": {"name": "Sand",     "hex": "#C4A882"},
    "BK": {"name": "Black",    "hex": "#1A1A1A"},
    "GR": {"name": "Graphite", "hex": "#4A4A4A"},
    "SL": {"name": "Silver",   "hex": "#B0B0B0"},
    "WH": {"name": "White",    "hex": "#F5F5F5"},
    "NV": {"name": "Navy",     "hex": "#1B2A6B"},
    "PU": {"name": "Purple",   "hex": "#6A0DAD"},
    "RD": {"name": "Red",      "hex": "#CC2020"},
    "RY": {"name": "Royal",    "hex": "#2B4EAA"},
    "FO": {"name": "Forest",   "hex": "#2D5A27"},
    "MR": {"name": "Maroon",   "hex": "#800000"},
    "OR": {"name": "Orange",   "hex": "#E06820"},
    "YL": {"name": "Yellow",   "hex": "#E8C820"},
    "LB": {"name": "Lt Blue",  "hex": "#87CEEB"},
    "CH": {"name": "Charcoal", "hex": "#36454F"},
    "KH": {"name": "Khaki",    "hex": "#C3B091"},
}

DEFAULT_COLORS = [
    {"name": "Black",    "hex": "#1A1A1A"},
    {"name": "Navy",     "hex": "#1B2A6B"},
    {"name": "White",    "hex": "#F5F5F5"},
    {"name": "Graphite", "hex": "#4A4A4A"},
    {"name": "Red",      "hex": "#CC2020"},
]


async def scrape_product(url: str) -> dict:
    logger.info("[scrape_product] Fetching URL: %s", url)
    try:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 Chrome/120 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except Exception as e:
        logger.error("[scrape_product] Failed to fetch URL: %s | error: %s", url, e)
        raise HTTPException(status_code=422, detail=f"Could not fetch URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    name = "Unknown Product"
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)

    item_no = ""
    for tag in soup.find_all(string=re.compile(r"Item\s*#")):
        match = re.search(r"Item\s*#\s*([\w-]+)", tag)
        if match:
            item_no = match.group(1)
            break

    price = ""
    price_el = soup.find(class_=re.compile(r"price", re.I))
    if price_el:
        price = price_el.get_text(strip=True)
    if not price:
        match = re.search(r"\$[\d,]+\.\d{2}\s*[-–]\s*\$[\d,]+\.\d{2}", resp.text)
        if match:
            price = match.group(0)

    breadcrumbs = []
    bc_el = soup.find(class_=re.compile(r"breadcrumb", re.I))
    if bc_el:
        breadcrumbs = [a.get_text(strip=True) for a in bc_el.find_all("a")]

    colors = []
    swatch_pattern = re.compile(r"color-([A-Z]{2})", re.I)
    for el in soup.find_all(attrs={"class": swatch_pattern}):
        for cls in el.get("class", []):
            m = swatch_pattern.match(cls)
            if m:
                code = m.group(1).upper()
                if code in COLOR_CODE_MAP:
                    c = COLOR_CODE_MAP[code]
                    if c not in colors:
                        colors.append(c)

    if not colors:
        colors = DEFAULT_COLORS

    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src", "")
        alt = img.get("alt", "").lower()
        if not src:
            continue
        if any(x in src.lower() for x in ["logo", "icon", "thumb", "sprite"]):
            continue
        if any(x in alt for x in ["logo", "icon", "badge"]):
            continue
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = "https://www.ipromo.com" + src
        if src not in images:
            images.append(src)
        if len(images) >= 6:
            break

    glb_file = get_glb_for_category(url, breadcrumbs)
    logger.info("[scrape_product] Done | name=%s item_no=%s glb_file=%s images=%d",
                name, item_no, glb_file, len(images))

    pricing_tiers = [
        {"qty": "12–23",  "price": "$51.99", "save": None},
        {"qty": "24–47",  "price": "$49.99", "save": "3%"},
        {"qty": "48–95",  "price": "$47.99", "save": "7%"},
        {"qty": "96–143", "price": "$45.99", "save": "11%"},
        {"qty": "144+",   "price": "$43.99", "save": "15%"},
    ]

    return {
        "name":          name,
        "item_no":       item_no,
        "price":         price,
        "breadcrumbs":   breadcrumbs,
        "colors":        colors,
        "images":        images,
        "glb_file":      glb_file,
        "pricing_tiers": pricing_tiers,
        "source_url":    url,
    }


@router.get("/glb-proxy")
async def glb_proxy(url: str):
    """Proxy a GLB file to avoid CORS issues when loading from the browser."""
    import urllib.parse
    from fastapi.responses import StreamingResponse
    logger.info("[glb_proxy] Fetching GLB | url=%s", url[:80])
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    logger.info("[glb_proxy] Streaming GLB | size=%d bytes", len(resp.content))
    return StreamingResponse(
        iter([resp.content]),
        media_type="model/gltf-binary",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/")
async def get_product(url: str):
    if url in _cache:
        logger.info("[get_product] Cache hit | url=%s", url)
        return _cache[url]
    logger.info("[get_product] Cache miss, scraping | url=%s", url)
    result = await scrape_product(url)
    _cache[url] = result
    return result


@router.post("/scrape-images")
async def scrape_images(url: str, db: Session = Depends(get_db)):
    """Fetch all product images and store them in the DB."""
    existing = db.query(ProductImage).filter(ProductImage.product_url == url).all()
    if existing:
        logger.info("[scrape_images] DB cache hit | url=%s count=%d", url, len(existing))
        return {"source": "cache", "count": len(existing),
                "images": [r.image_url for r in existing]}

    logger.info("[scrape_images] Scraping images | url=%s", url)
    images = await fetch_product_images(url)
    if not images:
        logger.warning("[scrape_images] No images found | url=%s", url)
        raise HTTPException(status_code=404, detail="No images found for this product URL")

    rows = [ProductImage(product_url=url, image_url=img_url, position=i)
            for i, img_url in enumerate(images)]
    db.add_all(rows)
    db.commit()
    logger.info("[scrape_images] Stored %d images | url=%s", len(rows), url)

    return {"source": "scraped", "count": len(rows),
            "images": [r.image_url for r in rows]}


@router.post("/generate-3d")
async def generate_3d(url: str, db: Session = Depends(get_db)):
    """Submit a Meshy AI task for a product URL. Returns task_id immediately."""
    existing = db.query(ProductGLB).filter(ProductGLB.product_url == url).first()
    if existing:
        logger.info("[generate_3d] DB cache hit | url=%s glb_url=%s", url, existing.glb_url[:80])
        # glb_url is already a local /static path — return directly, no proxy needed
        return {"source": "cache", "glb_url": existing.glb_url, "task_id": existing.task_id}

    rows = db.query(ProductImage).filter(ProductImage.product_url == url)\
             .order_by(ProductImage.position).limit(3).all()
    if not rows:
        logger.info("[generate_3d] No stored images, scraping now | url=%s", url)
        images = await fetch_product_images(url)
        if not images:
            raise HTTPException(status_code=404, detail="No images found for this product URL")
        db.add_all([ProductImage(product_url=url, image_url=img, position=i)
                    for i, img in enumerate(images)])
        db.commit()
        image_urls = images[:3]
    else:
        image_urls = [r.image_url for r in rows]

    logger.info("[generate_3d] Submitting to Meshy AI | url=%s image=%s", url, image_urls[0])
    try:
        task_id = await generate_glb(image_urls)
    except Exception as e:
        logger.error("[generate_3d] Meshy submit error | url=%s error=%s", url, e)
        raise HTTPException(status_code=502, detail=f"Meshy error: {e}")

    return {"source": "pending", "task_id": task_id}


@router.get("/generation-progress")
async def generation_progress(task_id: str, product_url: str, db: Session = Depends(get_db)):
    """Poll Meshy for task progress. Saves GLB to DB when SUCCEEDED."""
    try:
        result = await poll_task(task_id)
    except Exception as e:
        logger.error("[generation_progress] Poll error | task_id=%s error=%s", task_id, e)
        raise HTTPException(status_code=502, detail=f"Poll error: {e}")

    if result["status"] == "SUCCEEDED" and result["glb_url"]:
        existing = db.query(ProductGLB).filter(ProductGLB.product_url == product_url).first()
        if not existing:
            # Download from Meshy and store locally so URL never expires
            local_path = await _download_and_store_glb(task_id, result["glb_url"])
            db.add(ProductGLB(product_url=product_url, glb_url=local_path, task_id=task_id))
            db.commit()
            logger.info("[generation_progress] GLB stored locally | product_url=%s path=%s", product_url, local_path)
        else:
            local_path = existing.glb_url
        # Return local path instead of expiring Meshy URL
        result["glb_url"] = local_path

    return result


@router.get("/stored-images")
def get_stored_images(url: str, db: Session = Depends(get_db)):
    """Retrieve previously scraped images for a product URL."""
    rows = db.query(ProductImage).filter(ProductImage.product_url == url)\
               .order_by(ProductImage.position).all()
    logger.info("[get_stored_images] url=%s count=%d", url, len(rows))
    return {"count": len(rows), "images": [r.image_url for r in rows]}
