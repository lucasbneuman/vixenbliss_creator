"""
Cost Tracking Service
Tracks AI generation costs per avatar and provides cost analytics
"""

from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.avatar import Avatar
from app.models.identity_component import IdentityComponent


class CostBreakdown(dict):
    """Cost breakdown structure"""
    facial_generation: float = 0.0
    dataset_generation: float = 0.0
    lora_training: float = 0.0
    bio_generation: float = 0.0
    content_generation: float = 0.0
    total: float = 0.0


class CostTrackerService:
    """Service for tracking and analyzing AI costs"""

    # Base costs for different operations
    COST_RATES = {
        # Image generation
        "replicate_sdxl": 0.01,
        "leonardo": 0.025,
        "midjourney": 0.08,
        "dall_e_3": 0.04,

        # LoRA training
        "lora_training_replicate": 2.50,
        "lora_training_colab": 1.50,

        # LLM costs (per 1k tokens)
        "claude_sonnet": 0.003,  # per 1k input tokens
        "claude_sonnet_output": 0.015,  # per 1k output tokens
        "gpt4o": 0.0025,  # per 1k input tokens
        "gpt4o_output": 0.010,  # per 1k output tokens

        # Embeddings
        "ada_002": 0.0001  # per 1k tokens
    }

    def track_cost(
        self,
        db: Session,
        avatar_id: UUID,
        operation: str,
        provider: str,
        amount_usd: float,
        metadata: Optional[Dict] = None
    ):
        """Track a cost entry for an avatar"""

        avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()

        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        # Initialize cost_breakdown if not exists
        avatar.metadata = avatar.metadata or {}
        if "cost_breakdown" not in avatar.metadata:
            avatar.metadata["cost_breakdown"] = {
                "facial_generation": 0.0,
                "dataset_generation": 0.0,
                "lora_training": 0.0,
                "bio_generation": 0.0,
                "content_generation": 0.0,
                "total": 0.0,
                "entries": []
            }

        # Add cost entry
        cost_entry = {
            "operation": operation,
            "provider": provider,
            "amount_usd": amount_usd,
            "timestamp": str(datetime.utcnow()),
            "metadata": metadata or {}
        }

        avatar.metadata["cost_breakdown"]["entries"].append(cost_entry)

        # Update category total
        category_map = {
            "facial_generation": "facial_generation",
            "dataset_generation": "dataset_generation",
            "lora_training": "lora_training",
            "bio_generation": "bio_generation",
            "content_generation": "content_generation"
        }

        category = category_map.get(operation, "content_generation")
        avatar.metadata["cost_breakdown"][category] += amount_usd
        avatar.metadata["cost_breakdown"]["total"] += amount_usd

        # Mark as modified (for JSONB update)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(avatar, "metadata")

        db.commit()
        db.refresh(avatar)

    def get_avatar_costs(
        self,
        db: Session,
        avatar_id: UUID
    ) -> Dict[str, any]:
        """Get cost breakdown for specific avatar"""

        avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()

        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        cost_data = avatar.metadata.get("cost_breakdown", {
            "facial_generation": 0.0,
            "dataset_generation": 0.0,
            "lora_training": 0.0,
            "bio_generation": 0.0,
            "content_generation": 0.0,
            "total": 0.0,
            "entries": []
        })

        return {
            "avatar_id": str(avatar_id),
            "avatar_name": avatar.name,
            "breakdown": {
                "facial_generation": cost_data.get("facial_generation", 0.0),
                "dataset_generation": cost_data.get("dataset_generation", 0.0),
                "lora_training": cost_data.get("lora_training", 0.0),
                "bio_generation": cost_data.get("bio_generation", 0.0),
                "content_generation": cost_data.get("content_generation", 0.0)
            },
            "total_cost_usd": cost_data.get("total", 0.0),
            "entries": cost_data.get("entries", [])
        }

    def get_batch_costs(
        self,
        db: Session,
        batch_id: str
    ) -> Dict[str, any]:
        """Get costs for a specific batch operation (e.g., dataset generation batch)"""

        # Find all avatars with this batch_id in metadata
        avatars = db.query(Avatar).filter(
            Avatar.metadata.contains({"dataset": {"batch_id": batch_id}})
        ).all()

        total_cost = 0.0
        avatar_costs = []

        for avatar in avatars:
            cost_data = self.get_avatar_costs(db, avatar.id)
            avatar_costs.append(cost_data)
            total_cost += cost_data["total_cost_usd"]

        return {
            "batch_id": batch_id,
            "total_avatars": len(avatars),
            "total_cost_usd": total_cost,
            "avatar_costs": avatar_costs
        }

    def get_cost_summary(
        self,
        db: Session,
        user_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict[str, any]:
        """Get cost summary across all avatars (or for specific user)"""

        query = db.query(Avatar)

        if user_id:
            query = query.filter(Avatar.user_id == user_id)

        # Filter by creation date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Avatar.created_at >= cutoff_date)

        avatars = query.all()

        total_facial = 0.0
        total_dataset = 0.0
        total_lora = 0.0
        total_bio = 0.0
        total_content = 0.0

        for avatar in avatars:
            costs = avatar.metadata.get("cost_breakdown", {})
            total_facial += costs.get("facial_generation", 0.0)
            total_dataset += costs.get("dataset_generation", 0.0)
            total_lora += costs.get("lora_training", 0.0)
            total_bio += costs.get("bio_generation", 0.0)
            total_content += costs.get("content_generation", 0.0)

        grand_total = total_facial + total_dataset + total_lora + total_bio + total_content

        return {
            "period_days": days,
            "total_avatars": len(avatars),
            "breakdown": {
                "facial_generation": round(total_facial, 2),
                "dataset_generation": round(total_dataset, 2),
                "lora_training": round(total_lora, 2),
                "bio_generation": round(total_bio, 2),
                "content_generation": round(total_content, 2)
            },
            "total_cost_usd": round(grand_total, 2),
            "average_cost_per_avatar": round(grand_total / len(avatars), 2) if avatars else 0.0
        }

    def estimate_avatar_creation_cost(self) -> Dict[str, float]:
        """Estimate total cost to create one complete avatar"""

        return {
            "facial_generation": 0.01,  # SDXL
            "dataset_generation": 0.50,  # 50 images @ $0.01 each
            "lora_training": 2.50,  # Replicate training
            "bio_generation": 0.05,  # Claude Sonnet (~1500 tokens)
            "total_estimated": 3.06
        }


# Singleton instance
cost_tracker_service = CostTrackerService()
