# iPromo 3D Product Configurator — Full Build Plan
> **Stack:** FastAPI (Python 3.11) · React 18 + Vite · Three.js · Tailwind CSS  
> **Target Product:** Crosswind Quarter Zip Sweatshirt (IP-276-9359) — works for any iPromo URL  
> **Features:** Rotatable 3D model · Live color swap · Logo upload with UV mapping · Shareable link · PDF download

---

## Table of Contents
1. [Project Architecture](#1-project-architecture)
2. [Monorepo Folder Structure](#2-monorepo-folder-structure)
3. [Backend — FastAPI Setup](#3-backend--fastapi-setup)
4. [Database Models](#4-database-models)
5. [API Endpoints](#5-api-endpoints)
6. [3D Model Pipeline](#6-3d-model-pipeline)
7. [Frontend — React + Vite Setup](#7-frontend--react--vite-setup)
8. [Three.js Scene & Viewer Component](#8-threejs-scene--viewer-component)
9. [Color Switcher Component](#9-color-switcher-component)
10. [Logo Upload & UV Mapping](#10-logo-upload--uv-mapping)
11. [Share Link Feature](#11-share-link-feature)
12. [PDF Download Feature](#12-pdf-download-feature)
13. [iPromo Branding & UI Polish](#13-ipromo-branding--ui-polish)
14. [Environment Variables](#14-environment-variables)
15. [Docker Compose (Optional)](#15-docker-compose-optional)
16. [Step-by-Step Build Order for the IDE Agent](#16-step-by-step-build-order-for-the-ide-agent)

---

## 1. Project Architecture

```
Browser (React + Three.js)
        │
        │  REST / multipart
        ▼
FastAPI Backend
   ├── /api/products      ← scrape or static product data
   ├── /api/configs       ← save/load shareable configs (UUID)
   ├── /api/upload-logo   ← store logo, return URL
   └── /api/pdf           ← generate PDF mockup
        │
        ├── SQLite (dev) / PostgreSQL (prod)  ← configs table
        └── /static/uploads                   ← logo files
```

---

## 2. Monorepo Folder Structure

```
ipromo-configurator/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── database.py
│   ├── routers/
│   │   ├── products.py
│   │   ├── configs.py
│   │   ├── upload.py
│   │   └── pdf.py
│   ├── utils/
│   │   ├── pdf_generator.py
│   │   └── scraper.py
│   ├── static/
│   │   └── uploads/          ← uploaded logos stored here
│   ├── assets/
│   │   └── ipromo_logo.png   ← iPromo 27th anniversary logo (download from site)
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js
│       ├── components/
│       │   ├── Viewer3D.jsx          ← Three.js canvas
│       │   ├── ColorPicker.jsx
│       │   ├── LogoUploader.jsx
│       │   ├── ShareButton.jsx
│       │   ├── PDFDownloadButton.jsx
│       │   ├── ProductInfo.jsx
│       │   └── Navbar.jsx
│       ├── hooks/
│       │   └── useConfigurator.js
│       ├── store/
│       │   └── configuratorStore.js  ← Zustand
│       ├── pages/
│       │   ├── ConfiguratorPage.jsx  ← main page
│       │   └── SharedViewPage.jsx    ← /share/:uuid
│       └── assets/
│           └── ipromo_logo.png
│
├── docker-compose.yml
└── README.md
```

---

## 3. Backend — FastAPI Setup

### `backend/requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
python-multipart==0.0.9
pillow==10.3.0
reportlab==4.1.0
httpx==0.27.0
beautifulsoup4==4.12.3
python-dotenv==1.0.1
aiofiles==23.2.1
uuid==1.30
pydantic==2.7.0
```

### `backend/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import products, configs, upload, pdf
from database import engine, Base
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="iPromo 3D Configurator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(configs.router,  prefix="/api/configs",  tags=["Configs"])
app.include_router(upload.router,   prefix="/api/upload",   tags=["Upload"])
app.include_router(pdf.router,      prefix="/api/pdf",      tags=["PDF"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

### `backend/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./configurator.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 4. Database Models

### `backend/models.py`
```python
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from database import Base
import uuid

class ConfigSnapshot(Base):
    __tablename__ = "config_snapshots"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_url = Column(String, nullable=False)
    color       = Column(String, nullable=True)
    logo_url    = Column(String, nullable=True)   # relative path under /static
    logo_pos    = Column(JSON,   nullable=True)   # {"x": 0.5, "y": 0.3, "scale": 0.2}
    extra_data  = Column(JSON,   nullable=True)   # product name, price, etc.
    created_at  = Column(DateTime, server_default=func.now())
```

---

## 5. API Endpoints

### `backend/routers/products.py`
```python
from fastapi import APIRouter, HTTPException
import httpx
from bs4 import BeautifulSoup
import re

router = APIRouter()

COLORS = {
    "Aqua":    "#7ECECE",
    "Pink":    "#F08080",
    "Tan":     "#C4A882",
    "Black":   "#1A1A1A",
    "Silver":  "#B0B0B0",
    "White":   "#F5F5F5",
    "Navy":    "#1B2A6B",
    "Graphite":"#4A4A4A",
    "Purple":  "#6A0DAD",
    "Red":     "#CC2020",
}

@router.get("/")
async def get_product(url: str):
    """
    Scrape basic product info from iPromo URL.
    Falls back to hardcoded data for the Crosswind sweatshirt.
    """
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
        # 3D model path served from frontend /public/models/
        "model_path": "/models/quarter_zip.glb",
        "logo_zones": [
            {"id": "chest_left",  "label": "Left Chest",  "uv": [0.35, 0.55, 0.15, 0.15]},
            {"id": "chest_right", "label": "Right Chest", "uv": [0.55, 0.55, 0.15, 0.15]},
            {"id": "back_center", "label": "Back Center", "uv": [0.50, 0.50, 0.30, 0.30]},
        ]
    }
```

### `backend/routers/upload.py`
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
import aiofiles, os, uuid

router = APIRouter()
UPLOAD_DIR = "static/uploads"

@router.post("/logo")
async def upload_logo(file: UploadFile = File(...)):
    allowed = {"image/png", "image/jpeg", "image/svg+xml"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Only PNG, JPG, SVG allowed")

    ext = file.filename.rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())

    return {"logo_url": f"/static/uploads/{filename}"}
```

### `backend/routers/configs.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import ConfigSnapshot
from schemas import ConfigCreate, ConfigOut
import uuid

router = APIRouter()

@router.post("/", response_model=ConfigOut)
def save_config(data: ConfigCreate, db: Session = Depends(get_db)):
    config = ConfigSnapshot(
        id          = str(uuid.uuid4()),
        product_url = data.product_url,
        color       = data.color,
        logo_url    = data.logo_url,
        logo_pos    = data.logo_pos,
        extra_data  = data.extra_data,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config

@router.get("/{config_id}", response_model=ConfigOut)
def load_config(config_id: str, db: Session = Depends(get_db)):
    config = db.query(ConfigSnapshot).filter(ConfigSnapshot.id == config_id).first()
    if not config:
        raise HTTPException(404, "Config not found")
    return config
```

### `backend/schemas.py`
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ConfigCreate(BaseModel):
    product_url: str
    color:       Optional[str]
    logo_url:    Optional[str]
    logo_pos:    Optional[Dict[str, float]]
    extra_data:  Optional[Dict[str, Any]]

class ConfigOut(ConfigCreate):
    id:         str
    created_at: datetime
    class Config:
        from_attributes = True
```

### `backend/routers/pdf.py`
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
from utils.pdf_generator import generate_pdf

router = APIRouter()

class PDFRequest(BaseModel):
    product_name: str
    item_no:      str
    price:        str
    color:        str
    logo_url:     Optional[str]
    snapshot_url: Optional[str]   # base64 PNG of the canvas

@router.post("/download")
def download_pdf(req: PDFRequest):
    pdf_bytes = generate_pdf(req)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=ipromo_mockup.pdf"}
    )
```

### `backend/utils/pdf_generator.py`
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io, os, base64, tempfile

IPROMO_NAVY  = colors.HexColor("#1B2A6B")
IPROMO_TEAL  = colors.HexColor("#00B5B8")
IPROMO_LIGHT = colors.HexColor("#F4F6F9")

def generate_pdf(req) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.5*inch, leftMargin=0.5*inch,
        topMargin=0.5*inch,   bottomMargin=0.5*inch,
    )
    styles = getSampleStyleSheet()
    story  = []

    # ── Header bar ────────────────────────────────────────────────
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "ipromo_logo.png")
    header_data = []
    if os.path.exists(logo_path):
        header_data.append([Image(logo_path, width=1.8*inch, height=0.6*inch), ""])
    header_data.append([
        Paragraph(
            '<font color="#1B2A6B" size="18"><b>3D Product Mockup</b></font>',
            ParagraphStyle("h", alignment=TA_LEFT)
        ),
        Paragraph(
            '<font color="#00B5B8" size="9">iPromo — 27 Years of Branded Merchandise Excellence</font>',
            ParagraphStyle("sub", alignment=TA_LEFT)
        ),
    ])
    t = Table(header_data, colWidths=[4*inch, 3*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), IPROMO_NAVY),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [IPROMO_LIGHT]),
        ("GRID", (0,0), (-1,-1), 0, colors.white),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*inch))

    # ── 3D Canvas snapshot ────────────────────────────────────────
    if req.snapshot_url:
        # snapshot_url is a data:image/png;base64,... string
        b64 = req.snapshot_url.split(",", 1)[-1]
        img_bytes = base64.b64decode(b64)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name
        story.append(Image(tmp_path, width=4.5*inch, height=4.5*inch, hAlign="CENTER"))
        story.append(Spacer(1, 0.15*inch))

    # ── Product details table ─────────────────────────────────────
    detail_data = [
        ["Product Name", req.product_name],
        ["Item #",       req.item_no],
        ["Price Range",  req.price],
        ["Selected Color", req.color],
    ]
    dt = Table(detail_data, colWidths=[2*inch, 5*inch])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), IPROMO_NAVY),
        ("TEXTCOLOR",  (0,0), (0,-1), colors.white),
        ("BACKGROUND", (1,0), (1,-1), IPROMO_LIGHT),
        ("GRID", (0,0), (-1,-1), 0.5, colors.white),
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 10),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0), (-1,-1), 7),
    ]))
    story.append(dt)
    story.append(Spacer(1, 0.25*inch))

    # ── Footer ────────────────────────────────────────────────────
    footer_style = ParagraphStyle(
        "footer", fontSize=8, textColor=colors.grey, alignment=TA_CENTER
    )
    story.append(Paragraph(
        "Generated by iPromo 3D Configurator · www.ipromo.com · 888.994.7766",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()
```

---

## 6. 3D Model Pipeline

### Getting the GLB model
You need a `.glb` 3D model of the quarter-zip sweatshirt. Use one of these approaches:

**Option A — Free (Recommended for prototype):**
1. Download a free hoodie/quarter-zip base mesh from [Sketchfab](https://sketchfab.com/search?q=quarter+zip&type=models&features=downloadable) (filter: free, CC license)
2. Open in [Blender](https://www.blender.org/) (free)
3. Adjust shape to match sweatshirt profile (add quarter-zip detail to collar)
4. UV-unwrap cleanly — the chest and back panels need distinct UV islands for logo placement
5. Export as `.glb` with embedded textures
6. Place at `frontend/public/models/quarter_zip.glb`

**Option B — Paid production quality:**
- Commission a 3D artist on Fiverr (~$50–150) for a photo-realistic GLB  
- Specify: separate material slots for body (colorable), zipper, cuffs, and a `LogoDecal` mesh panel

**UV Layout Requirements:**
```
UV Island Layout (normalized 0–1):
┌─────────────────────────┐
│  BACK (0.5,0.5) large   │
│                         │
│  FRONT-RIGHT  FRONT-LEFT│
│  (0.35,0.55)  (0.55,0.55│
└─────────────────────────┘
```
- Body material slot name: **"Body"** (this is what we tint by color)  
- Logo decal mesh: separate plane mesh called **"LogoPlane_Chest"** parented to body  

---

## 7. Frontend — React + Vite Setup

### `frontend/package.json` — key dependencies
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "@react-three/fiber": "^8.16.8",
    "@react-three/drei": "^9.105.6",
    "three": "^0.165.0",
    "zustand": "^4.5.2",
    "axios": "^1.7.2",
    "react-dropzone": "^14.2.3",
    "react-hot-toast": "^2.4.1",
    "lucide-react": "^0.383.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.4",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "vite": "^5.2.12"
  }
}
```

### `frontend/vite.config.js`
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    }
  }
})
```

### `frontend/tailwind.config.js`
```js
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "ipromo-navy":  "#1B2A6B",
        "ipromo-teal":  "#00B5B8",
        "ipromo-light": "#F4F6F9",
      }
    }
  },
  plugins: []
}
```

---

## 8. Three.js Scene & Viewer Component

### `frontend/src/components/Viewer3D.jsx`
```jsx
import { Suspense, useRef, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import {
  OrbitControls, useGLTF, Environment,
  ContactShadows, Html, useTexture
} from '@react-three/drei'
import * as THREE from 'three'
import { useConfigurator } from '../store/configuratorStore'

// ─── Sweatshirt model ───────────────────────────────────────────
function SweatshirtModel() {
  const { scene } = useGLTF('/models/quarter_zip.glb')
  const { selectedColor, logoTexture, logoZone, logoTransform } = useConfigurator()
  const meshRef = useRef()

  // Live color update
  useEffect(() => {
    scene.traverse((child) => {
      if (child.isMesh && child.material?.name === 'Body') {
        child.material = child.material.clone()
        child.material.color.set(selectedColor)
        child.material.needsUpdate = true
      }
    })
  }, [selectedColor, scene])

  // Logo decal via canvas texture on LogoPlane_Chest mesh
  useEffect(() => {
    if (!logoTexture) return
    scene.traverse((child) => {
      if (child.isMesh && child.name === 'LogoPlane_Chest') {
        const tex = new THREE.TextureLoader().load(logoTexture)
        tex.colorSpace = THREE.SRGBColorSpace
        child.material = new THREE.MeshStandardMaterial({
          map: tex,
          transparent: true,
          alphaTest: 0.05,
          depthWrite: false,
          roughness: 0.8,
          metalness: 0.0,
        })
      }
    })
  }, [logoTexture, scene])

  return (
    <primitive
      ref={meshRef}
      object={scene}
      scale={1.4}
      position={[0, -1.0, 0]}
      castShadow
      receiveShadow
    />
  )
}

// ─── Loading spinner ────────────────────────────────────────────
function Loader() {
  return (
    <Html center>
      <div className="flex flex-col items-center gap-2 text-ipromo-navy">
        <div className="w-10 h-10 border-4 border-ipromo-teal border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium">Loading 3D model…</span>
      </div>
    </Html>
  )
}

// ─── Main exported component ────────────────────────────────────
export default function Viewer3D({ onCapture }) {
  const gl = useRef()

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden bg-gradient-to-b from-slate-100 to-slate-200">
      <Canvas
        ref={gl}
        camera={{ position: [0, 0.5, 3.2], fov: 45 }}
        shadows
        gl={{ preserveDrawingBuffer: true }}   // ← needed for PDF screenshot
        onCreated={({ gl: renderer }) => { gl.current = renderer }}
      >
        {/* Lighting rig — soft studio look */}
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[5, 10, 5]}
          intensity={1.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />
        <directionalLight position={[-4, 5, -3]} intensity={0.4} color="#cce0ff" />
        <pointLight position={[0, 3, 2]} intensity={0.3} color="#fff8f0" />

        {/* HDRI environment for realistic reflections */}
        <Environment preset="studio" />

        {/* Model */}
        <Suspense fallback={<Loader />}>
          <SweatshirtModel />
        </Suspense>

        {/* Ground shadow */}
        <ContactShadows
          position={[0, -1.8, 0]}
          opacity={0.5}
          scale={6}
          blur={2.5}
          far={4}
        />

        {/* Camera controls — rotate on drag */}
        <OrbitControls
          enablePan={false}
          minPolarAngle={Math.PI / 6}
          maxPolarAngle={Math.PI * 0.8}
          minDistance={1.8}
          maxDistance={5}
          autoRotate
          autoRotateSpeed={0.6}
        />
      </Canvas>

      {/* Capture button (used by PDF) */}
      <button
        className="absolute bottom-4 right-4 bg-ipromo-navy text-white px-3 py-1.5 rounded-lg text-xs opacity-70 hover:opacity-100"
        onClick={() => {
          if (gl.current) {
            const dataUrl = gl.current.domElement.toDataURL('image/png')
            onCapture?.(dataUrl)
          }
        }}
      >
        📸 Capture
      </button>
    </div>
  )
}
```

---

## 9. Color Switcher Component

### `frontend/src/components/ColorPicker.jsx`
```jsx
import { useConfigurator } from '../store/configuratorStore'

const COLOR_MAP = {
  "Aqua":    "#7ECECE",
  "Pink":    "#F08080",
  "Tan":     "#C4A882",
  "Black":   "#1A1A1A",
  "Silver":  "#B0B0B0",
  "White":   "#F5F5F5",
  "Navy":    "#1B2A6B",
  "Graphite":"#4A4A4A",
  "Purple":  "#6A0DAD",
  "Red":     "#CC2020",
}

export default function ColorPicker() {
  const { selectedColor, setColor } = useConfigurator()

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
      <h3 className="text-sm font-semibold text-ipromo-navy mb-3">
        1. Choose Color
        <span className="ml-2 text-ipromo-teal font-normal">
          {Object.entries(COLOR_MAP).find(([,v]) => v === selectedColor)?.[0] ?? ''}
        </span>
      </h3>
      <div className="flex flex-wrap gap-2">
        {Object.entries(COLOR_MAP).map(([name, hex]) => (
          <button
            key={name}
            title={name}
            onClick={() => setColor(hex)}
            className={`
              w-8 h-8 rounded-full border-2 transition-all duration-150 shadow-sm
              hover:scale-110
              ${selectedColor === hex
                ? 'border-ipromo-teal scale-110 ring-2 ring-ipromo-teal ring-offset-1'
                : 'border-white'}
            `}
            style={{ backgroundColor: hex }}
          />
        ))}
      </div>
    </div>
  )
}
```

---

## 10. Logo Upload & UV Mapping

### `frontend/src/components/LogoUploader.jsx`
```jsx
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { Upload, X, Move } from 'lucide-react'

export default function LogoUploader() {
  const { setLogoTexture, logoTransform, setLogoTransform } = useConfigurator()
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(async (files) => {
    const file = files[0]
    if (!file) return
    setPreview(URL.createObjectURL(file))
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post('/api/upload/logo', form)
      setLogoTexture(data.logo_url)          // stored URL → Three.js loads it
      toast.success('Logo applied to model!')
    } catch {
      toast.error('Upload failed — try again')
    } finally {
      setUploading(false)
    }
  }, [setLogoTexture])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/png': [], 'image/jpeg': [], 'image/svg+xml': [] },
    maxFiles: 1,
    maxSize: 5_000_000,
  })

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-4">
      <h3 className="text-sm font-semibold text-ipromo-navy">2. Upload Your Logo</h3>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-6 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive
            ? 'border-ipromo-teal bg-teal-50'
            : 'border-slate-200 hover:border-ipromo-teal'}
        `}
      >
        <input {...getInputProps()} />
        {preview ? (
          <div className="flex items-center justify-center gap-3">
            <img src={preview} alt="logo" className="h-12 object-contain rounded" />
            <button
              className="text-slate-400 hover:text-red-400"
              onClick={(e) => { e.stopPropagation(); setPreview(null); setLogoTexture(null) }}
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <>
            <Upload className="mx-auto mb-2 text-ipromo-teal" size={28} />
            <p className="text-xs text-slate-500">
              {uploading ? 'Uploading…' : 'Drag & drop PNG / JPG / SVG or click to browse'}
            </p>
          </>
        )}
      </div>

      {/* Logo position & scale sliders */}
      {preview && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
            <Move size={12} /> Position & Size
          </label>
          {[
            { key: 'x', label: 'Left ↔ Right', min: -0.5, max: 0.5 },
            { key: 'y', label: 'Up ↕ Down',    min: -0.5, max: 0.5 },
            { key: 's', label: 'Scale',         min: 0.05, max: 0.5 },
          ].map(({ key, label, min, max }) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-xs text-slate-400 w-20">{label}</span>
              <input
                type="range" min={min} max={max} step={0.01}
                value={logoTransform[key] ?? (key === 's' ? 0.18 : 0)}
                onChange={(e) =>
                  setLogoTransform({ ...logoTransform, [key]: parseFloat(e.target.value) })
                }
                className="flex-1 accent-ipromo-teal"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

---

## 11. Share Link Feature

### `frontend/src/components/ShareButton.jsx`
```jsx
import { useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { Link2, Copy, Check } from 'lucide-react'

export default function ShareButton() {
  const { selectedColor, logoTexture, logoTransform, productUrl, productData } = useConfigurator()
  const [shareUrl, setShareUrl] = useState('')
  const [copied, setCopied]     = useState(false)
  const [loading, setLoading]   = useState(false)

  const handleShare = async () => {
    setLoading(true)
    try {
      const { data } = await axios.post('/api/configs/', {
        product_url: productUrl,
        color:       selectedColor,
        logo_url:    logoTexture,
        logo_pos:    logoTransform,
        extra_data:  productData,
      })
      const url = `${window.location.origin}/share/${data.id}`
      setShareUrl(url)
      await navigator.clipboard.writeText(url)
      setCopied(true)
      toast.success('Link copied to clipboard!')
      setTimeout(() => setCopied(false), 3000)
    } catch {
      toast.error('Could not generate share link')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-2">
      <button
        onClick={handleShare}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 bg-ipromo-navy
                   text-white py-2.5 px-4 rounded-xl font-medium text-sm
                   hover:bg-blue-900 transition-colors disabled:opacity-60"
      >
        <Link2 size={16} />
        {loading ? 'Generating…' : 'Get Shareable Link'}
      </button>

      {shareUrl && (
        <div className="flex items-center gap-2 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
          <span className="flex-1 text-xs text-slate-600 truncate">{shareUrl}</span>
          <button
            onClick={() => { navigator.clipboard.writeText(shareUrl); setCopied(true) }}
            className="text-ipromo-teal hover:text-teal-700 flex-shrink-0"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        </div>
      )}
    </div>
  )
}
```

### `frontend/src/pages/SharedViewPage.jsx`
```jsx
import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { useConfigurator } from '../store/configuratorStore'
import Viewer3D from '../components/Viewer3D'
import ProductInfo from '../components/ProductInfo'

export default function SharedViewPage() {
  const { uuid }  = useParams()
  const { setColor, setLogoTexture, setLogoTransform, setProductData } = useConfigurator()

  useEffect(() => {
    axios.get(`/api/configs/${uuid}`).then(({ data }) => {
      if (data.color)    setColor(data.color)
      if (data.logo_url) setLogoTexture(data.logo_url)
      if (data.logo_pos) setLogoTransform(data.logo_pos)
      if (data.extra_data) setProductData(data.extra_data)
    })
  }, [uuid])

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      {/* Banner */}
      <div className="bg-ipromo-navy text-white text-center py-2 text-sm">
        👀 You're viewing a custom iPromo product mockup — 
        <a href="https://www.ipromo.com" className="text-ipromo-teal underline ml-1">
          Order yours at iPromo.com
        </a>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-[500px] relative">
            <Viewer3D />
          </div>
          <ProductInfo readOnly />
        </div>
      </div>
    </div>
  )
}
```

---

## 12. PDF Download Feature

### `frontend/src/components/PDFDownloadButton.jsx`
```jsx
import { useState, useRef } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { FileDown } from 'lucide-react'

export default function PDFDownloadButton({ canvasRef }) {
  const { selectedColor, productData } = useConfigurator()
  const [loading, setLoading] = useState(false)
  // canvasRef.current is the Three.js WebGLRenderer domElement

  const handleDownload = async () => {
    setLoading(true)
    try {
      // Capture canvas as base64 PNG
      let snapshot = null
      if (canvasRef?.current) {
        snapshot = canvasRef.current.toDataURL('image/png')
      }

      const colorName = Object.entries({
        "#7ECECE":"Aqua","#F08080":"Pink","#C4A882":"Tan",
        "#1A1A1A":"Black","#B0B0B0":"Silver","#F5F5F5":"White",
        "#1B2A6B":"Navy","#4A4A4A":"Graphite","#6A0DAD":"Purple","#CC2020":"Red"
      }).find(([hex]) => hex === selectedColor)?.[1] ?? selectedColor

      const { data } = await axios.post('/api/pdf/download', {
        product_name: productData?.name  ?? 'Crosswind Quarter Zip Sweatshirt',
        item_no:      productData?.item_no ?? 'IP-276-9359',
        price:        productData?.price   ?? '$43.99 – $51.99',
        color:        colorName,
        snapshot_url: snapshot,
      }, { responseType: 'blob' })

      const url = URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
      const a   = document.createElement('a')
      a.href    = url
      a.download = 'ipromo_mockup.pdf'
      a.click()
      toast.success('PDF downloaded!')
    } catch {
      toast.error('PDF generation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className="w-full flex items-center justify-center gap-2
                 bg-ipromo-teal text-white py-2.5 px-4 rounded-xl
                 font-medium text-sm hover:bg-teal-600 transition-colors
                 disabled:opacity-60"
    >
      <FileDown size={16} />
      {loading ? 'Generating PDF…' : 'Download PDF Mockup'}
    </button>
  )
}
```

---

## 13. iPromo Branding & UI Polish

### `frontend/src/components/Navbar.jsx`
```jsx
export default function Navbar() {
  return (
    <header className="bg-ipromo-navy text-white px-6 py-3 flex items-center justify-between shadow-lg">
      <div className="flex items-center gap-3">
        {/* Replace with actual iPromo logo from /assets/ipromo_logo.png */}
        <img src="/ipromo_logo.png" alt="iPromo" className="h-8 object-contain" />
        <div className="hidden sm:block border-l border-white/20 pl-3">
          <p className="text-xs text-white/60">27th Anniversary</p>
          <p className="text-sm font-semibold">3D Product Configurator</p>
        </div>
      </div>
      <a
        href="https://www.ipromo.com"
        target="_blank"
        className="text-ipromo-teal text-xs underline hover:text-white transition-colors"
      >
        Visit iPromo.com →
      </a>
    </header>
  )
}
```

### `frontend/src/pages/ConfiguratorPage.jsx`
```jsx
import { useRef, useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Viewer3D from '../components/Viewer3D'
import ColorPicker from '../components/ColorPicker'
import LogoUploader from '../components/LogoUploader'
import ShareButton from '../components/ShareButton'
import PDFDownloadButton from '../components/PDFDownloadButton'
import ProductInfo from '../components/ProductInfo'
import { useConfigurator } from '../store/configuratorStore'
import axios from 'axios'
import toast, { Toaster } from 'react-hot-toast'

export default function ConfiguratorPage() {
  const [searchParams] = useSearchParams()
  const productUrl = searchParams.get('url') ?? 'https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html'
  const { setProductData, setProductUrl } = useConfigurator()
  const canvasRef = useRef(null)

  useEffect(() => {
    setProductUrl(productUrl)
    axios.get(`/api/products/?url=${encodeURIComponent(productUrl)}`)
      .then(({ data }) => setProductData(data))
      .catch(() => toast.error('Could not load product data'))
  }, [productUrl])

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      <Navbar />
      <Toaster position="top-right" />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6
                        grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">
        {/* ── 3D Viewer ── */}
        <div className="relative h-[520px] lg:h-auto lg:min-h-[580px]">
          <Viewer3D
            canvasRef={canvasRef}
            onCapture={(dataUrl) => { /* stored for PDF */ }}
          />
        </div>

        {/* ── Control panel ── */}
        <aside className="flex flex-col gap-4">
          <ProductInfo />
          <ColorPicker />
          <LogoUploader />

          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-sm font-semibold text-ipromo-navy">3. Share & Export</h3>
            <ShareButton />
            <PDFDownloadButton canvasRef={canvasRef} />
          </div>

          {/* Pricing table */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
            <h3 className="text-sm font-semibold text-ipromo-navy mb-3">Quantity Pricing</h3>
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-ipromo-navy text-white">
                  {['12–23','24–47','48–95','96–143','144+'].map(q =>
                    <th key={q} className="py-1.5 px-2 text-center">{q}</th>
                  )}
                </tr>
              </thead>
              <tbody>
                <tr className="bg-slate-50">
                  {['$51.99','$49.99','$47.99','$45.99','$43.99'].map(p =>
                    <td key={p} className="py-1.5 px-2 text-center font-medium">{p}</td>
                  )}
                </tr>
              </tbody>
            </table>
            <p className="text-xs text-slate-400 mt-2">Setup Charge: $75.00 · Min qty: 12</p>
          </div>
        </aside>
      </main>
    </div>
  )
}
```

---

## 14. Global State Store

### `frontend/src/store/configuratorStore.js`
```js
import { create } from 'zustand'

export const useConfigurator = create((set) => ({
  productUrl:     '',
  productData:    null,
  selectedColor:  '#7ECECE',   // default Aqua
  logoTexture:    null,
  logoTransform:  { x: 0, y: 0, s: 0.18 },

  setProductUrl:    (url)  => set({ productUrl: url }),
  setProductData:   (data) => set({ productData: data }),
  setColor:         (hex)  => set({ selectedColor: hex }),
  setLogoTexture:   (url)  => set({ logoTexture: url }),
  setLogoTransform: (t)    => set({ logoTransform: t }),
}))
```

---

## 15. Environment Variables

### `backend/.env`
```
DATABASE_URL=sqlite:///./configurator.db
# For production: DATABASE_URL=postgresql://user:pass@db:5432/configurator
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### `frontend/.env`
```
VITE_API_BASE=http://localhost:8000
```

---

## 16. Docker Compose (Optional)

### `docker-compose.yml`
```yaml
version: "3.9"
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/static:/app/static
    environment:
      - DATABASE_URL=sqlite:///./data/configurator.db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:80"
    depends_on:
      - backend
```

### `backend/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## 17. Step-by-Step Build Order for the IDE Agent

Follow this **exact order** to avoid dependency issues:

### Phase 1 — Backend Foundation
```
Step 1.  Create backend/ folder, copy requirements.txt, run: pip install -r requirements.txt
Step 2.  Create database.py, models.py, schemas.py
Step 3.  Create main.py with CORS, StaticFiles, router includes
Step 4.  Create routers/upload.py — test with: POST /api/upload/logo
Step 5.  Create routers/products.py with static fallback data
Step 6.  Create routers/configs.py, run: POST /api/configs/ then GET /api/configs/{id}
Step 7.  Create utils/pdf_generator.py, routers/pdf.py
Step 8.  Download iPromo 27th anniversary logo from https://www.ipromo.com
         Save as backend/assets/ipromo_logo.png
Step 9.  Run: uvicorn main:app --reload  →  confirm /health returns {"status":"ok"}
```

### Phase 2 — 3D Model
```
Step 10. Download a free quarter-zip GLB from Sketchfab (CC license)
          OR create a simple placeholder sweatshirt shape in Blender
Step 11. In Blender:
          a. Split materials: "Body" (tintable), "Zipper", "Cuffs"
          b. Add a flat mesh plane on left chest, name it "LogoPlane_Chest"
          c. UV-unwrap the chest plane cleanly (0–1 UV space)
          d. Export: File → Export → glTF 2.0 (.glb), check "Apply Modifiers"
Step 12. Place file at: frontend/public/models/quarter_zip.glb
```

### Phase 3 — Frontend Core
```
Step 13. Create frontend/ with: npm create vite@latest . -- --template react
Step 14. Install all dependencies from package.json
Step 15. Configure tailwind.config.js, postcss.config.js, vite.config.js
Step 16. Create store/configuratorStore.js (Zustand)
Step 17. Create App.jsx with react-router-dom routes:
          /           → ConfiguratorPage (with ?url= query param)
          /share/:uuid → SharedViewPage
Step 18. Create components/Viewer3D.jsx — test: does the GLB load and rotate?
Step 19. Create components/ColorPicker.jsx — test: does color update on model live?
Step 20. Create components/LogoUploader.jsx — test: upload PNG, see on chest
Step 21. Create components/ShareButton.jsx — test: generates /share/:uuid link
Step 22. Create pages/SharedViewPage.jsx — test: open share link, see correct config
Step 23. Create components/PDFDownloadButton.jsx — test: PDF downloads with mockup
Step 24. Create components/Navbar.jsx with iPromo logo
Step 25. Wire everything in ConfiguratorPage.jsx
```

### Phase 4 — Polish & QA
```
Step 26. Add react-hot-toast for all error/success states
Step 27. Add loading skeletons/spinners for initial 3D model load
Step 28. Mobile responsive: test on 375px width — viewer stacks above controls
Step 29. Test full flow: URL input → color pick → logo upload → share link → PDF
Step 30. Set autoRotate=false on OrbitControls once user grabs model
Step 31. Add meta tags to SharedViewPage (og:image, og:title) for social previews
Step 32. Optionally add URL input field on ConfiguratorPage so any iPromo URL
         can be pasted and the configurator reloads with that product's data
```

---

## Quick-Start Commands

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
# Open: http://localhost:5173/?url=https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html
```

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| 3D renderer | `@react-three/fiber` + `three.js` | Full control, no vendor lock-in |
| State management | Zustand | Minimal boilerplate, SSR-ready |
| PDF generation | ReportLab (Python) | Pixel-perfect, no headless browser needed |
| Logo UV mapping | Separate LogoPlane mesh | Cleanest approach; no shader math in React |
| Share links | UUID → SQLite | No auth needed, instant |
| Color change | Material clone + `color.set()` | Prevents shared material mutation |
| Logo lighting | `MeshStandardMaterial` with `roughness=0.8` | Logo appears to be printed on fabric |
| PDF canvas capture | `preserveDrawingBuffer: true` on WebGL | Required for `toDataURL()` |

---

*Built for iPromo — 27 Years of Branded Merchandise Excellence*  
*www.ipromo.com · 888.994.7766*