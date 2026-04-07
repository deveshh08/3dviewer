import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import products, configs, upload, pdf
from database import engine, Base

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(title="iPromo 3D Configurator API", version="1.0.0")

raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins.strip() == "" or raw_origins.strip() == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Always use absolute path so StaticFiles works regardless of launch directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "static"))
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(configs.router,  prefix="/api/configs",  tags=["Configs"])
app.include_router(upload.router,   prefix="/api/upload",   tags=["Upload"])
app.include_router(pdf.router,      prefix="/api/pdf",      tags=["PDF"])

@app.get("/health")
def health():
    return {"status": "ok"}
