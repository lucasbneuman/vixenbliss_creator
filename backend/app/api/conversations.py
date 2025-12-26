"""
Conversations API Endpoints
Endpoints for chatbot conversations and lead management (ÉPICA 06)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.conversation import (
    Conversation,
    Message,
    UpsellEvent,
    ABTestVariant,
    FunnelStage,
    LeadQualification,
    SenderType
)
from app.services.lead_scoring import lead_scoring_service
from app.services.conversion_tracking import conversion_tracking_service
from app.services.ab_testing import ab_testing_service
from app.services.dm_webhook_handler import dm_webhook_handler

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)


# Conversation Endpoints

@router.get("")
async def get_conversations(
    user_id: Optional[str] = None,
    avatar_id: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    qualification: Optional[str] = None,
    min_lead_score: Optional[int] = None,
    is_converted: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of conversations with filtering

    E06-002: Filter by funnel stage
    E06-003: Filter by lead score and qualification
    """

    query = db.query(Conversation)

    if user_id:
        query = query.filter(Conversation.user_id == UUID(user_id))

    if avatar_id:
        query = query.filter(Conversation.avatar_id == UUID(avatar_id))

    if funnel_stage:
        query = query.filter(Conversation.funnel_stage == FunnelStage(funnel_stage))

    if qualification:
        query = query.filter(Conversation.qualification_status == LeadQualification(qualification))

    if min_lead_score is not None:
        query = query.filter(Conversation.lead_score >= min_lead_score)

    if is_converted is not None:
        query = query.filter(Conversation.is_converted == is_converted)

    # Order by lead score (highest first)
    query = query.order_by(Conversation.lead_score.desc(), Conversation.last_message_at.desc())

    conversations = query.limit(limit).offset(offset).all()

    return {
        "total": query.count(),
        "conversations": [
            {
                "id": str(conv.id),
                "avatar_id": str(conv.avatar_id),
                "platform": conv.platform,
                "lead_username": conv.lead_username,
                "lead_display_name": conv.lead_display_name,
                "funnel_stage": conv.funnel_stage.value,
                "lead_score": conv.lead_score,
                "qualification_status": conv.qualification_status.value,
                "conversion_probability": conv.conversion_probability,
                "message_count": conv.message_count,
                "is_converted": conv.is_converted,
                "total_revenue": conv.total_revenue,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "created_at": conv.created_at.isoformat()
            }
            for conv in conversations
        ]
    }


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed conversation information"""

    conversation = db.query(Conversation).filter(
        Conversation.id == UUID(conversation_id)
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": str(conversation.id),
        "avatar_id": str(conversation.avatar_id),
        "social_account_id": str(conversation.social_account_id),
        "user_id": str(conversation.user_id),
        "platform": conversation.platform,
        "channel_type": conversation.channel_type.value,
        "platform_conversation_id": conversation.platform_conversation_id,
        "lead_username": conversation.lead_username,
        "lead_display_name": conversation.lead_display_name,
        "lead_profile_url": conversation.lead_profile_url,
        "funnel_stage": conversation.funnel_stage.value,
        "conversion_probability": conversation.conversion_probability,
        "lead_score": conversation.lead_score,
        "qualification_status": conversation.qualification_status.value,
        "message_count": conversation.message_count,
        "user_message_count": conversation.user_message_count,
        "bot_message_count": conversation.bot_message_count,
        "avg_response_time_seconds": conversation.avg_response_time_seconds,
        "avg_sentiment_score": conversation.avg_sentiment_score,
        "is_converted": conversation.is_converted,
        "converted_at": conversation.converted_at.isoformat() if conversation.converted_at else None,
        "total_revenue": conversation.total_revenue,
        "ab_test_variant_id": str(conversation.ab_test_variant_id) if conversation.ab_test_variant_id else None,
        "ab_test_name": conversation.ab_test_name,
        "is_active": conversation.is_active,
        "is_blocked": conversation.is_blocked,
        "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat()
    }


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get messages for a conversation"""

    conversation = db.query(Conversation).filter(
        Conversation.id == UUID(conversation_id)
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == UUID(conversation_id)
    ).order_by(Message.created_at.desc()).limit(limit).offset(offset).all()

    return {
        "conversation_id": conversation_id,
        "total": len(messages),
        "messages": [
            {
                "id": str(msg.id),
                "sender_type": msg.sender_type.value,
                "message_text": msg.message_text,
                "media_urls": msg.media_urls,
                "sentiment_score": msg.sentiment_score,
                "intent_detected": msg.intent_detected,
                "bot_template_used": msg.bot_template_used,
                "bot_confidence_score": msg.bot_confidence_score,
                "created_at": msg.created_at.isoformat(),
                "read_at": msg.read_at.isoformat() if msg.read_at else None
            }
            for msg in reversed(messages)
        ]
    }


@router.post("/{conversation_id}/send-message")
async def send_manual_message(
    conversation_id: str,
    message_text: str,
    db: Session = Depends(get_db)
):
    """
    Send manual message to conversation (for testing or manual intervention)
    """

    try:
        result = await dm_webhook_handler.process_manual_message(
            db=db,
            conversation_id=UUID(conversation_id),
            message_text=message_text
        )

        return {
            "success": True,
            "bot_response": result["bot_response"],
            "lead_score": result["lead_score"],
            "funnel_stage": result["funnel_stage"],
            "intent": result.get("intent"),
            "sentiment": result.get("sentiment")
        }

    except Exception as e:
        logger.error(f"Failed to send manual message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/rescore")
async def rescore_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Recalculate lead score for conversation (E06-003)
    """

    conversation = db.query(Conversation).filter(
        Conversation.id == UUID(conversation_id)
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    score_data = lead_scoring_service.calculate_lead_score(db, conversation)

    # Update conversation
    conversation.lead_score = score_data["lead_score"]
    conversation.conversion_probability = score_data["conversion_probability"]
    conversation.update_lead_score(score_data["lead_score"])

    db.commit()

    return {
        "conversation_id": conversation_id,
        **score_data
    }


@router.get("/analytics/overview")
async def get_conversations_analytics(
    avatar_id: Optional[str] = None,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get conversation analytics overview

    E06-002: Funnel metrics
    E06-003: Lead scoring distribution
    E06-004: Conversion tracking
    """

    avatar_uuid = UUID(avatar_id) if avatar_id else None

    # Get funnel analytics
    funnel_analytics = conversion_tracking_service.get_conversion_funnel_analytics(
        db=db,
        avatar_id=avatar_uuid,
        days_back=days_back
    )

    # Get lead score distribution
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    conv_query = db.query(Conversation).filter(
        Conversation.created_at >= cutoff_date
    )

    if avatar_uuid:
        conv_query = conv_query.filter(Conversation.avatar_id == avatar_uuid)

    conversations = conv_query.all()

    # Distribution by qualification
    cold_leads = len([c for c in conversations if c.qualification_status == LeadQualification.COLD_LEAD])
    warm_leads = len([c for c in conversations if c.qualification_status == LeadQualification.WARM_LEAD])
    hot_leads = len([c for c in conversations if c.qualification_status == LeadQualification.HOT_LEAD])

    # Average lead score
    avg_lead_score = sum(c.lead_score for c in conversations) / len(conversations) if conversations else 0

    return {
        "period_days": days_back,
        "funnel_analytics": funnel_analytics,
        "lead_distribution": {
            "cold_leads": cold_leads,
            "warm_leads": warm_leads,
            "hot_leads": hot_leads,
            "average_lead_score": round(avg_lead_score, 2)
        },
        "top_conversations": [
            {
                "id": str(conv.id),
                "lead_username": conv.lead_username,
                "lead_score": conv.lead_score,
                "conversion_probability": conv.conversion_probability,
                "total_revenue": conv.total_revenue
            }
            for conv in sorted(conversations, key=lambda c: c.lead_score, reverse=True)[:10]
        ]
    }


# Upsell Events Endpoints

@router.post("/upsell-events")
async def create_upsell_event(
    conversation_id: str,
    offer_type: str,
    offer_price: Optional[float] = None,
    ab_test_variant_id: Optional[str] = None,
    pricing_strategy: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create upsell event (E06-004)
    """

    try:
        upsell_event = conversion_tracking_service.create_upsell_event(
            db=db,
            conversation_id=UUID(conversation_id),
            offer_type=offer_type,
            offer_price=offer_price,
            ab_test_variant_id=UUID(ab_test_variant_id) if ab_test_variant_id else None,
            pricing_strategy=pricing_strategy
        )

        return {
            "id": str(upsell_event.id),
            "conversation_id": str(upsell_event.conversation_id),
            "offer_type": upsell_event.offer_type,
            "offer_price_usd": upsell_event.offer_price_usd,
            "user_response": upsell_event.user_response,
            "created_at": upsell_event.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to create upsell event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/upsell-events/{upsell_event_id}/response")
async def record_upsell_response(
    upsell_event_id: str,
    user_response: str,
    rejection_reason: Optional[str] = None,
    negotiated_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Record user response to upsell (E06-004)
    """

    try:
        upsell_event = conversion_tracking_service.record_upsell_response(
            db=db,
            upsell_event_id=UUID(upsell_event_id),
            user_response=user_response,
            rejection_reason=rejection_reason,
            negotiated_price=negotiated_price
        )

        return {
            "id": str(upsell_event.id),
            "user_response": upsell_event.user_response,
            "rejection_reason": upsell_event.rejection_reason,
            "offer_price_usd": upsell_event.offer_price_usd
        }

    except Exception as e:
        logger.error(f"Failed to record upsell response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upsell-events/{upsell_event_id}/convert")
async def mark_upsell_converted(
    upsell_event_id: str,
    revenue_generated: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Mark upsell as converted (E06-004)
    """

    try:
        result = conversion_tracking_service.mark_upsell_converted(
            db=db,
            upsell_event_id=UUID(upsell_event_id),
            revenue_generated=revenue_generated
        )

        return result

    except Exception as e:
        logger.error(f"Failed to mark upsell converted: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# A/B Testing Endpoints

@router.post("/ab-tests")
async def create_ab_test(
    test_name: str,
    element_type: str,
    variants: List[Dict[str, Any]],
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create A/B test (E06-005)
    """

    try:
        test_variants = ab_testing_service.create_ab_test(
            db=db,
            test_name=test_name,
            element_type=element_type,
            variants=variants,
            description=description
        )

        return {
            "test_name": test_name,
            "element_type": element_type,
            "variants": [
                {
                    "id": str(v.id),
                    "variant_name": v.variant_name,
                    "traffic_percentage": v.traffic_percentage
                }
                for v in test_variants
            ]
        }

    except Exception as e:
        logger.error(f"Failed to create A/B test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-tests/{test_name}/results")
async def get_ab_test_results(
    test_name: str,
    db: Session = Depends(get_db)
):
    """
    Get A/B test results (E06-005)
    """

    try:
        results = ab_testing_service.get_test_results(db, test_name)
        return results

    except Exception as e:
        logger.error(f"Failed to get A/B test results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_name}/end")
async def end_ab_test(
    test_name: str,
    deploy_winner: bool = False,
    db: Session = Depends(get_db)
):
    """
    End A/B test and optionally deploy winner (E06-005)
    """

    try:
        results = ab_testing_service.end_test(
            db=db,
            test_name=test_name,
            deploy_winner=deploy_winner
        )

        return results

    except Exception as e:
        logger.error(f"Failed to end A/B test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
