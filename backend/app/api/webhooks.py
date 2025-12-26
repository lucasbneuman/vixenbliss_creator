"""
Webhook API Endpoints
Endpoints for receiving webhooks from social media platforms (E06-001)
"""

import os
import hmac
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.dm_webhook_handler import dm_webhook_handler
from app.workers.tasks import process_dm_message

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"]
)


# Instagram Webhooks

@router.get("/instagram/verify")
async def verify_instagram_webhook(
    mode: str = Query(alias="hub.mode"),
    challenge: str = Query(alias="hub.challenge"),
    verify_token: str = Query(alias="hub.verify_token")
):
    """
    Verify Instagram webhook subscription
    Instagram sends GET request with verification token
    """

    expected_verify_token = os.getenv("INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "your_verify_token_here")

    if mode == "subscribe" and verify_token == expected_verify_token:
        logger.info("Instagram webhook verified successfully")
        return int(challenge)
    else:
        logger.warning(f"Instagram webhook verification failed: mode={mode}, token={verify_token}")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/instagram/callback")
async def instagram_webhook_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive Instagram webhook events (DMs, comments, mentions)

    Webhook payload example:
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

    # Verify webhook signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_instagram_signature(body, signature):
        logger.warning("Instagram webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse webhook data
    webhook_data = await request.json()

    # Check if this is a messaging event
    if webhook_data.get("object") != "instagram":
        return {"status": "ignored", "reason": "Not an Instagram event"}

    # Process each entry
    for entry in webhook_data.get("entry", []):
        messaging_events = entry.get("messaging", [])

        for event in messaging_events:
            # Check if this is a message event
            if "message" in event:
                # Process DM in background task
                background_tasks.add_task(
                    process_instagram_dm_webhook,
                    db,
                    webhook_data
                )

    return {"status": "received"}


async def process_instagram_dm_webhook(db: Session, webhook_data: Dict[str, Any]):
    """Background task to process Instagram DM webhook"""
    try:
        result = await dm_webhook_handler.process_instagram_webhook(db, webhook_data)
        logger.info(f"Processed Instagram webhook: {result}")
    except Exception as e:
        logger.error(f"Failed to process Instagram webhook: {str(e)}")


def verify_instagram_signature(payload: bytes, signature: str) -> bool:
    """Verify Instagram webhook signature using app secret"""

    app_secret = os.getenv("INSTAGRAM_CLIENT_SECRET", "")

    if not app_secret:
        logger.warning("INSTAGRAM_CLIENT_SECRET not set, skipping signature verification")
        return True  # In development, allow without verification

    # Remove 'sha256=' prefix
    signature = signature.replace("sha256=", "")

    # Calculate expected signature
    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)


# TikTok Webhooks

@router.get("/tiktok/verify")
async def verify_tiktok_webhook(
    challenge: str = Query(...),
    timestamp: str = Query(...),
    signature: str = Query(...)
):
    """
    Verify TikTok webhook subscription
    TikTok sends GET request with challenge code
    """

    # Verify signature
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")

    expected_signature = hashlib.sha256(
        f"{client_secret}{challenge}{timestamp}".encode("utf-8")
    ).hexdigest()

    if hmac.compare_digest(signature, expected_signature):
        logger.info("TikTok webhook verified successfully")
        return {"challenge": challenge}
    else:
        logger.warning("TikTok webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/tiktok/callback")
async def tiktok_webhook_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive TikTok webhook events (DMs, comments, mentions)

    Webhook payload example:
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

    # Verify webhook signature
    body = await request.body()
    signature = request.headers.get("X-TikTok-Signature", "")

    if not verify_tiktok_signature(body, signature):
        logger.warning("TikTok webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse webhook data
    webhook_data = await request.json()

    # Check if this is a DM event
    if webhook_data.get("event") == "direct_message":
        # Process DM in background task
        background_tasks.add_task(
            process_tiktok_dm_webhook,
            db,
            webhook_data
        )

    return {"status": "received"}


async def process_tiktok_dm_webhook(db: Session, webhook_data: Dict[str, Any]):
    """Background task to process TikTok DM webhook"""
    try:
        result = await dm_webhook_handler.process_tiktok_webhook(db, webhook_data)
        logger.info(f"Processed TikTok webhook: {result}")
    except Exception as e:
        logger.error(f"Failed to process TikTok webhook: {str(e)}")


def verify_tiktok_signature(payload: bytes, signature: str) -> bool:
    """Verify TikTok webhook signature using client secret"""

    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")

    if not client_secret:
        logger.warning("TIKTOK_CLIENT_SECRET not set, skipping signature verification")
        return True  # In development, allow without verification

    # Calculate expected signature
    expected_signature = hmac.new(
        client_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)


# Manual Message Endpoint (for testing)

@router.post("/manual/send-message")
async def send_manual_message(
    conversation_id: str,
    message_text: str,
    db: Session = Depends(get_db)
):
    """
    Send manual message to chatbot (for testing)

    Args:
        conversation_id: UUID of conversation
        message_text: Message text from user
    """

    from uuid import UUID

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
            "funnel_stage": result["funnel_stage"]
        }

    except Exception as e:
        logger.error(f"Failed to process manual message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
