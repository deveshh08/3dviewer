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
