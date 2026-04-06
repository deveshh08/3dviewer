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
