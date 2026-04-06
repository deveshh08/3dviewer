from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import aiofiles, os, uuid
import httpx

router = APIRouter()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
DATA_DIR    = os.getenv("DATA_DIR", os.path.join(BACKEND_DIR, "static"))
UPLOAD_DIR  = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY", "k5jZCq4ctcmcJKa789oi7at1")

@router.post("/logo")
async def upload_logo(file: UploadFile = File(...), request: Request = None):
    allowed = {"image/png", "image/jpeg", "image/svg+xml"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Only PNG, JPG, SVG allowed")

    raw = await file.read()

    if file.content_type == "image/svg+xml":
        ext, output_bytes = file.filename.rsplit(".", 1)[-1], raw
    else:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": (file.filename, raw, file.content_type)},
                data={"size": "auto"},
                headers={"X-Api-Key": REMOVE_BG_API_KEY},
            )
        if resp.status_code != 200:
            raise HTTPException(502, f"remove.bg error: {resp.text}")
        ext, output_bytes = "png", resp.content

    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(path, "wb") as f:
        await f.write(output_bytes)

    public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if not public_base:
        public_base = str(request.base_url).rstrip("/")
    return {"logo_url": f"{public_base}/static/uploads/{filename}"}
