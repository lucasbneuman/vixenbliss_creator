import logging
from datetime import datetime, timedelta
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.cleanup_old_data")
def cleanup_old_data():
    """
    Cleanup old data from database (scheduled daily).
    - Remove old temporary files
    - Clean up expired sessions
    - Archive old logs
    """
    logger.info("Starting cleanup of old data...")

    # TODO: Implement cleanup logic
    # Example:
    # - Delete content_pieces older than 90 days with status='draft'
    # - Clean up expired presigned URLs
    # - Archive old conversation logs

    logger.info("Cleanup completed successfully")
    return {"status": "success", "timestamp": datetime.utcnow().isoformat()}


@celery_app.task(name="app.workers.tasks.update_avatar_statistics")
def update_avatar_statistics():
    """
    Update avatar performance statistics (scheduled hourly).
    - Calculate engagement scores
    - Update ROI metrics
    - Classify winners/losers
    """
    logger.info("Updating avatar statistics...")

    # TODO: Implement statistics update logic
    # Example:
    # - Calculate engagement = (likes + comments + shares*2) / impressions * 100
    # - Calculate ROI = (revenue - cost) / cost * 100
    # - Update avatar.performance_score

    logger.info("Avatar statistics updated successfully")
    return {"status": "success", "timestamp": datetime.utcnow().isoformat()}


@celery_app.task(name="app.workers.tasks.generate_content_batch", bind=True)
def generate_content_batch(
    self,
    avatar_id: str,
    num_pieces: int = 50,
    platform: str = "instagram",
    tier_distribution: dict = None,
    include_hooks: bool = True,
    safety_check: bool = True,
    upload_to_storage: bool = True,
    custom_prompts: list = None,
    custom_tiers: list = None,
    generation_config: dict = None
):
    """
    Generate batch of content pieces for an avatar (ÉPICA 03 - E03-005).

    Args:
        avatar_id: UUID of the avatar
        num_pieces: Number of content pieces to generate (default: 50)
        platform: Target platform for hooks
        tier_distribution: Distribution of content tiers
        include_hooks: Whether to generate hooks
        safety_check: Whether to run safety checks
        upload_to_storage: Whether to upload to R2
    """
    import asyncio
    from app.database import SessionLocal
    from app.models.avatar import Avatar
    from app.services.batch_processor import batch_processor, BatchProcessorConfig
    from app.services.hook_generator import Platform
    from uuid import UUID

    logger.info(f"Starting batch content generation for avatar {avatar_id}...")

    db = SessionLocal()

    try:
        # Get avatar (SQLAlchemy 2.0 style)
        from sqlalchemy import select
        stmt = select(Avatar).where(Avatar.id == UUID(avatar_id))
        avatar = db.execute(stmt).scalars().first()
        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        if not avatar.lora_weights_url:
            raise ValueError(f"Avatar {avatar_id} has no trained LoRA weights")

        # Update task state
        self.update_state(
            state="STARTED",
            meta={
                "progress": 0,
                "stage": "Initializing",
                "num_pieces": num_pieces
            }
        )

        # Default generation config from avatar metadata if not provided
        if generation_config is None:
            avatar_meta = getattr(avatar, "meta_data", None) or getattr(avatar, "metadata", None) or {}
            generation_config = avatar_meta.get("generation_config")

        # Create batch processor config
        config = BatchProcessorConfig(
            num_pieces=num_pieces,
            platform=Platform(platform),
            tier_distribution=tier_distribution,
            include_hooks=include_hooks,
            safety_check=safety_check,
            upload_to_storage=upload_to_storage,
            generation_config=generation_config
        )

        # Update state: template selection
        self.update_state(
            state="STARTED",
            meta={
                "progress": 10,
                "stage": "Selecting templates",
                "num_pieces": num_pieces
            }
        )

        # Process batch
        result = asyncio.run(
            batch_processor.process_batch(
                db=db,
                avatar=avatar,
                config=config,
                custom_prompts=custom_prompts,
                custom_tiers=custom_tiers
            )
        )

        # Update state: generation complete
        self.update_state(
            state="STARTED",
            meta={
                "progress": 100,
                "stage": "Complete",
                "num_pieces": result["total_pieces"]
            }
        )

        logger.info(f"Generated {result['total_pieces']} content pieces for avatar {avatar_id}")

        return {
            "status": "success",
            "avatar_id": avatar_id,
            "total_pieces": result["total_pieces"],
            "statistics": result["statistics"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Batch content generation failed for avatar {avatar_id}: {str(e)}")
        raise

    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.train_lora_task", bind=True)
def train_lora_task(
    self,
    avatar_id: str,
    dataset_batch_id: str,
    training_steps: int = 1500,
    learning_rate: float = 1e-4,
    lora_rank: int = 128,
    use_auto_captions: bool = True
):
    """
    Train LoRA model for avatar using Replicate/Colab (ÉPICA 02-003).

    Args:
        avatar_id: UUID of the avatar
        dataset_batch_id: Batch ID from dataset generation
        training_steps: Number of training steps
        learning_rate: Learning rate for training
        lora_rank: LoRA rank dimension
        use_auto_captions: Whether to use auto-generated captions
    """
    import asyncio
    from app.database import SessionLocal
    from app.services.lora_training import lora_training_service
    from app.services.cost_tracker import cost_tracker_service
    from app.models.avatar import Avatar
    from uuid import UUID

    logger.info(f"Starting LoRA training for avatar {avatar_id}...")

    db = SessionLocal()

    try:
        # Get avatar and dataset
        avatar = db.query(Avatar).filter(Avatar.id == UUID(avatar_id)).first()
        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        dataset_info = avatar.metadata.get("dataset", {})
        dataset_zip_url = dataset_info.get("zip_url")

        if not dataset_zip_url:
            raise ValueError(f"No dataset found for avatar {avatar_id}")

        # Start training
        training_result = asyncio.run(
            lora_training_service.train_lora_replicate(
                avatar_id=avatar_id,
                dataset_zip_url=dataset_zip_url,
                training_steps=training_steps,
                learning_rate=learning_rate,
                lora_rank=lora_rank
            )
        )

        # Update task progress
        self.update_state(
            state="STARTED",
            meta={
                "progress": 10.0,
                "current_step": 0,
                "total_steps": training_steps,
                "eta_minutes": 25
            }
        )

        # Poll for completion (simplified - in production, use webhooks)
        training_id = training_result["training_id"]
        completed = False
        progress = 10.0

        while not completed and progress < 100:
            status_result = asyncio.run(
                lora_training_service.get_training_status_replicate(training_id)
            )

            if status_result["status"] == "succeeded":
                completed = True
                weights_url = status_result["output"]["weights"]

                # Finalize training
                asyncio.run(
                    lora_training_service.finalize_training(
                        db=db,
                        avatar_id=avatar_id,
                        weights_url=weights_url,
                        training_metadata={
                            "model_id": training_id,
                            "steps": training_steps,
                            "provider": "replicate"
                        }
                    )
                )

                # Track cost
                cost_tracker_service.track_cost(
                    db=db,
                    avatar_id=UUID(avatar_id),
                    operation="lora_training",
                    provider="replicate",
                    amount_usd=2.50,
                    metadata={"training_id": training_id, "steps": training_steps}
                )

                logger.info(f"LoRA training completed for avatar {avatar_id}")
                return {
                    "status": "success",
                    "avatar_id": avatar_id,
                    "weights_url": weights_url,
                    "total_steps": training_steps,
                    "final_loss": status_result.get("logs", {}).get("final_loss")
                }

            elif status_result["status"] == "failed":
                raise Exception(f"Training failed: {status_result.get('error')}")

            # Update progress
            progress = status_result.get("progress", progress + 5)
            self.update_state(
                state="STARTED",
                meta={
                    "progress": progress,
                    "current_step": int(training_steps * progress / 100),
                    "total_steps": training_steps
                }
            )

            # Wait before next poll
            import time
            time.sleep(30)

    except Exception as e:
        logger.error(f"LoRA training failed for avatar {avatar_id}: {str(e)}")
        raise

    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.schedule_social_post")
def schedule_social_post(content_id: str, platform: str, scheduled_time: str):
    """
    Schedule a social media post (triggered manually).

    Args:
        content_id: UUID of the content piece
        platform: Platform name ('instagram', 'tiktok')
        scheduled_time: ISO format datetime string
    """
    logger.info(f"Scheduling post {content_id} on {platform} for {scheduled_time}")

    # TODO: Implement scheduling logic (ÉPICA 04)
    # 1. Validate platform credentials
    # 2. Create scheduled_posts entry
    # 3. Set up Celery Beat task for publish time
    # 4. Return confirmation

    return {
        "status": "scheduled",
        "content_id": content_id,
        "platform": platform,
        "scheduled_time": scheduled_time
    }


@celery_app.task(name="app.workers.tasks.publish_social_post", bind=True)
def publish_social_post(self, scheduled_post_id: str):
    """
    Publish scheduled social media post (triggered by Celery Beat).

    Args:
        scheduled_post_id: UUID of scheduled post

    E04-001 & E04-002: Auto-publishing
    E04-006: Auto-retry with exponential backoff
    """
    import asyncio
    from app.database import SessionLocal
    from app.models.social_account import ScheduledPost, SocialAccount, Platform
    from app.models.content_piece import ContentPiece
    from app.services.instagram_integration import instagram_service
    from app.services.tiktok_integration import tiktok_service
    from app.services.smart_scheduler import smart_scheduler
    from uuid import UUID

    logger.info(f"Publishing scheduled post {scheduled_post_id}")

    db = SessionLocal()

    try:
        # Get scheduled post
        scheduled_post = db.query(ScheduledPost).filter(
            ScheduledPost.id == UUID(scheduled_post_id)
        ).first()

        if not scheduled_post:
            raise ValueError(f"Scheduled post {scheduled_post_id} not found")

        if scheduled_post.status != "pending":
            logger.warning(f"Post {scheduled_post_id} already processed (status: {scheduled_post.status})")
            return {"status": "skipped", "reason": f"Post already {scheduled_post.status}"}

        # Get social account
        social_account = db.query(SocialAccount).filter(
            SocialAccount.id == scheduled_post.social_account_id
        ).first()

        if not social_account:
            raise ValueError(f"Social account not found")

        # Get content piece
        content_piece = db.query(ContentPiece).filter(
            ContentPiece.id == scheduled_post.content_piece_id
        ).first()

        if not content_piece:
            raise ValueError(f"Content piece not found")

        # Check if account is healthy
        if not social_account.is_healthy():
            logger.warning(f"Account {social_account.id} is unhealthy, skipping post")
            scheduled_post.status = "failed"
            scheduled_post.error_message = f"Account unhealthy (status: {social_account.status.value})"
            db.commit()
            return {"status": "failed", "reason": "Account unhealthy"}

        # Get platform service
        if social_account.platform == Platform.INSTAGRAM:
            service = instagram_service
        elif social_account.platform == Platform.TIKTOK:
            service = tiktok_service
        else:
            raise ValueError(f"Platform {social_account.platform.value} not supported")

        # Decrypt access token
        access_token = service.decrypt_token(social_account.access_token)

        # Build caption with hashtags
        caption = scheduled_post.caption or content_piece.hook_text or ""
        hashtags = scheduled_post.hashtags or []

        # Publish with retry (E04-006: Auto-retry)
        result = asyncio.run(
            service.publish_with_retry(
                access_token=access_token,
                media_urls=[content_piece.url],
                caption=caption,
                hashtags=hashtags,
                max_retries=3
            )
        )

        # Update scheduled post
        scheduled_post.status = "published"
        scheduled_post.published_at = datetime.utcnow()
        scheduled_post.platform_post_id = result.get("post_id")
        scheduled_post.platform_url = result.get("platform_url")

        # Update social account last post time
        social_account.last_post_at = datetime.utcnow()

        db.commit()

        logger.info(f"Successfully published post {scheduled_post_id}")

        return {
            "status": "published",
            "scheduled_post_id": scheduled_post_id,
            "platform_post_id": result.get("post_id"),
            "platform_url": result.get("platform_url"),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to publish post {scheduled_post_id}: {str(e)}")

        # Get scheduled post for retry logic
        scheduled_post = db.query(ScheduledPost).filter(
            ScheduledPost.id == UUID(scheduled_post_id)
        ).first()

        if scheduled_post and scheduled_post.can_retry():
            # Reschedule with exponential backoff (E04-006)
            smart_scheduler.reschedule_failed_post(db, scheduled_post)
            logger.info(f"Rescheduled post {scheduled_post_id} for retry")
        else:
            # Max retries exceeded
            if scheduled_post:
                scheduled_post.status = "failed"
                scheduled_post.error_message = str(e)
                db.commit()

        raise

    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.process_dm_message")
def process_dm_message(conversation_id: str, message_text: str, platform: str = "instagram"):
    """
    Process incoming DM message with chatbot (triggered by webhook) - E06-001

    Args:
        conversation_id: UUID of conversation
        message_text: Message text from user
        platform: Platform name (instagram, tiktok)
    """
    import asyncio
    from uuid import UUID
    from app.database import SessionLocal
    from app.models.conversation import Conversation
    from app.models.social_account import SocialAccount
    from app.services.chatbot_agent import chatbot_agent
    from app.services.instagram_integration import instagram_service
    from app.services.tiktok_integration import tiktok_service

    logger.info(f"Processing DM for conversation {conversation_id} on {platform}")

    db = SessionLocal()

    try:
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == UUID(conversation_id)
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Process message with chatbot agent
        bot_response_data = asyncio.run(
            chatbot_agent.process_message(
                db=db,
                conversation=conversation,
                user_message_text=message_text
            )
        )

        # Get social account for sending response
        social_account = db.query(SocialAccount).filter(
            SocialAccount.id == conversation.social_account_id
        ).first()

        if not social_account:
            raise ValueError(f"Social account not found")

        # Send bot response via platform API
        if platform == "instagram":
            service = instagram_service
        elif platform == "tiktok":
            service = tiktok_service
        else:
            raise ValueError(f"Platform {platform} not supported")

        # Decrypt access token
        access_token = service.decrypt_token(social_account.access_token)

        # Extract recipient ID from platform conversation ID
        # Format: "instagram_<sender_id>_<recipient_id>" or "tiktok_<sender_id>_<recipient_id>"
        parts = conversation.platform_conversation_id.split("_")
        recipient_id = parts[1] if len(parts) >= 3 else None

        if not recipient_id:
            raise ValueError(f"Could not extract recipient ID from {conversation.platform_conversation_id}")

        # Send response
        asyncio.run(
            service.send_dm(
                access_token=access_token,
                recipient_id=recipient_id,
                message_text=bot_response_data["bot_response"]
            )
        )

        logger.info(f"Sent bot response for conversation {conversation_id}: {bot_response_data['bot_response'][:100]}")

        # Check if upsell should be triggered
        if bot_response_data.get("should_upsell"):
            logger.info(f"Upsell opportunity detected for conversation {conversation_id}")
            # Could trigger another task to handle upsell tracking

        return {
            "status": "processed",
            "conversation_id": conversation_id,
            "bot_response": bot_response_data["bot_response"],
            "lead_score": bot_response_data["lead_score"],
            "funnel_stage": bot_response_data["funnel_stage"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to process DM for conversation {conversation_id}: {str(e)}")
        raise

    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.monitor_account_health")
def monitor_account_health():
    """
    Run health checks on all social media accounts (scheduled hourly).

    E04-005: Health monitoring automation
    """
    import asyncio
    from app.database import SessionLocal
    from app.services.health_monitoring import health_monitoring_service

    logger.info("Starting health monitoring for all accounts...")

    db = SessionLocal()

    try:
        # Check all accounts
        results = asyncio.run(health_monitoring_service.check_all_accounts(db))

        # Auto-pause unhealthy accounts
        paused_count = asyncio.run(health_monitoring_service.auto_pause_unhealthy_accounts(db))

        logger.info(f"Health check completed: {len(results)} accounts checked, {paused_count} auto-paused")

        return {
            "status": "success",
            "accounts_checked": len(results),
            "accounts_paused": paused_count,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health monitoring failed: {str(e)}")
        raise

    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.calculate_daily_revenue")
def calculate_daily_revenue():
    """
    Calculate and report daily revenue metrics (scheduled daily).
    """
    logger.info("Calculating daily revenue...")

    # TODO: Implement revenue calculation (ÉPICA 11)
    # 1. Sum all revenue_events for today
    # 2. Calculate by tier (Capa 1, 2, 3)
    # 3. Calculate MRR, churn rate
    # 4. Update analytics dashboard

    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }
