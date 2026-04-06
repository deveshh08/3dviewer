from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from database import Base
import uuid

class ConfigSnapshot(Base):
    __tablename__ = "config_snapshots"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_url = Column(String, nullable=True)
    color       = Column(String, nullable=True)
    logo_url    = Column(String, nullable=True)
    logo_pos    = Column(JSON,   nullable=True)
    extra_data  = Column(JSON,   nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
