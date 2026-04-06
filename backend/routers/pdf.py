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
    logo_url:     Optional[str] = None
    snapshot_url: Optional[str] = None

@router.post("/download")
def download_pdf(req: PDFRequest):
    pdf_bytes = generate_pdf(req)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=ipromo_mockup.pdf"}
    )
