from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import products, configs, upload, pdf
from database import engine, Base
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="iPromo 3D Configurator API", version="1.0.0")

raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins.strip() == "" or raw_origins.strip() == "*":
    # Wildcard — allow all origins (dev mode or not yet configured)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # must be False when origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Explicit origins list — safe to use allow_credentials=True
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
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
