from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base, GUID

class ContentPiece(Base):
    __tablename__ = "content_pieces"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    avatar_id = Column(GUID, ForeignKey("avatars.id", ondelete="CASCADE"), nullable=False)
    content_type = Column(String(50), nullable=False)  # image, video
    access_tier = Column(String(20), nullable=False, default="capa1")  # capa1, capa2, capa3
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    hook_text = Column(Text)
    meta_data = Column(JSON, default=dict)
    safety_rating = Column(String(20))  # safe, suggestive, borderline

    # Premium content fields (E07-001)
    explicitness_level = Column(Integer, nullable=True)  # 1-10 (1=soft, 10=explicit)
    price_usd = Column(Float, nullable=True)  # Price for premium packs

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True))

    # Relationships
    avatar = relationship("Avatar", back_populates="content_pieces")
