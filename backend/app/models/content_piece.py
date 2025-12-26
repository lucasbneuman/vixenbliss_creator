from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class ContentPiece(Base):
    __tablename__ = "content_pieces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id", ondelete="CASCADE"), nullable=False)
    content_type = Column(String(50), nullable=False)  # image, video
    access_tier = Column(String(20), nullable=False, default="capa1")  # capa1, capa2, capa3
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    hook_text = Column(Text)
    metadata = Column(JSONB, default={})
    safety_rating = Column(String(20))  # safe, suggestive, borderline
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True))

    # Relationships
    avatar = relationship("Avatar", back_populates="content_pieces")
