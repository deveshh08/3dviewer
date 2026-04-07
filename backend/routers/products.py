from fastapi import APIRouter, HTTPException, Depends
import httpx
from bs4 import BeautifulSoup
import re
from sqlalchemy.orm import Session
from database import get_db
from models import ProductImage, ProductGLB
from utils.category_mapper import get_glb_for_category
from utils.image_scraper import fetch_product_images
from utils.tripo import generate_glb

router = APIRouter()

_cache: dict = {}

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


@router.get("/")
async def get_product(url: str):
    if url in _cache:
        return _cache[url]
    result = await scrape_product(url)
    _cache[url] = result
    return result


@router.post("/scrape-images")
async def scrape_images(url: str, db: Session = Depends(get_db)):
    """Fetch all product images via hybrid method and store them in the DB."""
    # Return cached rows if already scraped
    existing = db.query(ProductImage).filter(ProductImage.product_url == url).all()
    if existing:
        return {"source": "cache", "count": len(existing),
                "images": [r.image_url for r in existing]}

    images = await fetch_product_images(url)
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this product URL")

    rows = [
        ProductImage(product_url=url, image_url=img_url, position=i)
        for i, img_url in enumerate(images)
    ]
    db.add_all(rows)
    db.commit()

    return {"source": "scraped", "count": len(rows),
            "images": [r.image_url for r in rows]}


@router.post("/generate-3d")
async def generate_3d(url: str, db: Session = Depends(get_db)):
    """Generate a GLB model for a product URL using TripoAI. Cached by URL."""
    # Return cached GLB if already generated
    existing = db.query(ProductGLB).filter(ProductGLB.product_url == url).first()
    if existing:
        return {"source": "cache", "glb_url": existing.glb_url, "task_id": existing.task_id}

    # Get stored images or scrape them now
    rows = db.query(ProductImage).filter(ProductImage.product_url == url)\
             .order_by(ProductImage.position).limit(3).all()
    if not rows:
        images = await fetch_product_images(url)
        if not images:
            raise HTTPException(status_code=404, detail="No images found for this product URL")
        db.add_all([ProductImage(product_url=url, image_url=img, position=i)
                    for i, img in enumerate(images)])
        db.commit()
        image_urls = images[:3]
    else:
        image_urls = [r.image_url for r in rows]

    try:
        glb_url, task_id = await generate_glb(image_urls)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TripoAI error: {e}")

    db.add(ProductGLB(product_url=url, glb_url=glb_url, task_id=task_id))
    db.commit()

    return {"source": "generated", "glb_url": glb_url, "task_id": task_id}



def get_stored_images(url: str, db: Session = Depends(get_db)):
    """Retrieve previously scraped images for a product URL."""
    rows = db.query(ProductImage).filter(ProductImage.product_url == url)\
               .order_by(ProductImage.position).all()
    return {"count": len(rows), "images": [r.image_url for r in rows]}
