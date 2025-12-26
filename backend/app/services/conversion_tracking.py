"""
Conversion Tracking Service
Track upsell events and monetization (E06-004)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.models.conversation import Conversation, UpsellEvent, ABTestVariant
from app.models.avatar import Avatar

logger = logging.getLogger(__name__)


class ConversionTrackingService:
    """
    Track and analyze conversion events across the sales funnel

    Tracks:
    - Upsell offers presented
    - User responses (accepted, rejected, negotiating)
    - Revenue generated
    - Conversion rates by tier
    - A/B test performance
    """

    def __init__(self):
        # Offer types and pricing
        self.offer_types = {
            "subscription_tier_1": {
                "name": "Basic Subscription",
                "price": 9.99,
                "description": "Access to premium photos"
            },
            "subscription_tier_2": {
                "name": "Premium Subscription",
                "price": 19.99,
                "description": "Exclusive content + DMs"
            },
            "subscription_tier_3": {
                "name": "VIP Subscription",
                "price": 29.99,
                "description": "All content + custom requests"
            },
            "custom_content": {
                "name": "Custom Content Request",
                "price": 39.99,
                "description": "Personalized content just for you"
            },
            "premium_pack": {
                "name": "Premium Photo Pack",
                "price": 14.99,
                "description": "50 exclusive photos"
            }
        }

    def create_upsell_event(
        self,
        db: Session,
        conversation_id: UUID,
        offer_type: str,
        offer_price: Optional[float] = None,
        ab_test_variant_id: Optional[UUID] = None,
        pricing_strategy: Optional[str] = None,
        offer_description: Optional[str] = None
    ) -> UpsellEvent:
        """
        Create an upsell event when offer is presented

        Args:
            db: Database session
            conversation_id: Conversation ID
            offer_type: Type of offer (subscription_tier_1, custom_content, etc.)
            offer_price: Custom price (uses default if not provided)
            ab_test_variant_id: A/B test variant ID (if applicable)
            pricing_strategy: Pricing strategy used
            offer_description: Custom offer description

        Returns:
            Created UpsellEvent object
        """

        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get offer details
        offer_info = self.offer_types.get(offer_type, {})

        if not offer_info and not offer_price:
            raise ValueError(f"Unknown offer type {offer_type} and no price provided")

        # Create upsell event
        upsell_event = UpsellEvent(
            conversation_id=conversation_id,
            avatar_id=conversation.avatar_id,
            user_id=conversation.user_id,
            offer_type=offer_type,
            offer_description=offer_description or offer_info.get("description", ""),
            offer_price_usd=offer_price or offer_info["price"],
            user_response="pending",
            is_successful=False,
            revenue_generated=0.0,
            ab_test_variant_id=ab_test_variant_id,
            pricing_strategy=pricing_strategy
        )

        db.add(upsell_event)
        db.commit()
        db.refresh(upsell_event)

        logger.info(f"Created upsell event {upsell_event.id} for conversation {conversation_id}: {offer_type} - ${offer_price or offer_info['price']}")

        return upsell_event

    def record_upsell_response(
        self,
        db: Session,
        upsell_event_id: UUID,
        user_response: str,
        rejection_reason: Optional[str] = None,
        negotiated_price: Optional[float] = None
    ) -> UpsellEvent:
        """
        Record user's response to upsell offer

        Args:
            db: Database session
            upsell_event_id: Upsell event ID
            user_response: Response (accepted, rejected, negotiating, pending)
            rejection_reason: Reason for rejection (if applicable)
            negotiated_price: New price if negotiated

        Returns:
            Updated UpsellEvent object
        """

        upsell_event = db.query(UpsellEvent).filter(
            UpsellEvent.id == upsell_event_id
        ).first()

        if not upsell_event:
            raise ValueError(f"Upsell event {upsell_event_id} not found")

        # Update response
        upsell_event.user_response = user_response
        upsell_event.rejection_reason = rejection_reason

        # If negotiated, update price
        if negotiated_price:
            upsell_event.offer_price_usd = negotiated_price

        db.commit()

        logger.info(f"Recorded upsell response for event {upsell_event_id}: {user_response}")

        return upsell_event

    def mark_upsell_converted(
        self,
        db: Session,
        upsell_event_id: UUID,
        revenue_generated: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Mark upsell as successfully converted

        Args:
            db: Database session
            upsell_event_id: Upsell event ID
            revenue_generated: Revenue amount (uses offer price if not provided)

        Returns:
            Conversion result with metrics
        """

        upsell_event = db.query(UpsellEvent).filter(
            UpsellEvent.id == upsell_event_id
        ).first()

        if not upsell_event:
            raise ValueError(f"Upsell event {upsell_event_id} not found")

        # Mark as successful
        upsell_event.is_successful = True
        upsell_event.user_response = "accepted"
        upsell_event.converted_at = datetime.utcnow()
        upsell_event.revenue_generated = revenue_generated or upsell_event.offer_price_usd

        # Get conversation and mark as converted
        conversation = db.query(Conversation).filter(
            Conversation.id == upsell_event.conversation_id
        ).first()

        if conversation:
            conversation.mark_converted(revenue=upsell_event.revenue_generated)

        # Update A/B test metrics if applicable
        if upsell_event.ab_test_variant_id:
            variant = db.query(ABTestVariant).filter(
                ABTestVariant.id == upsell_event.ab_test_variant_id
            ).first()

            if variant:
                variant.update_metrics(
                    conversion=True,
                    revenue=upsell_event.revenue_generated
                )

        db.commit()

        logger.info(f"Upsell event {upsell_event_id} converted: ${upsell_event.revenue_generated}")

        # Calculate conversion metrics
        metrics = self._calculate_conversion_metrics(db, conversation.avatar_id if conversation else None)

        return {
            "upsell_event_id": str(upsell_event_id),
            "conversation_id": str(upsell_event.conversation_id),
            "revenue_generated": upsell_event.revenue_generated,
            "offer_type": upsell_event.offer_type,
            "converted_at": upsell_event.converted_at.isoformat(),
            "metrics": metrics
        }

    def _calculate_conversion_metrics(
        self,
        db: Session,
        avatar_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Calculate conversion metrics for avatar or overall"""

        query = db.query(UpsellEvent)

        if avatar_id:
            query = query.filter(UpsellEvent.avatar_id == avatar_id)

        # Total upsell events
        total_events = query.count()

        # Successful conversions
        successful_events = query.filter(UpsellEvent.is_successful == True).count()

        # Conversion rate
        conversion_rate = (successful_events / total_events * 100) if total_events > 0 else 0.0

        # Total revenue
        total_revenue = db.query(func.sum(UpsellEvent.revenue_generated)).filter(
            UpsellEvent.is_successful == True
        )

        if avatar_id:
            total_revenue = total_revenue.filter(UpsellEvent.avatar_id == avatar_id)

        total_revenue = total_revenue.scalar() or 0.0

        # Average revenue per conversion
        avg_revenue_per_conversion = (total_revenue / successful_events) if successful_events > 0 else 0.0

        # Revenue by offer type
        revenue_by_type = {}

        for offer_type_key in self.offer_types.keys():
            type_revenue = db.query(func.sum(UpsellEvent.revenue_generated)).filter(
                UpsellEvent.offer_type == offer_type_key,
                UpsellEvent.is_successful == True
            )

            if avatar_id:
                type_revenue = type_revenue.filter(UpsellEvent.avatar_id == avatar_id)

            type_revenue = type_revenue.scalar() or 0.0
            revenue_by_type[offer_type_key] = round(type_revenue, 2)

        return {
            "total_upsell_events": total_events,
            "successful_conversions": successful_events,
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_conversion": round(avg_revenue_per_conversion, 2),
            "revenue_by_offer_type": revenue_by_type
        }

    def get_conversion_funnel_analytics(
        self,
        db: Session,
        avatar_id: Optional[UUID] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get conversion funnel analytics

        Args:
            db: Database session
            avatar_id: Filter by avatar (optional)
            days_back: Days to analyze

        Returns:
            Funnel analytics with conversion rates at each stage
        """

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Base query
        conv_query = db.query(Conversation).filter(
            Conversation.created_at >= cutoff_date
        )

        if avatar_id:
            conv_query = conv_query.filter(Conversation.avatar_id == avatar_id)

        # Total conversations started
        total_conversations = conv_query.count()

        # Conversations by funnel stage
        from app.models.conversation import FunnelStage

        lead_magnet_count = conv_query.filter(Conversation.funnel_stage == FunnelStage.LEAD_MAGNET).count()
        qualification_count = conv_query.filter(Conversation.funnel_stage == FunnelStage.QUALIFICATION).count()
        conversion_count = conv_query.filter(Conversation.funnel_stage == FunnelStage.CONVERSION).count()

        # Actually converted
        converted_count = conv_query.filter(Conversation.is_converted == True).count()

        # Calculate conversion rates
        if total_conversations > 0:
            lead_to_qual_rate = ((qualification_count + conversion_count) / total_conversations * 100)
            qual_to_conv_rate = (conversion_count / total_conversations * 100)
            final_conversion_rate = (converted_count / total_conversations * 100)
        else:
            lead_to_qual_rate = 0.0
            qual_to_conv_rate = 0.0
            final_conversion_rate = 0.0

        # Get revenue metrics
        revenue_metrics = self._calculate_conversion_metrics(db, avatar_id)

        return {
            "period_days": days_back,
            "total_conversations": total_conversations,
            "funnel_stages": {
                "lead_magnet": {
                    "count": lead_magnet_count,
                    "percentage": round(lead_magnet_count / total_conversations * 100, 2) if total_conversations > 0 else 0
                },
                "qualification": {
                    "count": qualification_count,
                    "percentage": round(qualification_count / total_conversations * 100, 2) if total_conversations > 0 else 0
                },
                "conversion": {
                    "count": conversion_count,
                    "percentage": round(conversion_count / total_conversations * 100, 2) if total_conversations > 0 else 0
                },
                "converted": {
                    "count": converted_count,
                    "percentage": round(final_conversion_rate, 2)
                }
            },
            "conversion_rates": {
                "lead_to_qualification": round(lead_to_qual_rate, 2),
                "qualification_to_conversion": round(qual_to_conv_rate, 2),
                "final_conversion": round(final_conversion_rate, 2)
            },
            "revenue": revenue_metrics,
            "last_updated": datetime.utcnow().isoformat()
        }


# Singleton instance
conversion_tracking_service = ConversionTrackingService()
