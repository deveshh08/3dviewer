from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import aiofiles, os, uuid

router = APIRouter()

# Resolve to backend/static/uploads — works regardless of uvicorn launch directory
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))          # .../backend/routers
BACKEND_DIR = os.path.dirname(BASE_DIR)                           # .../backend
UPLOAD_DIR  = os.path.join(BACKEND_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/logo")
async def upload_logo(file: UploadFile = File(...), request: Request = None):
    allowed = {"image/png", "image/jpeg", "image/svg+xml"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Only PNG, JPG, SVG allowed")

    ext = file.filename.rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())

    base = str(request.base_url).rstrip("/")
    return {"logo_url": f"{base}/static/uploads/{filename}"}
