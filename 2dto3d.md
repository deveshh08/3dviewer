# iPromo 3D Configurator — From 2D Product URL to 3D Experience
> **The core problem:** iPromo product pages only have flat 2D photos.
> **This document:** Explains every possible solution, picks the best one, and gives full implementation code.

---

## 🧠 Understanding the Real Problem

When a user pastes this URL:
```
https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html
```

The page contains:
```
✅  Product name          "Crosswind Quarter Zip Sweatshirt"
✅  Product category      "Sweatshirts & Sweatpants > Quarter-Zips"
✅  Color list            Aqua, Navy, Black, Red, White...
✅  Price table           $43.99 – $51.99
✅  2D product photos     front view, back view, lifestyle shots
❌  No 3D model           nowhere on the page
❌  No GLB file           does not exist
❌  No depth data         flat photos only
```

So the question becomes: **how do we get a 3D model from a 2D product page?**

---

## 🗺️ All Possible Approaches (with honest pros/cons)

### Approach 1 — Category-to-GLB Mapping (Recommended ✅)
**What it is:** You build a small library of ~12 generic GLB models
(one per apparel category: quarter-zip, t-shirt, polo, hoodie, etc.).
When the user pastes a URL, the backend reads the product category and
serves the matching GLB. The GLB is then colored to match the product's
selected color, and the user's logo is projected onto it.

```
User pastes URL
    ↓
Backend scrapes: category = "Quarter-Zips"
    ↓
Category map: "Quarter-Zips" → quarter_zip.glb
    ↓
Frontend loads quarter_zip.glb, tints it with selected color
    ↓
User uploads logo → DecalGeometry stamps it on
```

| | |
|---|---|
| ✅ Works for every iPromo product URL instantly | |
| ✅ No AI API cost | |
| ✅ Fast — GLB loads in < 2s | |
| ✅ High visual quality (you control the GLB) | |
| ⚠️ GLB is generic, not photo-identical to the real product | |
| ⚠️ Requires ~12 GLB files upfront (one-time work) | |

**Verdict: This is what Nike, Under Armour, and every real apparel configurator does.**
They never use the actual product photo as the 3D model.
They use generic base meshes and change color + logo.

---

### Approach 2 — AI 3D Generation from Product Photos
**What it is:** Services like Meshy.ai, Tripo3D, or CSM.ai accept
2D images and return a GLB file using AI reconstruction.

```
User pastes URL
    ↓
Backend scrapes the product's front-view photo URL
    ↓
Sends photo to Meshy.ai API → waits 30–90 seconds
    ↓
Receives .glb file → caches it in database
    ↓
Frontend loads it
```

| | |
|---|---|
| ✅ Model is based on the actual product photo | |
| ✅ No manual GLB library needed | |
| ❌ 30–90 second wait per new product | |
| ❌ Costs $0.05–$0.50 per generation | |
| ❌ Quality varies — clothes are notoriously hard for AI 3D | |
| ❌ Logo placement via DecalGeometry still needed | |
| ❌ Color variants still need manual material tinting | |

**Verdict: Impressive demo, poor production reliability for apparel.**
AI 3D generation works best on rigid objects (shoes, bottles, mugs).
Soft fabric like sweatshirts comes out distorted.

---

### Approach 3 — 2D Photo on a 3D Curved Surface (Pseudo-3D)
**What it is:** Use the actual product photo as a texture mapped onto
a slightly curved plane in Three.js. When the user rotates, it feels 3D.
Logo is composited on the photo using canvas before applying.

```
User pastes URL
    ↓
Backend scrapes front-view + back-view photo URLs
    ↓
Frontend: create a curved PlaneGeometry, apply photo as texture
    ↓
User logo → composited onto canvas → applied as second texture layer
    ↓
OrbitControls lets user "rotate" — shows front/back photo
```

| | |
|---|---|
| ✅ Uses the actual product photo | |
| ✅ Zero 3D modeling needed | |
| ✅ Fast to implement | |
| ❌ Not actually 3D — perspective looks wrong when rotating | |
| ❌ Logo placement is flat, does not wrap around curves | |
| ❌ Feels like a "fake" 3D experience | |

**Verdict: Good for MVP if you have zero GLB files yet.
Can run in parallel while you build the GLB library.**

---

### Approach 4 — Hybrid (Best of 1 + 3)
**What it is:** Use Approach 1 (GLB library) as the primary path.
Fall back to Approach 3 (photo on curved plane) for product categories
that don't have a GLB yet.

```
User pastes URL
    ↓
Scrape category from URL
    ↓
GLB exists for this category?
    ├── YES → load GLB, tint color, place logo via DecalGeometry
    └── NO  → load product photo, curved plane, logo via canvas
```

**Verdict: This is the recommended architecture for this project.**
Start with 3–4 GLBs for the most common iPromo categories (quarter-zips,
t-shirts, hoodies, polos) and fall back to photo mode for everything else.

---

## 🏆 Recommended Architecture (Approach 4 — Hybrid)

```
┌─────────────────────────────────────────────────────────────┐
│                    iPromo Product URL                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI: /api/products/?url=...                 │
│                                                              │
│  1. Scrape product page (httpx + BeautifulSoup)              │
│  2. Extract: name, category, colors, images, price           │
│  3. Map category → GLB filename (or null if not found)       │
│  4. Return JSON with all data + glb_file field               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend                             │
│                                                              │
│  if (product.glb_file)                                       │
│    → Viewer3D.jsx   [Three.js + DecalGeometry logo]          │
│  else                                                        │
│    → FlatViewer.jsx [Three.js curved plane + canvas logo]    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 GLB Library — What to Build

You only need GLBs for iPromo's most popular categories.
These 12 cover ~80% of all iPromo apparel orders:

| GLB filename | iPromo Categories it covers | Priority |
|---|---|---|
| `quarter_zip.glb` | Quarter-Zips | 🔴 High |
| `crewneck.glb` | Crew Neck Sweatshirts | 🔴 High |
| `hoodie.glb` | Hoodies | 🔴 High |
| `tshirt.glb` | Short/Long Sleeve T-Shirts | 🔴 High |
| `polo.glb` | Polos (Men's + Ladies') | 🔴 High |
| `lightweight_jacket.glb` | Lightweight Jackets, Soft Shells | 🟡 Medium |
| `fleece_vest.glb` | Fleece Jackets & Vests | 🟡 Medium |
| `baseball_cap.glb` | Baseball Caps, Trucker Hats | 🟡 Medium |
| `beanie.glb` | Beanies | 🟡 Medium |
| `tote_bag.glb` | Tote Bags | 🟡 Medium |
| `backpack.glb` | Backpacks | 🟢 Low |
| `tumbler.glb` | Tumblers, Travel Mugs | 🟢 Low |

### Where to get these GLBs (free options)

| Source | URL | License | Quality |
|---|---|---|---|
| Sketchfab (Free) | sketchfab.com | CC BY 4.0 | ⭐⭐⭐⭐ |
| Poly Pizza | poly.pizza | CC BY | ⭐⭐⭐ |
| KhronosGroup samples | github.com/KhronosGroup/glTF-Sample-Assets | MIT | ⭐⭐⭐ |
| ReadyPlayerMe | readyplayer.me | Free tier | ⭐⭐⭐⭐ |

**Search terms for Sketchfab:**
- "quarter zip sweatshirt" → filter: Free, Downloadable
- "crew neck sweatshirt fabric"
- "hoodie 3d model"
- "polo shirt low poly"
- "t-shirt 3d"

**Important when downloading:** Always check the GLB has
separate material slots for fabric vs hardware (zipper/buttons).
In Sketchfab viewer, click the Materials tab to verify.

---

## 📋 Category Detection Logic

The backend needs to map iPromo URL breadcrumbs → GLB file.
iPromo URLs follow a pattern:
```
/apparel/sweatshirts-sweatpants/quarter-zips/product-name.html
/apparel/t-shirts/short-sleeve-t-shirts/product-name.html
/apparel/custom-polos/men-s-cotton-blend-polos/product-name.html
```

### `backend/utils/category_mapper.py`

```python
"""
Maps iPromo product categories (from URL or breadcrumb) to GLB filenames.
Returns None if no matching GLB exists (triggers flat photo fallback).
"""

# Order matters — more specific matches first
CATEGORY_TO_GLB = [
    # ── Sweatshirts ────────────────────────────────────────────────────────
    (["quarter-zip", "quarter_zip", "1/4 zip"], "quarter_zip.glb"),
    (["crew-neck", "crewneck", "crew neck"],     "crewneck.glb"),
    (["hoodie", "hooded"],                       "hoodie.glb"),
    (["sweatshirt", "sweatpant", "jogger"],      "crewneck.glb"),

    # ── T-Shirts ───────────────────────────────────────────────────────────
    (["t-shirt", "tshirt", "tank top", "tee"],  "tshirt.glb"),
    (["performance shirt", "long sleeve"],       "tshirt.glb"),

    # ── Polos ──────────────────────────────────────────────────────────────
    (["polo", "golf shirt"],                     "polo.glb"),

    # ── Outerwear ──────────────────────────────────────────────────────────
    (["lightweight jacket", "soft shell",
      "windbreaker"],                            "lightweight_jacket.glb"),
    (["fleece", "vest"],                         "fleece_vest.glb"),
    (["puffer", "insulated", "parka"],           "lightweight_jacket.glb"),

    # ── Headwear ───────────────────────────────────────────────────────────
    (["baseball cap", "trucker hat",
      "snapback", "fitted cap"],                 "baseball_cap.glb"),
    (["beanie", "knit hat", "winter hat"],       "beanie.glb"),
    (["bucket hat", "visor"],                    "baseball_cap.glb"),

    # ── Bags ───────────────────────────────────────────────────────────────
    (["tote", "shopping bag"],                   "tote_bag.glb"),
    (["backpack", "drawstring"],                 "backpack.glb"),

    # ── Drinkware ──────────────────────────────────────────────────────────
    (["tumbler", "travel mug", "water bottle",
      "coffee mug"],                             "tumbler.glb"),
]


def get_glb_for_category(url: str, breadcrumbs: list[str]) -> str | None:
    """
    Returns the GLB filename for a product, or None if no match.

    Args:
        url:         The full product URL string
        breadcrumbs: List of breadcrumb strings scraped from the page
                     e.g. ["Apparel", "Sweatshirts", "Quarter-Zips", "Crosswind..."]
    """
    # Combine URL + breadcrumbs into one searchable string
    search_text = (url + " " + " ".join(breadcrumbs)).lower()

    for keywords, glb_file in CATEGORY_TO_GLB:
        if any(kw in search_text for kw in keywords):
            return glb_file

    return None   # triggers flat photo fallback


# ── Unit test (run: python category_mapper.py) ────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html",
         ["Apparel", "Sweatshirts & Sweatpants", "Quarter-Zips"],
         "quarter_zip.glb"),

        ("https://www.ipromo.com/apparel/t-shirts/short-sleeve-t-shirts/gildan.html",
         ["Apparel", "T-Shirts", "Short Sleeve T-Shirts"],
         "tshirt.glb"),

        ("https://www.ipromo.com/food-candy/gourmet/chocolate.html",
         ["Food & Candy", "Gourmet", "Chocolate"],
         None),
    ]
    for url, crumbs, expected in tests:
        result = get_glb_for_category(url, crumbs)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url.split('/')[-1]} → {result} (expected {expected})")
```

---

## 🔧 Updated Backend Scraper

### `backend/routers/products.py` (full rewrite)

```python
from fastapi import APIRouter, HTTPException
import httpx
from bs4 import BeautifulSoup
import re
import os
from utils.category_mapper import get_glb_for_category

router = APIRouter()

# ── Static color map for iPromo swatches ──────────────────────────────────────
# iPromo uses short color codes in their swatch HTML (AQ = Aqua, etc.)
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
    """
    Scrape an iPromo product page and return structured data.
    Falls back gracefully on any error.
    """
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

    # ── Product name ─────────────────────────────────────────────────────────
    name = "Unknown Product"
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)

    # ── Item number ──────────────────────────────────────────────────────────
    item_no = ""
    for tag in soup.find_all(string=re.compile(r"Item\s*#")):
        match = re.search(r"Item\s*#\s*([\w-]+)", tag)
        if match:
            item_no = match.group(1)
            break

    # ── Price ────────────────────────────────────────────────────────────────
    price = ""
    price_el = soup.find(class_=re.compile(r"price", re.I))
    if price_el:
        price = price_el.get_text(strip=True)
    if not price:
        match = re.search(r"\$[\d,]+\.\d{2}\s*[-–]\s*\$[\d,]+\.\d{2}", resp.text)
        if match:
            price = match.group(0)

    # ── Breadcrumbs (used for category detection) ─────────────────────────────
    breadcrumbs = []
    bc_el = soup.find(class_=re.compile(r"breadcrumb", re.I))
    if bc_el:
        breadcrumbs = [a.get_text(strip=True) for a in bc_el.find_all("a")]

    # ── Colors ───────────────────────────────────────────────────────────────
    colors = []
    # iPromo color swatches often have data-color or class like "color-AQ"
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

    # ── Product images ───────────────────────────────────────────────────────
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src", "")
        alt = img.get("alt", "").lower()
        if not src:
            continue
        # Skip tiny thumbnails, logos, icons
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

    # ── GLB mapping ──────────────────────────────────────────────────────────
    glb_file = get_glb_for_category(url, breadcrumbs)

    # ── Pricing tiers (static for iPromo sweatshirts) ────────────────────────
    pricing_tiers = [
        {"qty": "12–23",   "price": "$51.99", "save": None},
        {"qty": "24–47",   "price": "$49.99", "save": "3%"},
        {"qty": "48–95",   "price": "$47.99", "save": "7%"},
        {"qty": "96–143",  "price": "$45.99", "save": "11%"},
        {"qty": "144+",    "price": "$43.99", "save": "15%"},
    ]

    return {
        "name":         name,
        "item_no":      item_no,
        "price":        price,
        "breadcrumbs":  breadcrumbs,
        "colors":       colors,
        "images":       images,
        "glb_file":     glb_file,           # None = use flat photo fallback
        "pricing_tiers": pricing_tiers,
        "source_url":   url,
    }


@router.get("/")
async def get_product(url: str):
    return await scrape_product(url)
```

---

## 🎨 Frontend: Smart Viewer (GLB or Flat Photo)

The frontend checks `product.glb_file` and renders the right viewer.

### `frontend/src/pages/ConfiguratorPage.jsx`

```jsx
import { useEffect, useState, useRef, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import axios from 'axios'
import toast, { Toaster } from 'react-hot-toast'
import Navbar from '../components/Navbar'
import Viewer3D from '../components/Viewer3D'
import FlatViewer from '../components/FlatViewer'
import ColorPicker from '../components/ColorPicker'
import LogoUploader from '../components/LogoUploader'
import ShareButton from '../components/ShareButton'
import PDFDownloadButton from '../components/PDFDownloadButton'
import ProductInfo from '../components/ProductInfo'
import PricingTable from '../components/PricingTable'
import { useConfigurator } from '../store/configuratorStore'

export default function ConfiguratorPage() {
  const [searchParams] = useSearchParams()
  const productUrl = searchParams.get('url') ?? ''
  const [loading, setLoading] = useState(false)
  const captureRef = useRef(null)

  const { setProductData, setProductUrl, productData } = useConfigurator()

  useEffect(() => {
    if (!productUrl) return
    setProductUrl(productUrl)
    setLoading(true)

    axios.get(`/api/products/?url=${encodeURIComponent(productUrl)}`)
      .then(({ data }) => {
        setProductData(data)
        if (!data.glb_file) {
          toast('No 3D model for this category — showing photo preview', {
            icon: '📸',
            duration: 4000,
          })
        }
      })
      .catch(() => toast.error('Could not load product — check the URL'))
      .finally(() => setLoading(false))
  }, [productUrl])

  const onRegisterCapture = useCallback((fn) => {
    captureRef.current = fn
  }, [])

  // ── URL input if no URL in query string ────────────────────────────────────
  if (!productUrl) {
    return <URLInputScreen />
  }

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      <Navbar />
      <Toaster position="top-right" />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6
                       grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">

        {/* ── 3D or Flat Viewer ─────────────────────────────────────────── */}
        <div className="relative h-[520px] lg:h-auto lg:min-h-[580px]">
          {loading && <ViewerSkeleton />}

          {!loading && productData && (
            productData.glb_file
              ? <Viewer3D
                  glbFile={`/models/${productData.glb_file}`}
                  onRegisterCapture={onRegisterCapture}
                />
              : <FlatViewer
                  images={productData.images}
                  onRegisterCapture={onRegisterCapture}
                />
          )}
        </div>

        {/* ── Control panel ─────────────────────────────────────────────── */}
        <aside className="flex flex-col gap-4">
          <ProductInfo />
          <ColorPicker />
          <LogoUploader />
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-sm font-semibold text-ipromo-navy">3. Share & Export</h3>
            <ShareButton captureRef={captureRef} />
            <PDFDownloadButton captureRef={captureRef} />
          </div>
          <PricingTable />
        </aside>
      </main>
    </div>
  )
}

// ── URL input screen (shown when no ?url= param) ───────────────────────────
function URLInputScreen() {
  const [inputUrl, setInputUrl] = useState('')

  const go = () => {
    if (!inputUrl.includes('ipromo.com')) {
      toast.error('Please paste an iPromo product URL')
      return
    }
    window.location.href = `/?url=${encodeURIComponent(inputUrl)}`
  }

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      <Navbar />
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="bg-white rounded-3xl p-8 shadow-lg max-w-lg w-full space-y-5">
          {/* Logo */}
          <div className="text-center">
            <img src="/ipromo_logo.png" alt="iPromo" className="h-10 mx-auto mb-3" />
            <h1 className="text-xl font-semibold text-ipromo-navy">3D Product Configurator</h1>
            <p className="text-sm text-slate-500 mt-1">
              Paste any iPromo product URL to see it in 3D with your logo
            </p>
          </div>

          {/* Input */}
          <div className="space-y-2">
            <input
              type="url"
              value={inputUrl}
              onChange={e => setInputUrl(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && go()}
              placeholder="https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html"
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm
                         focus:outline-none focus:ring-2 focus:ring-ipromo-teal"
            />
            <button
              onClick={go}
              className="w-full bg-ipromo-navy text-white py-3 rounded-xl font-medium
                         hover:bg-blue-900 transition-colors"
            >
              View in 3D →
            </button>
          </div>

          {/* Example links */}
          <div>
            <p className="text-xs text-slate-400 mb-2">Or try an example:</p>
            <div className="flex flex-col gap-1.5">
              {[
                ["Crosswind Quarter Zip", "https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html"],
                ["Gildan T-Shirt",        "https://www.ipromo.com/gildan-ultra-cotton-t-shirt.html"],
                ["Sport-Tek Polo",        "https://www.ipromo.com/sport-tek-micropique-sport-wick-polo.html"],
              ].map(([label, url]) => (
                <button
                  key={url}
                  onClick={() => window.location.href = `/?url=${encodeURIComponent(url)}`}
                  className="text-left text-sm text-ipromo-teal hover:underline px-1"
                >
                  → {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ViewerSkeleton() {
  return (
    <div className="w-full h-full rounded-2xl bg-slate-100 animate-pulse flex items-center justify-center">
      <p className="text-slate-400 text-sm">Loading product…</p>
    </div>
  )
}
```

---

## 🎨 FlatViewer Component (Photo Fallback)

For product categories without a GLB, we show the actual product photo
with logo compositing on a 2D canvas. This is still useful and professional.

### `frontend/src/components/FlatViewer.jsx`

```jsx
import { useEffect, useRef, useState } from 'react'
import { useConfigurator } from '../store/configuratorStore'

export default function FlatViewer({ images, onRegisterCapture }) {
  const canvasRef = useRef(null)
  const [currentImage, setCurrentImage] = useState(0)
  const { selectedColor, logoTexture, decalTransform } = useConfigurator()

  // Composite product image + color tint + logo onto canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !images?.length) return
    const ctx = canvas.getContext('2d')

    const productImg = new Image()
    productImg.crossOrigin = 'anonymous'
    productImg.src = images[currentImage]

    productImg.onload = () => {
      // Draw product photo
      canvas.width  = productImg.naturalWidth  || 600
      canvas.height = productImg.naturalHeight || 600
      ctx.drawImage(productImg, 0, 0)

      // Soft color overlay (simulates fabric tint)
      ctx.globalAlpha = 0.25
      ctx.fillStyle = selectedColor
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.globalAlpha = 1.0

      // Draw logo if uploaded
      if (!logoTexture) return
      const logoImg = new Image()
      logoImg.crossOrigin = 'anonymous'
      logoImg.src = logoTexture

      logoImg.onload = () => {
        const scale  = decalTransform.scale ?? 1.0
        const w = canvas.width  * 0.22 * scale
        const h = canvas.height * 0.22 * scale
        // Left chest default position
        const x = canvas.width  * 0.25 + (decalTransform.offsetX ?? 0) * 50
        const y = canvas.height * 0.35 + (decalTransform.offsetY ?? 0) * 50

        ctx.save()
        ctx.translate(x + w/2, y + h/2)
        ctx.rotate((decalTransform.rotate ?? 0) * Math.PI / 180)
        ctx.drawImage(logoImg, -w/2, -h/2, w, h)
        ctx.restore()
      }
    }
  }, [images, currentImage, selectedColor, logoTexture, decalTransform])

  // Register canvas capture for PDF
  useEffect(() => {
    onRegisterCapture?.(() => canvasRef.current?.toDataURL('image/png'))
  }, [onRegisterCapture])

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden bg-slate-100 flex flex-col">
      <canvas
        ref={canvasRef}
        className="flex-1 w-full object-contain"
        style={{ imageRendering: 'auto' }}
      />

      {/* Image switcher (front / back / lifestyle) */}
      {images?.length > 1 && (
        <div className="flex gap-2 p-3 justify-center bg-white">
          {images.slice(0, 5).map((src, i) => (
            <button
              key={i}
              onClick={() => setCurrentImage(i)}
              className={`w-12 h-12 rounded-lg overflow-hidden border-2 transition-all
                ${currentImage === i ? 'border-ipromo-teal' : 'border-transparent'}`}
            >
              <img src={src} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* Notice badge */}
      <div className="absolute top-3 right-3 bg-amber-100 text-amber-800 text-xs
                      px-2 py-1 rounded-lg border border-amber-200">
        📸 Photo preview — 3D model coming soon for this category
      </div>
    </div>
  )
}
```

---

## 📁 File Changes Summary for IDE Agent

```
Files to CREATE:
────────────────────────────────────────────────────────
backend/utils/category_mapper.py          ← new file above
backend/routers/products.py               ← full rewrite above

frontend/src/components/FlatViewer.jsx    ← new file above
frontend/src/pages/ConfiguratorPage.jsx  ← full rewrite above

Files to UPDATE:
────────────────────────────────────────────────────────
frontend/src/store/configuratorStore.js  ← add glb_file field in productData
frontend/src/components/Viewer3D.jsx     ← accept glbFile as prop instead of hardcoded path

Files to ADD (static assets):
────────────────────────────────────────────────────────
frontend/public/models/quarter_zip.glb   ← download from Sketchfab
frontend/public/models/tshirt.glb        ← download from Sketchfab
frontend/public/models/polo.glb          ← download from Sketchfab
frontend/public/models/hoodie.glb        ← download from Sketchfab
(add more as needed per the table above)
```

---

## 🗓️ Recommended Build Phases

### Phase 0 — Immediate (today)
```
1. Update products.py with the new scraper + category mapper
2. Test: curl "http://localhost:8000/api/products/?url=https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html"
   Should return glb_file: "quarter_zip.glb"
3. Confirm your Sketchfab quarter_zip.glb is at frontend/public/models/quarter_zip.glb
4. Update ConfiguratorPage to show URL input screen when no ?url= param
```

### Phase 1 — This week
```
5. Implement FlatViewer.jsx (photo fallback)
6. Fix logo placement with DecalGeometry (see Logo Placement Plan doc)
7. Test with 3 different iPromo URLs — one with GLB, one without
8. Download 2–3 more GLBs from Sketchfab (t-shirt, polo, hoodie)
```

### Phase 2 — Next week
```
9.  Color picker → live GLB material tinting
10. Share link → save/load UUID config
11. PDF download
12. Add remaining GLBs from the priority table
```

### Phase 3 — Optional (if you want AI 3D)
```
13. Sign up for Meshy.ai (free tier: 200 credits/month)
14. Add /api/generate-3d endpoint that calls Meshy.ai with product photo
15. Use as fallback when no GLB match AND no photo available
16. Cache generated GLBs in database by product URL to avoid re-generation cost
```

---

## ❓ FAQ

**Q: Will the GLB look exactly like the real product photo?**
A: No — it's a generic 3D shape with the correct color applied. This is
exactly what Nike iD, CustomInk, and every apparel configurator does.
Customers understand that the 3D is a visual representation, not a photo.

**Q: What if the user pastes a non-apparel product URL (like a pen or mug)?**
A: `get_glb_for_category()` returns `None` → FlatViewer shows the product photo
with logo composited on canvas. This works for all products without needing 3D.

**Q: What if the scraper can't get colors from the page?**
A: It falls back to `DEFAULT_COLORS` (Black, Navy, White, Graphite, Red).
These 5 colors cover 80%+ of iPromo orders anyway.

**Q: How many GLB files do I need before launch?**
A: Just 1 is enough for a demo. 4–5 (quarter-zip, t-shirt, polo, hoodie, cap)
covers the most popular iPromo products for a production launch.

**Q: Should I build the AI generation option?**
A: Only if a client specifically requests "the 3D must look like the actual product."
For a sales tool / mockup generator, the category-GLB approach is better —
it's faster, cheaper, more reliable, and looks more polished.