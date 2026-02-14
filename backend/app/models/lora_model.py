from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base, GUID


class LoRAModel(Base):
    __tablename__ = "lora_models"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    base_model = Column(String(255))
    lora_weights_url = Column(Text, nullable=False)
    preview_image_url = Column(Text)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    meta_data = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="lora_models")
    avatars = relationship("Avatar", back_populates="lora_model")
