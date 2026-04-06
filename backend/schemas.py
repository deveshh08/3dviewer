from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ConfigCreate(BaseModel):
    product_url: str
    color:       Optional[str] = None
    logo_url:    Optional[str] = None
    logo_pos:    Optional[Dict[str, float]] = None
    extra_data:  Optional[Dict[str, Any]] = None

class ConfigOut(ConfigCreate):
    id:         str
    created_at: datetime
    class Config:
        from_attributes = True
