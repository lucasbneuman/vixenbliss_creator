"""
Instagram Integration Service
Instagram Graph API integration for content distribution
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.services.social_integration import SocialIntegrationService

logger = logging.getLogger(__name__)


class InstagramIntegrationService(SocialIntegrationService):
    """Instagram Graph API integration"""

    def __init__(self):
        super().__init__("Instagram")

        self.client_id = os.getenv("INSTAGRAM_CLIENT_ID")
        self.client_secret = os.getenv("INSTAGRAM_CLIENT_SECRET")
        self.graph_api_version = "v19.0"
        self.base_url = f"https://graph.instagram.com/{self.graph_api_version}"
        self.oauth_url = "https://api.instagram.com/oauth"

    async def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get Instagram OAuth authorization URL"""

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "instagram_basic,instagram_content_publish,instagram_manage_comments,instagram_manage_insights",
            "response_type": "code",
            "state": state
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.oauth_url}/authorize?{query_string}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code
        }

        result = await self._make_request(
            method="POST",
            url=f"{self.oauth_url}/access_token",
            data=data
        )

        # Exchange short-lived token for long-lived token
        long_lived_token = await self._get_long_lived_token(result["access_token"])

        return {
            "access_token": long_lived_token["access_token"],
            "token_type": "bearer",
            "expires_in": long_lived_token.get("expires_in", 5184000),  # 60 days
            "user_id": result.get("user_id")
        }

    async def _get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived token (60 days)"""

        params = {
            "grant_type": "ig_exchange_token",
            "client_secret": self.client_secret,
            "access_token": short_lived_token
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        return await self._make_request(
            method="GET",
            url=f"{self.base_url}/access_token?{query_string}"
        )

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh long-lived access token"""

        params = {
            "grant_type": "ig_refresh_token",
            "access_token": refresh_token
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        result = await self._make_request(
            method="GET",
            url=f"{self.base_url}/refresh_access_token?{query_string}"
        )

        return {
            "access_token": result["access_token"],
            "token_type": "bearer",
            "expires_in": result.get("expires_in", 5184000)
        }

    async def get_account_info(self, access_token: str) -> Dict[str, Any]:
        """Get Instagram account information"""

        params = {
            "fields": "id,username,account_type,media_count,followers_count,follows_count",
            "access_token": access_token
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        result = await self._make_request(
            method="GET",
            url=f"{self.base_url}/me?{query_string}"
        )

        return {
            "platform_user_id": result["id"],
            "username": result["username"],
            "account_type": result.get("account_type", "PERSONAL"),
            "followers_count": result.get("followers_count", 0),
            "media_count": result.get("media_count", 0),
            "verified": False  # Instagram Graph API doesn't provide this
        }

    async def publish_post(
        self,
        access_token: str,
        media_urls: list[str],
        caption: Optional[str] = None,
        hashtags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish post to Instagram"""

        if not media_urls:
            raise ValueError("At least one media URL is required")

        # Add hashtags to caption
        final_caption = self._add_hashtags_to_caption(caption or "", hashtags or [])

        # Get user ID
        account_info = await self.get_account_info(access_token)
        user_id = account_info["platform_user_id"]

        if len(media_urls) == 1:
            # Single image/video post
            return await self._publish_single_media(user_id, access_token, media_urls[0], final_caption)
        else:
            # Carousel post
            return await self._publish_carousel(user_id, access_token, media_urls, final_caption)

    async def _publish_single_media(
        self,
        user_id: str,
        access_token: str,
        media_url: str,
        caption: str
    ) -> Dict[str, Any]:
        """Publish single image or video"""

        # Step 1: Create media container
        container_data = {
            "image_url": media_url,
            "caption": caption,
            "access_token": access_token
        }

        container_result = await self._make_request(
            method="POST",
            url=f"{self.base_url}/{user_id}/media",
            data=container_data
        )

        container_id = container_result["id"]

        # Step 2: Publish media container
        publish_data = {
            "creation_id": container_id,
            "access_token": access_token
        }

        publish_result = await self._make_request(
            method="POST",
            url=f"{self.base_url}/{user_id}/media_publish",
            data=publish_data
        )

        post_id = publish_result["id"]

        return {
            "success": True,
            "post_id": post_id,
            "platform_url": f"https://www.instagram.com/p/{post_id}/",
            "published_at": datetime.utcnow().isoformat()
        }

    async def _publish_carousel(
        self,
        user_id: str,
        access_token: str,
        media_urls: list[str],
        caption: str
    ) -> Dict[str, Any]:
        """Publish carousel post (multiple images)"""

        # Step 1: Create media containers for each image
        media_ids = []

        for media_url in media_urls:
            container_data = {
                "image_url": media_url,
                "is_carousel_item": "true",
                "access_token": access_token
            }

            container_result = await self._make_request(
                method="POST",
                url=f"{self.base_url}/{user_id}/media",
                data=container_data
            )

            media_ids.append(container_result["id"])

        # Step 2: Create carousel container
        carousel_data = {
            "media_type": "CAROUSEL",
            "children": ",".join(media_ids),
            "caption": caption,
            "access_token": access_token
        }

        carousel_result = await self._make_request(
            method="POST",
            url=f"{self.base_url}/{user_id}/media",
            data=carousel_data
        )

        carousel_id = carousel_result["id"]

        # Step 3: Publish carousel
        publish_data = {
            "creation_id": carousel_id,
            "access_token": access_token
        }

        publish_result = await self._make_request(
            method="POST",
            url=f"{self.base_url}/{user_id}/media_publish",
            data=publish_data
        )

        post_id = publish_result["id"]

        return {
            "success": True,
            "post_id": post_id,
            "platform_url": f"https://www.instagram.com/p/{post_id}/",
            "published_at": datetime.utcnow().isoformat(),
            "media_count": len(media_ids)
        }

    async def delete_post(self, access_token: str, post_id: str) -> bool:
        """Delete Instagram post"""

        try:
            params = {"access_token": access_token}
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])

            await self._make_request(
                method="DELETE",
                url=f"{self.base_url}/{post_id}?{query_string}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete Instagram post {post_id}: {str(e)}")
            return False

    async def check_account_health(self, access_token: str) -> Dict[str, Any]:
        """Check Instagram account health"""

        try:
            # Get account info to verify token works
            account_info = await self.get_account_info(access_token)

            # Get recent media insights to check engagement
            insights = await self._get_recent_insights(access_token)

            # Calculate health score based on:
            # - Token validity (50 points)
            # - Recent engagement rate (30 points)
            # - No rate limit issues (20 points)

            health_score = 50  # Token is valid

            # Check engagement
            engagement_rate = insights.get("engagement_rate", 0)
            if engagement_rate > 5:
                health_score += 30
            elif engagement_rate > 2:
                health_score += 20
            elif engagement_rate > 1:
                health_score += 10

            # Check rate limits
            rate_limit_info = await self.check_rate_limits(access_token)
            if not rate_limit_info["rate_limited"]:
                health_score += 20

            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "shadowbanned": False,  # Instagram doesn't expose this
                "rate_limited": rate_limit_info["rate_limited"],
                "engagement_rate": engagement_rate,
                "account_type": account_info.get("account_type"),
                "last_checked": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Instagram health check failed: {str(e)}")
            return {
                "healthy": False,
                "health_score": 0,
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }

    async def _get_recent_insights(self, access_token: str) -> Dict[str, Any]:
        """Get engagement insights from recent posts"""

        try:
            # Get recent media
            params = {
                "fields": "id,like_count,comments_count,timestamp",
                "limit": "10",
                "access_token": access_token
            }

            query_string = "&".join([f"{k}={v}" for k, v in params.items()])

            result = await self._make_request(
                method="GET",
                url=f"{self.base_url}/me/media?{query_string}"
            )

            media = result.get("data", [])

            if not media:
                return {"engagement_rate": 0}

            # Calculate average engagement
            total_engagement = sum(
                m.get("like_count", 0) + m.get("comments_count", 0)
                for m in media
            )

            avg_engagement = total_engagement / len(media)

            return {
                "engagement_rate": avg_engagement / 100,  # Simplified calculation
                "post_count": len(media)
            }

        except Exception as e:
            logger.error(f"Failed to get Instagram insights: {str(e)}")
            return {"engagement_rate": 0}

    async def get_user_info(self, access_token: str, user_id: str) -> Dict[str, Any]:
        """
        Get Instagram user information (E06-001)

        Args:
            access_token: Instagram access token
            user_id: Instagram user ID (IGID)

        Returns:
            User information dictionary
        """

        try:
            params = {
                "fields": "id,username,name,profile_picture_url",
                "access_token": access_token
            }

            query_string = "&".join([f"{k}={v}" for k, v in params.items()])

            result = await self._make_request(
                method="GET",
                url=f"{self.base_url}/{user_id}?{query_string}"
            )

            return {
                "user_id": result["id"],
                "username": result.get("username"),
                "name": result.get("name"),
                "profile_picture_url": result.get("profile_picture_url")
            }

        except Exception as e:
            logger.error(f"Failed to get Instagram user info for {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "username": f"user_{user_id}",
                "name": None,
                "profile_picture_url": None
            }

    async def send_dm(
        self,
        access_token: str,
        recipient_id: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Send direct message on Instagram (E06-001)

        Args:
            access_token: Instagram access token
            recipient_id: Instagram user ID (IGID) of recipient
            message_text: Message text to send

        Returns:
            Result with message ID
        """

        try:
            # Get current account ID
            account_info = await self.get_account_info(access_token)
            sender_id = account_info["platform_user_id"]

            # Send message using Instagram Messaging API
            data = {
                "recipient": {"id": recipient_id},
                "message": {"text": message_text},
                "access_token": access_token
            }

            result = await self._make_request(
                method="POST",
                url=f"{self.base_url}/{sender_id}/messages",
                data=data
            )

            logger.info(f"Sent Instagram DM to {recipient_id}: {message_text[:50]}")

            return {
                "success": True,
                "message_id": result.get("message_id"),
                "recipient_id": recipient_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send Instagram DM to {recipient_id}: {str(e)}")
            raise


# Singleton instance
instagram_service = InstagramIntegrationService()
