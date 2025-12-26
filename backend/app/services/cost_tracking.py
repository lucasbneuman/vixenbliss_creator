"""
Cost Tracking Service
Track generation costs across all providers (E02-007, E08-005)
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta

from app.models.avatar import Avatar

logger = logging.getLogger(__name__)


class CostTrackingService:
    """
    Service for tracking generation costs across avatars and providers
    """

    def track_generation_cost(
        self,
        db: Session,
        avatar_id: UUID,
        operation_type: str,
        provider: str,
        cost: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track a generation cost event

        Args:
            db: Database session
            avatar_id: Avatar ID
            operation_type: Type of operation (image, video, voice, lora_training)
            provider: Provider used
            cost: Cost in USD
            metadata: Additional metadata
        """

        avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()

        if not avatar:
            logger.warning(f"Avatar {avatar_id} not found for cost tracking")
            return

        # Initialize cost tracking if not exists
        if "cost_tracking" not in avatar.metadata:
            avatar.metadata["cost_tracking"] = {
                "total_cost": 0.0,
                "by_operation": {},
                "by_provider": {},
                "events": []
            }

        cost_data = avatar.metadata["cost_tracking"]

        # Update total cost
        cost_data["total_cost"] += cost

        # Update by operation
        if operation_type not in cost_data["by_operation"]:
            cost_data["by_operation"][operation_type] = {
                "total_cost": 0.0,
                "count": 0
            }

        cost_data["by_operation"][operation_type]["total_cost"] += cost
        cost_data["by_operation"][operation_type]["count"] += 1

        # Update by provider
        if provider not in cost_data["by_provider"]:
            cost_data["by_provider"][provider] = {
                "total_cost": 0.0,
                "count": 0
            }

        cost_data["by_provider"][provider]["total_cost"] += cost
        cost_data["by_provider"][provider]["count"] += 1

        # Add event
        event = {
            "operation_type": operation_type,
            "provider": provider,
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        # Keep last 100 events
        cost_data["events"].append(event)
        if len(cost_data["events"]) > 100:
            cost_data["events"] = cost_data["events"][-100:]

        db.commit()

        logger.info(f"Tracked cost: {operation_type} via {provider} = ${cost:.4f} for avatar {avatar_id}")

    def get_avatar_costs(
        self,
        db: Session,
        avatar_id: UUID,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost statistics for an avatar

        Args:
            db: Database session
            avatar_id: Avatar ID
            operation_type: Filter by operation type

        Returns:
            Cost statistics
        """

        avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()

        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        cost_data = avatar.metadata.get("cost_tracking", {
            "total_cost": 0.0,
            "by_operation": {},
            "by_provider": {},
            "events": []
        })

        if operation_type:
            # Filter for specific operation type
            op_data = cost_data["by_operation"].get(operation_type, {
                "total_cost": 0.0,
                "count": 0
            })

            return {
                "avatar_id": str(avatar_id),
                "operation_type": operation_type,
                "total_cost": op_data["total_cost"],
                "count": op_data["count"],
                "avg_cost_per_operation": op_data["total_cost"] / op_data["count"] if op_data["count"] > 0 else 0.0
            }

        return {
            "avatar_id": str(avatar_id),
            "total_cost": cost_data["total_cost"],
            "by_operation": cost_data["by_operation"],
            "by_provider": cost_data["by_provider"],
            "recent_events": cost_data["events"][-10:]  # Last 10 events
        }

    def get_user_costs(
        self,
        db: Session,
        user_id: UUID,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get cost statistics for all avatars of a user

        Args:
            db: Database session
            user_id: User ID
            days_back: Number of days to look back

        Returns:
            Aggregated cost statistics
        """

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Get all user avatars
        avatars = db.query(Avatar).filter(
            Avatar.user_id == user_id
        ).all()

        total_cost = 0.0
        by_operation = {}
        by_provider = {}
        by_avatar = {}

        for avatar in avatars:
            cost_data = avatar.metadata.get("cost_tracking", {})

            # Filter events by date
            recent_events = [
                e for e in cost_data.get("events", [])
                if datetime.fromisoformat(e["timestamp"]) >= cutoff_date
            ]

            avatar_cost = sum(e["cost"] for e in recent_events)
            total_cost += avatar_cost

            # Aggregate by avatar
            by_avatar[str(avatar.id)] = {
                "avatar_name": avatar.name,
                "cost": avatar_cost,
                "event_count": len(recent_events)
            }

            # Aggregate by operation type
            for event in recent_events:
                op_type = event["operation_type"]

                if op_type not in by_operation:
                    by_operation[op_type] = {
                        "total_cost": 0.0,
                        "count": 0
                    }

                by_operation[op_type]["total_cost"] += event["cost"]
                by_operation[op_type]["count"] += 1

                # Aggregate by provider
                provider = event["provider"]

                if provider not in by_provider:
                    by_provider[provider] = {
                        "total_cost": 0.0,
                        "count": 0
                    }

                by_provider[provider]["total_cost"] += event["cost"]
                by_provider[provider]["count"] += 1

        return {
            "user_id": str(user_id),
            "period_days": days_back,
            "total_cost": round(total_cost, 2),
            "by_operation": by_operation,
            "by_provider": by_provider,
            "by_avatar": by_avatar,
            "avatar_count": len(avatars)
        }

    def estimate_batch_cost(
        self,
        operation_type: str,
        provider: str,
        quantity: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Estimate cost for a batch operation

        Args:
            operation_type: Type of operation
            provider: Provider to use
            quantity: Number of items
            metadata: Additional parameters (duration, resolution, etc.)

        Returns:
            Estimated cost in USD
        """

        # Cost tables by operation and provider
        cost_tables = {
            "image": {
                "replicate_sdxl": 0.003,
                "leonardo": 0.005,
                "dalle3": 0.04
            },
            "video": {
                "runway": 0.05,  # per second
                "pika": 0.03,
                "luma": 0.02
            },
            "voice": {
                "elevenlabs": 0.30,  # per 1K chars
                "playht": 0.20,
                "azure": 0.016
            },
            "lora_training": {
                "replicate": 2.50  # per training
            }
        }

        base_cost = cost_tables.get(operation_type, {}).get(provider, 0.0)

        if operation_type == "video" and metadata:
            # Video cost depends on duration
            duration = metadata.get("duration", 4)
            return base_cost * duration * quantity

        elif operation_type == "voice" and metadata:
            # Voice cost depends on character count
            char_count = metadata.get("char_count", 100)
            return (base_cost * char_count / 1000) * quantity

        else:
            # Simple per-item cost
            return base_cost * quantity


# Singleton instance
cost_tracking_service = CostTrackingService()
