"""
Social Account Model
Stores connected social media accounts (Instagram, TikTok)
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base, GUID


class Platform(str, enum.Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    ONLYFANS = "onlyfans"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SHADOWBANNED = "shadowbanned"
    RATE_LIMITED = "rate_limited"
    DISCONNECTED = "disconnected"


class SocialAccount(Base):
    """Social media account connection"""

    __tablename__ = "social_accounts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Account details
    user_id = Column(GUID, nullable=False, index=True)
    avatar_id = Column(GUID, nullable=True, index=True)
    platform = Column(SQLEnum(Platform), nullable=False, index=True)

    # Platform-specific identifiers
    platform_user_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    display_name = Column(String, nullable=True)

    # OAuth tokens (encrypted)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Account health
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE, index=True)
    health_score = Column(String, default="100")  # 0-100
    last_health_check = Column(DateTime, nullable=True)

    # Platform metadata
    meta_data = Column(JSON, default=dict)  # Followers, verified status, etc.

    # Settings
    auto_post_enabled = Column(Boolean, default=True)
    posting_schedule = Column(JSON, default=dict)  # Timezone, hours, frequency

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_post_at = Column(DateTime, nullable=True)

    # Relationship
    scheduled_posts = relationship("ScheduledPost", back_populates="social_account")

    def __repr__(self):
        return f"<SocialAccount {self.platform.value}:{self.username}>"

    def is_token_expired(self):
        """Check if access token is expired"""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() >= self.token_expires_at

    def is_healthy(self):
        """Check if account is healthy for posting"""
        return self.status == AccountStatus.ACTIVE and int(self.health_score) >= 70


class ScheduledPost(Base):
    """Scheduled social media post"""

    __tablename__ = "scheduled_posts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Relations
    social_account_id = Column(GUID, ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    content_piece_id = Column(GUID, nullable=False)
    avatar_id = Column(GUID, nullable=False, index=True)

    # Scheduling
    scheduled_time = Column(DateTime, nullable=False, index=True)
    timezone = Column(String, default="UTC")

    # Content
    caption = Column(String, nullable=True)
    hashtags = Column(JSON, default=list)
    media_urls = Column(JSON, default=list)

    # Status
    status = Column(String, default="pending", index=True)  # pending, published, failed, cancelled
    published_at = Column(DateTime, nullable=True)

    # Publishing result
    platform_post_id = Column(String, nullable=True)
    platform_url = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    retry_count = Column(String, default="0")

    # Metadata
    meta_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    social_account = relationship("SocialAccount", back_populates="scheduled_posts")

    def __repr__(self):
        return f"<ScheduledPost {self.id} @ {self.scheduled_time}>"

    def can_retry(self):
        """Check if post can be retried"""
        return self.status == "failed" and int(self.retry_count) < 3
