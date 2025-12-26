"""
DM Webhook Handler Service
Process incoming DM webhooks from Instagram and TikTok (E06-001)
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.models.conversation import Conversation, ChannelType, FunnelStage, LeadQualification
from app.models.social_account import SocialAccount, Platform
from app.services.chatbot_agent import chatbot_agent
from app.services.instagram_integration import instagram_service
from app.services.tiktok_integration import tiktok_service

logger = logging.getLogger(__name__)


class DMWebhookHandler:
    """Handler for DM webhooks from social platforms"""

    def __init__(self):
        self.platform_services = {
            Platform.INSTAGRAM: instagram_service,
            Platform.TIKTOK: tiktok_service
        }

    async def process_instagram_webhook(
        self,
        db: Session,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process Instagram webhook for incoming DM

        Instagram webhook format:
        {
            "object": "instagram",
            "entry": [{
                "id": "<INSTAGRAM_USER_ID>",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "<SENDER_IGID>"},
                    "recipient": {"id": "<RECIPIENT_IGID>"},
                    "timestamp": 1234567890,
                    "message": {
                        "mid": "<MESSAGE_ID>",
                        "text": "User message text"
                    }
                }]
            }]
        }
        """

        logger.info(f"Processing Instagram DM webhook: {webhook_data}")

        try:
            entry = webhook_data.get("entry", [])[0]
            messaging = entry.get("messaging", [])[0]

            sender_id = messaging["sender"]["id"]
            recipient_id = messaging["recipient"]["id"]
            message_data = messaging.get("message", {})
            message_id = message_data.get("mid")
            message_text = message_data.get("text", "")

            # Find social account
            social_account = db.query(SocialAccount).filter(
                SocialAccount.platform == Platform.INSTAGRAM,
                SocialAccount.platform_user_id == recipient_id
            ).first()

            if not social_account:
                logger.warning(f"Social account not found for Instagram user {recipient_id}")
                return {"status": "error", "message": "Social account not found"}

            # Get or create conversation
            platform_conversation_id = f"instagram_{sender_id}_{recipient_id}"

            conversation = db.query(Conversation).filter(
                Conversation.platform_conversation_id == platform_conversation_id
            ).first()

            if not conversation:
                # Get sender info from Instagram API
                access_token = instagram_service.decrypt_token(social_account.access_token)

                try:
                    sender_info = await instagram_service.get_user_info(access_token, sender_id)
                    sender_username = sender_info.get("username", f"user_{sender_id}")
                    sender_name = sender_info.get("name")
                except Exception as e:
                    logger.error(f"Failed to get sender info: {str(e)}")
                    sender_username = f"user_{sender_id}"
                    sender_name = None

                # Create new conversation
                conversation = Conversation(
                    avatar_id=social_account.avatar_id,
                    social_account_id=social_account.id,
                    user_id=social_account.user_id,
                    platform=Platform.INSTAGRAM.value,
                    channel_type=ChannelType.INSTAGRAM_DM,
                    platform_conversation_id=platform_conversation_id,
                    lead_username=sender_username,
                    lead_display_name=sender_name,
                    funnel_stage=FunnelStage.LEAD_MAGNET,
                    lead_score=10,  # Starting score
                    qualification_status=LeadQualification.COLD_LEAD
                )

                db.add(conversation)
                db.commit()
                db.refresh(conversation)

                logger.info(f"Created new Instagram conversation {conversation.id} with {sender_username}")

            # Process message with chatbot agent
            bot_response_data = await chatbot_agent.process_message(
                db=db,
                conversation=conversation,
                user_message_text=message_text,
                platform_message_id=message_id
            )

            # Send bot response via Instagram API
            access_token = instagram_service.decrypt_token(social_account.access_token)

            await instagram_service.send_dm(
                access_token=access_token,
                recipient_id=sender_id,
                message_text=bot_response_data["bot_response"]
            )

            logger.info(f"Sent Instagram DM response to {sender_id}: {bot_response_data['bot_response'][:100]}")

            return {
                "status": "success",
                "conversation_id": str(conversation.id),
                "bot_response": bot_response_data["bot_response"],
                "lead_score": bot_response_data["lead_score"],
                "funnel_stage": bot_response_data["funnel_stage"]
            }

        except Exception as e:
            logger.error(f"Failed to process Instagram webhook: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def process_tiktok_webhook(
        self,
        db: Session,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process TikTok webhook for incoming DM

        TikTok webhook format:
        {
            "event": "direct_message",
            "data": {
                "message_id": "<MESSAGE_ID>",
                "sender_id": "<SENDER_USER_ID>",
                "recipient_id": "<RECIPIENT_USER_ID>",
                "content": {
                    "text": "User message text"
                },
                "timestamp": 1234567890
            }
        }
        """

        logger.info(f"Processing TikTok DM webhook: {webhook_data}")

        try:
            data = webhook_data.get("data", {})

            sender_id = data["sender_id"]
            recipient_id = data["recipient_id"]
            message_id = data.get("message_id")
            message_text = data.get("content", {}).get("text", "")

            # Find social account
            social_account = db.query(SocialAccount).filter(
                SocialAccount.platform == Platform.TIKTOK,
                SocialAccount.platform_user_id == recipient_id
            ).first()

            if not social_account:
                logger.warning(f"Social account not found for TikTok user {recipient_id}")
                return {"status": "error", "message": "Social account not found"}

            # Get or create conversation
            platform_conversation_id = f"tiktok_{sender_id}_{recipient_id}"

            conversation = db.query(Conversation).filter(
                Conversation.platform_conversation_id == platform_conversation_id
            ).first()

            if not conversation:
                # Get sender info from TikTok API
                access_token = tiktok_service.decrypt_token(social_account.access_token)

                try:
                    sender_info = await tiktok_service.get_user_info(access_token, sender_id)
                    sender_username = sender_info.get("username", f"user_{sender_id}")
                    sender_name = sender_info.get("display_name")
                except Exception as e:
                    logger.error(f"Failed to get sender info: {str(e)}")
                    sender_username = f"user_{sender_id}"
                    sender_name = None

                # Create new conversation
                conversation = Conversation(
                    avatar_id=social_account.avatar_id,
                    social_account_id=social_account.id,
                    user_id=social_account.user_id,
                    platform=Platform.TIKTOK.value,
                    channel_type=ChannelType.TIKTOK_DM,
                    platform_conversation_id=platform_conversation_id,
                    lead_username=sender_username,
                    lead_display_name=sender_name,
                    funnel_stage=FunnelStage.LEAD_MAGNET,
                    lead_score=10,
                    qualification_status=LeadQualification.COLD_LEAD
                )

                db.add(conversation)
                db.commit()
                db.refresh(conversation)

                logger.info(f"Created new TikTok conversation {conversation.id} with {sender_username}")

            # Process message with chatbot agent
            bot_response_data = await chatbot_agent.process_message(
                db=db,
                conversation=conversation,
                user_message_text=message_text,
                platform_message_id=message_id
            )

            # Send bot response via TikTok API
            access_token = tiktok_service.decrypt_token(social_account.access_token)

            await tiktok_service.send_dm(
                access_token=access_token,
                recipient_id=sender_id,
                message_text=bot_response_data["bot_response"]
            )

            logger.info(f"Sent TikTok DM response to {sender_id}: {bot_response_data['bot_response'][:100]}")

            return {
                "status": "success",
                "conversation_id": str(conversation.id),
                "bot_response": bot_response_data["bot_response"],
                "lead_score": bot_response_data["lead_score"],
                "funnel_stage": bot_response_data["funnel_stage"]
            }

        except Exception as e:
            logger.error(f"Failed to process TikTok webhook: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def process_manual_message(
        self,
        db: Session,
        conversation_id: UUID,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Process manual message (for testing or manual intervention)

        Args:
            db: Database session
            conversation_id: Conversation ID
            message_text: Message text

        Returns:
            Bot response data
        """

        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Process with chatbot agent
        bot_response_data = await chatbot_agent.process_message(
            db=db,
            conversation=conversation,
            user_message_text=message_text
        )

        return bot_response_data


# Singleton instance
dm_webhook_handler = DMWebhookHandler()
