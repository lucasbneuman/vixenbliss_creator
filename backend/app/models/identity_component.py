from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base, GUID

class IdentityComponent(Base):
    __tablename__ = "identity_components"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    avatar_id = Column(GUID, ForeignKey("avatars.id", ondelete="CASCADE"), nullable=False)
    component_type = Column(String(50), nullable=False)  # bio, location, interests, personality
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, default=dict)
    # embedding = Column(Vector(1536))  # OpenAI ada-002 embeddings - Disabled for SQLite compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    avatar = relationship("Avatar", back_populates="identity_components")
