from sqlalchemy import Column, String, JSON, DateTime, Integer, ForeignKey
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


class ProductImage(Base):
    __tablename__ = "product_images"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    product_url = Column(String, nullable=False, index=True)
    image_url   = Column(String, nullable=False)
    position    = Column(Integer, nullable=False)   # order within the product
    scraped_at  = Column(DateTime, server_default=func.now())


class ProductGLB(Base):
    __tablename__ = "product_glbs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    product_url = Column(String, nullable=False, unique=True, index=True)
    glb_url     = Column(String, nullable=False)
    task_id     = Column(String, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
