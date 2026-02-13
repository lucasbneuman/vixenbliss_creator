from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base, GUID

class Avatar(Base):
    __tablename__ = "avatars"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    stage = Column(String(50), nullable=False, default="draft")
    base_image_url = Column(Text)
    lora_model_id = Column(GUID, ForeignKey("lora_models.id"), nullable=True)
    lora_weights_url = Column(Text)
    niche = Column(String(100))
    aesthetic_style = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    meta_data = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="avatars")
    lora_model = relationship("LoRAModel", back_populates="avatars")
    identity_components = relationship("IdentityComponent", back_populates="avatar", cascade="all, delete-orphan")
    content_pieces = relationship("ContentPiece", back_populates="avatar", cascade="all, delete-orphan")
