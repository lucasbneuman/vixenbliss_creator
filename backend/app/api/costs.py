"""
Cost Tracking API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.services.cost_tracker import cost_tracker_service


router = APIRouter(prefix="/api/v1/identities/costs", tags=["costs"])


@router.get("/{avatar_id}")
def get_avatar_costs(
    avatar_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed cost breakdown for specific avatar"""
    try:
        costs = cost_tracker_service.get_avatar_costs(db, avatar_id)
        return costs
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/batch/{batch_id}")
def get_batch_costs(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """Get costs for a dataset generation batch"""
    costs = cost_tracker_service.get_batch_costs(db, batch_id)
    return costs


@router.get("/summary")
def get_cost_summary(
    user_id: Optional[UUID] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get cost summary across all avatars

    Query parameters:
    - user_id: Filter by specific user (optional)
    - days: Number of days to look back (default: 30)
    """
    summary = cost_tracker_service.get_cost_summary(db, user_id, days)
    return summary


@router.get("/estimate")
def get_cost_estimate():
    """Get estimated cost to create one complete avatar"""
    estimate = cost_tracker_service.estimate_avatar_creation_cost()
    return estimate
