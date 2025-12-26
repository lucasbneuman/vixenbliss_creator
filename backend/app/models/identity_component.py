from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from app.database import Base

class IdentityComponent(Base):
    __tablename__ = "identity_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id", ondelete="CASCADE"), nullable=False)
    component_type = Column(String(50), nullable=False)  # bio, location, interests, personality
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, default={})
    embedding = Column(Vector(1536))  # OpenAI ada-002 embeddings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    avatar = relationship("Avatar", back_populates="identity_components")
