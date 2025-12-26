"""
Conversation Models
Database models for chatbot lead generation system (ÉPICA 06)
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, Float, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ChannelType(str, enum.Enum):
    """Communication channel type"""
    INSTAGRAM_DM = "instagram_dm"
    TIKTOK_DM = "tiktok_dm"
    TWITTER_DM = "twitter_dm"
    ONLYFANS_DM = "onlyfans_dm"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


class FunnelStage(str, enum.Enum):
    """3-stage funnel progression (E06-002)"""
    LEAD_MAGNET = "lead_magnet"  # Initial contact, hook, value proposition
    QUALIFICATION = "qualification"  # Questions, engagement, interest validation
    CONVERSION = "conversion"  # Offer, pricing, close


class LeadQualification(str, enum.Enum):
    """Lead qualification status (E06-003)"""
    COLD_LEAD = "cold_lead"  # Score 0-40
    WARM_LEAD = "warm_lead"  # Score 41-70
    HOT_LEAD = "hot_lead"  # Score 71-100


class SenderType(str, enum.Enum):
    """Message sender type"""
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class Conversation(Base):
    """
    DM conversation with a lead (E06-001)
    Tracks entire conversation lifecycle across platforms
    """

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relations
    avatar_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    social_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Platform details
    platform = Column(String, nullable=False, index=True)  # instagram, tiktok, twitter
    channel_type = Column(SQLEnum(ChannelType), nullable=False, index=True)
    platform_conversation_id = Column(String, nullable=False, unique=True)  # Platform's conversation ID

    # Lead information
    lead_username = Column(String, nullable=False)
    lead_display_name = Column(String, nullable=True)
    lead_profile_url = Column(String, nullable=True)

    # Funnel tracking (E06-002)
    funnel_stage = Column(SQLEnum(FunnelStage), default=FunnelStage.LEAD_MAGNET, index=True)
    conversion_probability = Column(Float, default=0.0)  # 0.0-1.0

    # Lead scoring (E06-003)
    lead_score = Column(Integer, default=0, index=True)  # 0-100
    qualification_status = Column(SQLEnum(LeadQualification), default=LeadQualification.COLD_LEAD, index=True)

    # Engagement metrics
    message_count = Column(Integer, default=0)
    user_message_count = Column(Integer, default=0)
    bot_message_count = Column(Integer, default=0)
    avg_response_time_seconds = Column(Float, nullable=True)
    avg_sentiment_score = Column(Float, default=0.5)  # 0.0-1.0 (negative to positive)

    # Conversion tracking (E06-004)
    is_converted = Column(Boolean, default=False, index=True)
    converted_at = Column(DateTime, nullable=True)
    total_revenue = Column(Float, default=0.0)

    # A/B testing (E06-005)
    ab_test_variant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    ab_test_name = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_blocked = Column(Boolean, default=False)
    last_message_at = Column(DateTime, nullable=True)

    # Metadata
    metadata = Column(JSON, default=dict)  # Platform-specific data, preferences, notes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    upsell_events = relationship("UpsellEvent", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.platform}:{self.lead_username} - {self.funnel_stage.value}>"

    def update_lead_score(self, new_score: int):
        """Update lead score and qualification status"""
        self.lead_score = max(0, min(100, new_score))

        if self.lead_score >= 71:
            self.qualification_status = LeadQualification.HOT_LEAD
        elif self.lead_score >= 41:
            self.qualification_status = LeadQualification.WARM_LEAD
        else:
            self.qualification_status = LeadQualification.COLD_LEAD

    def advance_funnel_stage(self):
        """Move conversation to next funnel stage"""
        if self.funnel_stage == FunnelStage.LEAD_MAGNET:
            self.funnel_stage = FunnelStage.QUALIFICATION
        elif self.funnel_stage == FunnelStage.QUALIFICATION:
            self.funnel_stage = FunnelStage.CONVERSION

    def mark_converted(self, revenue: float = 0.0):
        """Mark conversation as converted"""
        self.is_converted = True
        self.converted_at = datetime.utcnow()
        self.total_revenue += revenue
        self.funnel_stage = FunnelStage.CONVERSION
        self.update_lead_score(100)


class Message(Base):
    """
    Individual message in a conversation
    Stores message content, sentiment, and metadata
    """

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relations
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message details
    sender_type = Column(SQLEnum(SenderType), nullable=False, index=True)
    platform_message_id = Column(String, nullable=True)  # Platform's message ID

    # Content
    message_text = Column(Text, nullable=False)
    media_urls = Column(JSON, default=list)  # Images/videos sent in message

    # Analysis
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    intent_detected = Column(String, nullable=True)  # purchase_intent, question, objection, etc.
    entities_detected = Column(JSON, default=dict)  # NER results

    # Bot response metadata (if sender_type == BOT)
    bot_template_used = Column(String, nullable=True)
    bot_confidence_score = Column(Float, nullable=True)
    bot_fallback_triggered = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)

    # Relationship
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.sender_type.value}: {self.message_text[:50]}...>"


class UpsellEvent(Base):
    """
    Upsell/conversion event tracking (E06-004)
    Records all monetization attempts and outcomes
    """

    __tablename__ = "upsell_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relations
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    avatar_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Offer details
    offer_type = Column(String, nullable=False, index=True)  # subscription_tier_1, tier_2, tier_3, custom_content, premium_pack
    offer_description = Column(Text, nullable=True)
    offer_price_usd = Column(Float, nullable=False)

    # User response
    user_response = Column(String, nullable=False, index=True)  # accepted, rejected, negotiating, pending
    rejection_reason = Column(String, nullable=True)  # too_expensive, not_interested, need_time

    # Conversion tracking
    is_successful = Column(Boolean, default=False, index=True)
    revenue_generated = Column(Float, default=0.0)

    # A/B testing
    ab_test_variant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    pricing_strategy = Column(String, nullable=True)  # anchor_pricing, scarcity, urgency, social_proof

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    converted_at = Column(DateTime, nullable=True)

    # Relationship
    conversation = relationship("Conversation", back_populates="upsell_events")

    def __repr__(self):
        return f"<UpsellEvent {self.offer_type}: {self.user_response}>"


class ABTestVariant(Base):
    """
    A/B testing variant configuration (E06-005)
    Test different chatbot strategies for optimization
    """

    __tablename__ = "ab_test_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Test configuration
    test_name = Column(String, nullable=False, index=True)  # welcome_message_test, pricing_test, objection_handling_test
    variant_name = Column(String, nullable=False)  # variant_a, variant_b, control
    description = Column(Text, nullable=True)

    # Test element
    element_type = Column(String, nullable=False)  # welcome_message, cta, pricing_offer, objection_response
    element_content = Column(JSON, nullable=False)  # Template, pricing, strategy details

    # Traffic allocation
    traffic_percentage = Column(Float, default=50.0)  # 0-100
    is_active = Column(Boolean, default=True, index=True)

    # Performance metrics
    total_conversations = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    avg_revenue_per_conversation = Column(Float, default=0.0)
    avg_messages_to_conversion = Column(Float, nullable=True)

    # Statistical significance
    confidence_level = Column(Float, nullable=True)  # 0.0-1.0
    is_winner = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    test_started_at = Column(DateTime, nullable=True)
    test_ended_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ABTestVariant {self.test_name}:{self.variant_name}>"

    def update_metrics(self, conversion: bool = False, revenue: float = 0.0):
        """Update variant metrics"""
        self.total_conversations += 1

        if conversion:
            self.total_conversions += 1

        self.conversion_rate = (self.total_conversions / self.total_conversations * 100) if self.total_conversations > 0 else 0.0
        self.avg_revenue_per_conversation = ((self.avg_revenue_per_conversation * (self.total_conversations - 1)) + revenue) / self.total_conversations if self.total_conversations > 0 else 0.0
