from fastapi import APIRouter
import httpx
from bs4 import BeautifulSoup
import re

router = APIRouter()

COLORS = {
    "Aqua":     "#7ECECE",
    "Pink":     "#F08080",
    "Tan":      "#C4A882",
    "Black":    "#1A1A1A",
    "Silver":   "#B0B0B0",
    "White":    "#F5F5F5",
    "Navy":     "#1B2A6B",
    "Graphite": "#4A4A4A",
    "Purple":   "#6A0DAD",
    "Red":      "#CC2020",
}

@router.get("/")
async def get_product(url: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")

        name_tag = soup.find("h1")
        name = name_tag.get_text(strip=True) if name_tag else "Crosswind Quarter Zip Sweatshirt"

        price_tag = soup.find(string=re.compile(r"\$\d+"))
        price = price_tag.strip() if price_tag else "$43.99 - $51.99"

        item_tag = soup.find(string=re.compile(r"Item #"))
        item_no = item_tag.strip() if item_tag else "IP-276-9359"

    except Exception:
        name    = "Crosswind Quarter Zip Sweatshirt"
        price   = "$43.99 – $51.99"
        item_no = "IP-276-9359"

    return {
        "name":    name,
        "item_no": item_no,
        "price":   price,
        "colors":  COLORS,
        "model_path": "/models/quarter_zip.glb",
        "logo_zones": [
            {"id": "chest_left",  "label": "Left Chest",  "uv": [0.35, 0.55, 0.15, 0.15]},
            {"id": "chest_right", "label": "Right Chest", "uv": [0.55, 0.55, 0.15, 0.15]},
            {"id": "back_center", "label": "Back Center", "uv": [0.50, 0.50, 0.30, 0.30]},
        ]
    }
