from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import os, uuid, io
from PIL import Image
from rembg import remove

router = APIRouter()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
DATA_DIR    = os.getenv("DATA_DIR", os.path.join(BACKEND_DIR, "static"))
UPLOAD_DIR  = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/logo")
async def upload_logo(file: UploadFile = File(...), request: Request = None):
    allowed = {"image/png", "image/jpeg", "image/svg+xml"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Only PNG, JPG, SVG allowed")

    raw = await file.read()

    # SVGs are kept as-is; raster images get background removed
    if file.content_type == "image/svg+xml":
        ext, output_bytes = "svg", raw
    else:
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        result = remove(img)                  # returns RGBA PIL image
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        ext, output_bytes = "png", buf.getvalue()

    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(output_bytes)

    public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if not public_base:
        public_base = str(request.base_url).rstrip("/")
    return {"logo_url": f"{public_base}/static/uploads/{filename}"}
