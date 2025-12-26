"""
Distribution API Endpoints
Endpoints for social media distribution system
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.social_account import SocialAccount, ScheduledPost, Platform, AccountStatus
from app.models.content_piece import ContentPiece
from app.services.instagram_integration import instagram_service
from app.services.tiktok_integration import tiktok_service
from app.services.smart_scheduler import smart_scheduler
from app.services.health_monitoring import health_monitoring_service


router = APIRouter(
    prefix="/api/v1/distribution",
    tags=["Distribution"]
)


# OAuth Connection Endpoints

@router.get("/auth/{platform}/url")
async def get_oauth_url(
    platform: str,
    redirect_uri: str,
    state: str
):
    """
    Get OAuth authorization URL for connecting social account

    E04-001 & E04-002: OAuth flow
    """

    platform_enum = Platform(platform.lower())

    if platform_enum == Platform.INSTAGRAM:
        auth_url = await instagram_service.get_authorization_url(redirect_uri, state)
    elif platform_enum == Platform.TIKTOK:
        auth_url = await tiktok_service.get_authorization_url(redirect_uri, state)
    else:
        raise HTTPException(status_code=400, detail=f"Platform {platform} not supported")

    return {
        "authorization_url": auth_url,
        "platform": platform,
        "redirect_uri": redirect_uri
    }


@router.post("/auth/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: str,
    redirect_uri: str,
    user_id: str,
    avatar_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback and create social account connection

    E04-001 & E04-002: Token exchange and account creation
    """

    platform_enum = Platform(platform.lower())

    # Exchange code for token
    if platform_enum == Platform.INSTAGRAM:
        token_data = await instagram_service.exchange_code_for_token(code, redirect_uri)
        account_info = await instagram_service.get_account_info(token_data["access_token"])
        service = instagram_service
    elif platform_enum == Platform.TIKTOK:
        token_data = await tiktok_service.exchange_code_for_token(code, redirect_uri)
        account_info = await tiktok_service.get_account_info(token_data["access_token"])
        service = tiktok_service
    else:
        raise HTTPException(status_code=400, detail=f"Platform {platform} not supported")

    # Encrypt tokens
    encrypted_access_token = service.encrypt_token(token_data["access_token"])
    encrypted_refresh_token = service.encrypt_token(token_data.get("refresh_token", "")) if token_data.get("refresh_token") else None

    # Calculate token expiration
    expires_in = token_data.get("expires_in", 0)
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in) if expires_in > 0 else None

    # Check if account already exists
    existing_account = db.query(SocialAccount).filter(
        SocialAccount.platform == platform_enum,
        SocialAccount.platform_user_id == account_info["platform_user_id"]
    ).first()

    if existing_account:
        # Update existing account
        existing_account.access_token = encrypted_access_token
        existing_account.refresh_token = encrypted_refresh_token
        existing_account.token_expires_at = token_expires_at
        existing_account.status = AccountStatus.ACTIVE
        existing_account.metadata.update(account_info)
        db.commit()

        social_account = existing_account
    else:
        # Create new social account
        social_account = SocialAccount(
            user_id=UUID(user_id),
            avatar_id=UUID(avatar_id) if avatar_id else None,
            platform=platform_enum,
            platform_user_id=account_info["platform_user_id"],
            username=account_info["username"],
            display_name=account_info.get("display_name"),
            access_token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            token_expires_at=token_expires_at,
            status=AccountStatus.ACTIVE,
            health_score="100",
            metadata=account_info
        )

        db.add(social_account)
        db.commit()
        db.refresh(social_account)

    return {
        "success": True,
        "account_id": str(social_account.id),
        "platform": platform,
        "username": social_account.username,
        "status": social_account.status.value
    }


# Account Management Endpoints

@router.get("/accounts", response_model=List[Dict[str, Any]])
async def get_social_accounts(
    user_id: str,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all connected social accounts for user

    E04-002: Account management
    """

    query = db.query(SocialAccount).filter(SocialAccount.user_id == UUID(user_id))

    if platform:
        query = query.filter(SocialAccount.platform == Platform(platform.lower()))

    accounts = query.all()

    return [
        {
            "id": str(account.id),
            "platform": account.platform.value,
            "username": account.username,
            "display_name": account.display_name,
            "status": account.status.value,
            "health_score": int(account.health_score),
            "auto_post_enabled": account.auto_post_enabled,
            "followers_count": account.metadata.get("followers_count", 0),
            "last_health_check": account.last_health_check.isoformat() if account.last_health_check else None,
            "last_post_at": account.last_post_at.isoformat() if account.last_post_at else None,
            "created_at": account.created_at.isoformat()
        }
        for account in accounts
    ]


@router.delete("/accounts/{account_id}")
async def disconnect_account(account_id: str, db: Session = Depends(get_db)):
    """Disconnect social account"""

    account = db.query(SocialAccount).filter(SocialAccount.id == UUID(account_id)).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.status = AccountStatus.DISCONNECTED
    account.auto_post_enabled = False
    db.commit()

    return {"success": True, "message": f"Account {account.username} disconnected"}


# Health Monitoring Endpoints

@router.post("/health/check/{account_id}")
async def check_account_health(
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Run health check for specific account

    E04-005: Health monitoring
    """

    account = db.query(SocialAccount).filter(SocialAccount.id == UUID(account_id)).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    result = await health_monitoring_service.check_account_health(db, account)

    return result


@router.post("/health/check-all")
async def check_all_accounts_health(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Run health check for all user accounts

    E04-005: Batch health monitoring
    """

    accounts = db.query(SocialAccount).filter(
        SocialAccount.user_id == UUID(user_id),
        SocialAccount.status != AccountStatus.DISCONNECTED
    ).all()

    results = []

    for account in accounts:
        result = await health_monitoring_service.check_account_health(db, account)
        results.append(result)

    return {
        "total_accounts": len(accounts),
        "results": results
    }


@router.get("/health/dashboard/{user_id}")
async def get_health_dashboard(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get health dashboard data for all user accounts

    E04-005: Health dashboard
    """

    dashboard_data = health_monitoring_service.get_health_dashboard_data(db, UUID(user_id))

    return dashboard_data


# Publishing Endpoints

@router.post("/publish")
async def publish_now(
    account_id: str,
    content_piece_id: str,
    caption: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Publish content immediately to social platform

    E04-001 & E04-002: Direct publishing
    """

    # Get account
    account = db.query(SocialAccount).filter(SocialAccount.id == UUID(account_id)).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check account health
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Account is {account.status.value}, cannot publish")

    # Get content
    content = db.query(ContentPiece).filter(ContentPiece.id == UUID(content_piece_id)).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Get service
    if account.platform == Platform.INSTAGRAM:
        service = instagram_service
    elif account.platform == Platform.TIKTOK:
        service = tiktok_service
    else:
        raise HTTPException(status_code=400, detail=f"Platform {account.platform.value} not supported")

    # Decrypt token
    access_token = service.decrypt_token(account.access_token)

    # Publish with retry (E04-006: Auto-retry)
    try:
        result = await service.publish_with_retry(
            access_token=access_token,
            media_urls=[content.url],
            caption=caption or content.hook_text,
            hashtags=hashtags
        )

        # Update account
        account.last_post_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "post_id": result["post_id"],
            "platform_url": result.get("platform_url"),
            "published_at": result["published_at"]
        }

    except Exception as e:
        logger.error(f"Failed to publish: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")


# Scheduling Endpoints

@router.post("/schedule")
async def schedule_posts(
    account_id: str,
    content_piece_ids: List[str],
    use_smart_scheduling: bool = True,
    use_pattern_randomization: bool = True,
    db: Session = Depends(get_db)
):
    """
    Schedule content for future publishing

    E04-003: Smart scheduler
    E04-004: Pattern randomization
    """

    # Get account
    account = db.query(SocialAccount).filter(SocialAccount.id == UUID(account_id)).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not use_smart_scheduling:
        raise HTTPException(status_code=400, detail="Manual scheduling not yet implemented")

    # Schedule posts
    content_ids = [UUID(cid) for cid in content_piece_ids]

    scheduled_posts = smart_scheduler.schedule_batch_posts(
        db=db,
        social_account=account,
        content_piece_ids=content_ids,
        use_pattern_randomization=use_pattern_randomization
    )

    return {
        "success": True,
        "total_scheduled": len(scheduled_posts),
        "scheduled_posts": [
            {
                "id": str(post.id),
                "content_piece_id": str(post.content_piece_id),
                "scheduled_time": post.scheduled_time.isoformat(),
                "timezone": post.timezone,
                "status": post.status
            }
            for post in scheduled_posts
        ]
    }


@router.get("/scheduled-posts")
async def get_scheduled_posts(
    account_id: Optional[str] = None,
    status: Optional[str] = "pending",
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get scheduled posts"""

    query = db.query(ScheduledPost)

    if account_id:
        query = query.filter(ScheduledPost.social_account_id == UUID(account_id))

    if status:
        query = query.filter(ScheduledPost.status == status)

    posts = query.order_by(ScheduledPost.scheduled_time).limit(limit).all()

    return {
        "total": len(posts),
        "posts": [
            {
                "id": str(post.id),
                "account_id": str(post.social_account_id),
                "content_piece_id": str(post.content_piece_id),
                "scheduled_time": post.scheduled_time.isoformat(),
                "timezone": post.timezone,
                "status": post.status,
                "caption": post.caption,
                "hashtags": post.hashtags,
                "retry_count": int(post.retry_count),
                "platform_post_id": post.platform_post_id,
                "platform_url": post.platform_url
            }
            for post in posts
        ]
    }


@router.delete("/scheduled-posts/{post_id}")
async def cancel_scheduled_post(post_id: str, db: Session = Depends(get_db)):
    """Cancel scheduled post"""

    post = db.query(ScheduledPost).filter(ScheduledPost.id == UUID(post_id)).first()

    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if post.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot cancel post with status {post.status}")

    post.status = "cancelled"
    db.commit()

    return {"success": True, "message": "Scheduled post cancelled"}


# Analytics Endpoints

@router.get("/analytics/optimal-times/{account_id}")
async def get_optimal_posting_times(
    account_id: str,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Analyze engagement patterns to determine optimal posting times

    E04-003: Engagement analysis
    """

    account = db.query(SocialAccount).filter(SocialAccount.id == UUID(account_id)).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    analysis = smart_scheduler.analyze_engagement_patterns(
        db=db,
        social_account_id=UUID(account_id),
        days_back=days_back
    )

    return analysis


import logging
from datetime import timedelta

logger = logging.getLogger(__name__)
