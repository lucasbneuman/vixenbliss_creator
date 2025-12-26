"""
Premium API Endpoints
Endpoints for premium content packs (Capa 2) - ÉPICA 07
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.services.premium_packs import premium_packs_service
from app.models.conversation import Conversation, UpsellEvent
from app.services.conversion_tracking import conversion_tracking_service

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/premium",
    tags=["Premium Content"]
)


# Premium Pack Creation (E07-001)

@router.get("/packs")
async def get_available_packs(
    avatar_id: str,
    db: Session = Depends(get_db)
):
    """
    Get available premium pack configurations for an avatar

    E07-001: Premium pack listings
    """

    try:
        packs = premium_packs_service.get_available_packs(
            db=db,
            avatar_id=UUID(avatar_id)
        )

        return {
            "avatar_id": avatar_id,
            "available_packs": packs
        }

    except Exception as e:
        logger.error(f"Failed to get available packs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/packs/create")
async def create_premium_pack(
    avatar_id: str,
    pack_type: str = "deluxe_pack",
    custom_piece_count: Optional[int] = None,
    custom_price: Optional[float] = None,
    custom_explicitness: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Create a premium content pack

    E07-001: Premium pack generation
    """

    try:
        result = await premium_packs_service.create_premium_pack(
            db=db,
            avatar_id=UUID(avatar_id),
            pack_type=pack_type,
            custom_piece_count=custom_piece_count,
            custom_price=custom_price,
            custom_explicitness=custom_explicitness
        )

        return result

    except Exception as e:
        logger.error(f"Failed to create premium pack: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packs/stats/{avatar_id}")
async def get_pack_statistics(
    avatar_id: str,
    db: Session = Depends(get_db)
):
    """
    Get premium pack statistics for an avatar

    E07-001: Pack analytics
    """

    try:
        stats = premium_packs_service.get_pack_statistics(
            db=db,
            avatar_id=UUID(avatar_id)
        )

        return {
            "avatar_id": avatar_id,
            **stats
        }

    except Exception as e:
        logger.error(f"Failed to get pack statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Conversion Tracking Capa 1 → 2 (E07-003)

@router.post("/conversions/tier-upgrade")
async def record_tier_upgrade(
    conversation_id: str,
    from_tier: str,
    to_tier: str,
    upgrade_price: float,
    db: Session = Depends(get_db)
):
    """
    Record tier upgrade event (Capa 1 → Capa 2)

    E07-003: Conversion tracking
    """

    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == UUID(conversation_id)
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Create upsell event for the upgrade
        upsell_event = conversion_tracking_service.create_upsell_event(
            db=db,
            conversation_id=UUID(conversation_id),
            offer_type=f"tier_upgrade_{from_tier}_to_{to_tier}",
            offer_price=upgrade_price,
            offer_description=f"Upgrade from {from_tier} to {to_tier}"
        )

        # Mark as converted immediately
        result = conversion_tracking_service.mark_upsell_converted(
            db=db,
            upsell_event_id=upsell_event.id,
            revenue_generated=upgrade_price
        )

        # Update conversation metadata
        conversation.metadata["tier_upgrades"] = conversation.metadata.get("tier_upgrades", [])
        conversation.metadata["tier_upgrades"].append({
            "from_tier": from_tier,
            "to_tier": to_tier,
            "price": upgrade_price,
            "timestamp": datetime.utcnow().isoformat()
        })

        db.commit()

        logger.info(f"Recorded tier upgrade: {from_tier} → {to_tier} for conversation {conversation_id}")

        return {
            "success": True,
            "upgrade_event_id": str(upsell_event.id),
            **result
        }

    except Exception as e:
        logger.error(f"Failed to record tier upgrade: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversions/tier-upgrade/stats")
async def get_tier_upgrade_stats(
    avatar_id: Optional[str] = None,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get tier upgrade statistics

    E07-003: Upgrade analytics
    """

    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    # Get all upgrade events
    query = db.query(UpsellEvent).filter(
        UpsellEvent.created_at >= cutoff_date,
        UpsellEvent.offer_type.like("tier_upgrade%")
    )

    if avatar_id:
        query = query.filter(UpsellEvent.avatar_id == UUID(avatar_id))

    upgrade_events = query.all()

    # Calculate metrics
    total_upgrades = len([e for e in upgrade_events if e.is_successful])
    total_upgrade_attempts = len(upgrade_events)

    conversion_rate_1_to_2 = (total_upgrades / total_upgrade_attempts * 100) if total_upgrade_attempts > 0 else 0.0

    # Calculate avg time to upgrade
    from app.models.conversation import Conversation

    upgraded_conversations = db.query(Conversation).filter(
        Conversation.id.in_([e.conversation_id for e in upgrade_events if e.is_successful])
    ).all()

    avg_time_to_upgrade_hours = 0.0

    if upgraded_conversations:
        total_hours = sum(
            (e.converted_at - conv.created_at).total_seconds() / 3600
            for e in upgrade_events if e.is_successful
            for conv in upgraded_conversations if conv.id == e.conversation_id
        )
        avg_time_to_upgrade_hours = total_hours / len(upgraded_conversations)

    # Revenue from upgrades
    upgrade_revenue = sum(e.revenue_generated for e in upgrade_events if e.is_successful)

    return {
        "period_days": days_back,
        "total_upgrade_attempts": total_upgrade_attempts,
        "successful_upgrades": total_upgrades,
        "conversion_rate_1_to_2": round(conversion_rate_1_to_2, 2),
        "avg_time_to_upgrade_hours": round(avg_time_to_upgrade_hours, 2),
        "total_upgrade_revenue": round(upgrade_revenue, 2),
        "avg_upgrade_price": round(upgrade_revenue / total_upgrades, 2) if total_upgrades > 0 else 0.0
    }


# Revenue Metrics (E07-004)

@router.get("/metrics/revenue-per-subscriber")
async def get_revenue_per_subscriber_metrics(
    avatar_id: Optional[str] = None,
    tier: Optional[str] = None,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get revenue per subscriber metrics

    E07-004: ARPU, LTV, revenue growth rate
    """

    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    # Get all upsell events (representing purchases/subscriptions)
    query = db.query(UpsellEvent).filter(
        UpsellEvent.created_at >= cutoff_date,
        UpsellEvent.is_successful == True
    )

    if avatar_id:
        query = query.filter(UpsellEvent.avatar_id == UUID(avatar_id))

    upsell_events = query.all()

    # Get unique subscribers (conversations that converted)
    unique_subscribers = len(set(e.conversation_id for e in upsell_events))

    if unique_subscribers == 0:
        return {
            "period_days": days_back,
            "total_subscribers": 0,
            "arpu": 0.0,
            "total_revenue": 0.0,
            "revenue_growth_rate": 0.0,
            "ltv_estimates": {}
        }

    # Calculate ARPU (Average Revenue Per User)
    total_revenue = sum(e.revenue_generated for e in upsell_events)
    arpu = total_revenue / unique_subscribers

    # Revenue by tier
    revenue_by_tier = {}

    for event in upsell_events:
        # Determine tier from offer type
        if "tier_1" in event.offer_type or "subscription" in event.offer_type:
            event_tier = "capa1"
        elif "tier_2" in event.offer_type or "premium" in event.offer_type:
            event_tier = "capa2"
        elif "tier_3" in event.offer_type or "custom" in event.offer_type:
            event_tier = "capa3"
        else:
            event_tier = "unknown"

        if event_tier not in revenue_by_tier:
            revenue_by_tier[event_tier] = {
                "revenue": 0.0,
                "subscribers": set()
            }

        revenue_by_tier[event_tier]["revenue"] += event.revenue_generated
        revenue_by_tier[event_tier]["subscribers"].add(event.conversation_id)

    # Calculate LTV estimates by tier (simplified: revenue * expected lifetime in months)
    ltv_estimates = {}

    for tier_name, tier_data in revenue_by_tier.items():
        subscriber_count = len(tier_data["subscribers"])

        if subscriber_count > 0:
            arpu_tier = tier_data["revenue"] / subscriber_count

            # Estimate lifetime (simplified assumption)
            if tier_name == "capa1":
                expected_lifetime_months = 3  # 3 months average
            elif tier_name == "capa2":
                expected_lifetime_months = 6  # 6 months average
            elif tier_name == "capa3":
                expected_lifetime_months = 12  # 12 months average
            else:
                expected_lifetime_months = 3

            ltv_estimates[tier_name] = {
                "arpu": round(arpu_tier, 2),
                "subscribers": subscriber_count,
                "total_revenue": round(tier_data["revenue"], 2),
                "estimated_ltv": round(arpu_tier * expected_lifetime_months, 2),
                "expected_lifetime_months": expected_lifetime_months
            }

    # Calculate revenue growth rate (compare to previous period)
    previous_cutoff = cutoff_date - timedelta(days=days_back)

    previous_query = db.query(UpsellEvent).filter(
        UpsellEvent.created_at >= previous_cutoff,
        UpsellEvent.created_at < cutoff_date,
        UpsellEvent.is_successful == True
    )

    if avatar_id:
        previous_query = previous_query.filter(UpsellEvent.avatar_id == UUID(avatar_id))

    previous_events = previous_query.all()
    previous_revenue = sum(e.revenue_generated for e in previous_events)

    revenue_growth_rate = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0.0

    return {
        "period_days": days_back,
        "total_subscribers": unique_subscribers,
        "arpu": round(arpu, 2),
        "total_revenue": round(total_revenue, 2),
        "revenue_growth_rate": round(revenue_growth_rate, 2),
        "ltv_estimates": ltv_estimates,
        "previous_period_revenue": round(previous_revenue, 2)
    }


@router.get("/metrics/dashboard")
async def get_premium_metrics_dashboard(
    avatar_id: Optional[str] = None,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive premium metrics dashboard

    E07-004: Revenue dashboard with tier segmentation
    """

    # Get revenue per subscriber metrics
    revenue_metrics = await get_revenue_per_subscriber_metrics(
        avatar_id=avatar_id,
        days_back=days_back,
        db=db
    )

    # Get tier upgrade stats
    upgrade_stats = await get_tier_upgrade_stats(
        avatar_id=avatar_id,
        days_back=days_back,
        db=db
    )

    # Get pack statistics if avatar specified
    pack_stats = None

    if avatar_id:
        pack_stats = premium_packs_service.get_pack_statistics(
            db=db,
            avatar_id=UUID(avatar_id)
        )

    return {
        "period_days": days_back,
        "avatar_id": avatar_id,
        "revenue_metrics": revenue_metrics,
        "tier_upgrade_stats": upgrade_stats,
        "premium_pack_stats": pack_stats,
        "last_updated": datetime.utcnow().isoformat()
    }
