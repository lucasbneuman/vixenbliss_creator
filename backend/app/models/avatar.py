from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Avatar(Base):
    __tablename__ = "avatars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    stage = Column(String(50), nullable=False, default="draft")
    base_image_url = Column(Text)
    lora_model_id = Column(String(255))
    lora_weights_url = Column(Text)
    niche = Column(String(100))
    aesthetic_style = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSONB, default={})

    # Relationships
    user = relationship("User", back_populates="avatars")
    identity_components = relationship("IdentityComponent", back_populates="avatar", cascade="all, delete-orphan")
    content_pieces = relationship("ContentPiece", back_populates="avatar", cascade="all, delete-orphan")
