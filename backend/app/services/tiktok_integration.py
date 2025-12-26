"""
TikTok Integration Service
TikTok API integration for content distribution
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import hmac

from app.services.social_integration import SocialIntegrationService

logger = logging.getLogger(__name__)


class TikTokIntegrationService(SocialIntegrationService):
    """TikTok API integration"""

    def __init__(self):
        super().__init__("TikTok")

        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.base_url = "https://open.tiktokapis.com/v2"
        self.oauth_url = "https://www.tiktok.com/v2/auth"

    async def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get TikTok OAuth authorization URL"""

        # TikTok uses PKCE for OAuth
        # In production, generate and store code_verifier
        code_verifier = self._generate_code_verifier()

        params = {
            "client_key": self.client_key,
            "scope": "user.info.basic,video.upload,video.publish",
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.oauth_url}/authorize?{query_string}"

    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier"""
        import secrets
        return secrets.token_urlsafe(32)

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }

        result = await self._make_request(
            method="POST",
            url=f"{self.base_url}/oauth/token/",
            json=data
        )

        return {
            "access_token": result["data"]["access_token"],
            "refresh_token": result["data"]["refresh_token"],
            "token_type": "Bearer",
            "expires_in": result["data"]["expires_in"],
            "open_id": result["data"]["open_id"]
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh TikTok access token"""

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        result = await self._make_request(
            method="POST",
            url=f"{self.base_url}/oauth/token/",
            json=data
        )

        return {
            "access_token": result["data"]["access_token"],
            "refresh_token": result["data"]["refresh_token"],
            "token_type": "Bearer",
            "expires_in": result["data"]["expires_in"]
        }

    async def get_account_info(self, access_token: str) -> Dict[str, Any]:
        """Get TikTok account information"""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        result = await self._make_request(
            method="GET",
            url=f"{self.base_url}/user/info/?fields=open_id,union_id,avatar_url,display_name,follower_count,following_count,likes_count,video_count",
            headers=headers
        )

        user_data = result["data"]["user"]

        return {
            "platform_user_id": user_data["open_id"],
            "username": user_data.get("display_name", ""),
            "avatar_url": user_data.get("avatar_url"),
            "followers_count": user_data.get("follower_count", 0),
            "following_count": user_data.get("following_count", 0),
            "video_count": user_data.get("video_count", 0),
            "likes_count": user_data.get("likes_count", 0)
        }

    async def publish_post(
        self,
        access_token: str,
        media_urls: list[str],
        caption: Optional[str] = None,
        hashtags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish video to TikTok"""

        if not media_urls:
            raise ValueError("At least one video URL is required")

        video_url = media_urls[0]  # TikTok only supports single videos

        # Add hashtags to caption
        final_caption = self._add_hashtags_to_caption(caption or "", hashtags or [])

        # Step 1: Initialize video upload
        init_result = await self._initialize_video_upload(access_token, final_caption, metadata)

        publish_id = init_result["publish_id"]
        upload_url = init_result["upload_url"]

        # Step 2: Upload video to TikTok's server
        await self._upload_video_to_url(video_url, upload_url)

        # Step 3: Check upload status
        status = await self._check_upload_status(access_token, publish_id)

        return {
            "success": status["status"] == "PUBLISH_COMPLETE",
            "post_id": publish_id,
            "platform_url": status.get("share_url", ""),
            "published_at": datetime.utcnow().isoformat(),
            "status": status["status"]
        }

    async def _initialize_video_upload(
        self,
        access_token: str,
        caption: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize TikTok video upload"""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Extract trending sounds/effects from metadata if provided
        video_settings = {
            "title": caption[:150],  # Max 150 characters
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000
        }

        # Add trending sounds if provided
        if metadata and metadata.get("trending_sound_id"):
            video_settings["music_id"] = metadata["trending_sound_id"]

        data = {
            "post_info": video_settings,
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": metadata.get("video_size", 10000000),  # In bytes
                "chunk_size": 10000000,
                "total_chunk_count": 1
            }
        }

        result = await self._make_request(
            method="POST",
            url=f"{self.base_url}/post/publish/video/init/",
            headers=headers,
            json=data
        )

        return {
            "publish_id": result["data"]["publish_id"],
            "upload_url": result["data"]["upload_url"]
        }

    async def _upload_video_to_url(self, video_url: str, upload_url: str):
        """Upload video file to TikTok's upload URL"""

        import httpx

        # Download video from our storage
        async with httpx.AsyncClient() as client:
            video_response = await client.get(video_url, timeout=60.0)
            video_response.raise_for_status()
            video_content = video_response.content

        # Upload to TikTok
        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(video_content))
            }

            upload_response = await client.put(
                upload_url,
                content=video_content,
                headers=headers,
                timeout=120.0
            )

            upload_response.raise_for_status()

        logger.info("Video uploaded successfully to TikTok")

    async def _check_upload_status(
        self,
        access_token: str,
        publish_id: str,
        max_attempts: int = 30
    ) -> Dict[str, Any]:
        """Check video upload and publish status"""

        import asyncio

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        for attempt in range(max_attempts):
            result = await self._make_request(
                method="POST",
                url=f"{self.base_url}/post/publish/status/fetch/",
                headers=headers,
                json={"publish_id": publish_id}
            )

            status = result["data"]["status"]

            if status == "PUBLISH_COMPLETE":
                return {
                    "status": status,
                    "share_url": result["data"].get("share_url", ""),
                    "video_id": result["data"].get("video_id", "")
                }
            elif status == "FAILED":
                raise Exception(f"TikTok publish failed: {result['data'].get('fail_reason', 'Unknown')}")

            # Wait before checking again
            await asyncio.sleep(10)

        raise Exception("TikTok publish timeout - status check exceeded max attempts")

    async def delete_post(self, access_token: str, post_id: str) -> bool:
        """Delete TikTok video"""

        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            await self._make_request(
                method="POST",
                url=f"{self.base_url}/post/publish/video/delete/",
                headers=headers,
                json={"video_id": post_id}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete TikTok video {post_id}: {str(e)}")
            return False

    async def check_account_health(self, access_token: str) -> Dict[str, Any]:
        """Check TikTok account health"""

        try:
            # Get account info to verify token works
            account_info = await self.get_account_info(access_token)

            # Calculate health score based on account metrics
            health_score = 50  # Token is valid

            # Check follower count (20 points)
            followers = account_info.get("followers_count", 0)
            if followers > 10000:
                health_score += 20
            elif followers > 1000:
                health_score += 15
            elif followers > 100:
                health_score += 10

            # Check video count (15 points)
            videos = account_info.get("video_count", 0)
            if videos > 50:
                health_score += 15
            elif videos > 10:
                health_score += 10

            # Check engagement ratio (15 points)
            if followers > 0 and account_info.get("likes_count", 0) > 0:
                engagement_ratio = account_info["likes_count"] / followers
                if engagement_ratio > 0.1:
                    health_score += 15
                elif engagement_ratio > 0.05:
                    health_score += 10

            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "shadowbanned": False,  # TikTok doesn't expose this directly
                "rate_limited": False,
                "followers_count": followers,
                "video_count": videos,
                "last_checked": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"TikTok health check failed: {str(e)}")
            return {
                "healthy": False,
                "health_score": 0,
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }

    async def get_trending_sounds(self, access_token: str, limit: int = 20) -> list[Dict[str, Any]]:
        """Get trending sounds for TikTok videos"""

        # Note: TikTok API doesn't provide public trending sounds endpoint
        # This would need to be implemented with a third-party service or scraping
        # For now, return empty list

        logger.warning("TikTok trending sounds not available via official API")
        return []

    async def optimize_hashtags(self, caption: str, niche: str) -> list[str]:
        """Optimize hashtags for TikTok based on niche"""

        # Predefined hashtag sets by niche
        hashtag_map = {
            "fitness": ["fitness", "workout", "gym", "fit", "fitnessmotivation", "healthylifestyle"],
            "lifestyle": ["lifestyle", "dailyvlog", "lifestyleblogger", "vlog", "dayinmylife"],
            "fashion": ["fashion", "style", "ootd", "fashionista", "fashionblogger", "fashionstyle"],
            "beauty": ["beauty", "makeup", "skincare", "beautytips", "makeuptutorial"],
            "wellness": ["wellness", "selfcare", "mentalhealth", "mindfulness", "wellbeing"]
        }

        base_hashtags = hashtag_map.get(niche.lower(), ["fyp", "foryou", "viral"])

        # Always add viral hashtags
        viral_hashtags = ["fyp", "foryou", "foryoupage", "viral", "trending"]

        return base_hashtags + viral_hashtags

    async def get_user_info(self, access_token: str, user_id: str) -> Dict[str, Any]:
        """
        Get TikTok user information (E06-001)

        Args:
            access_token: TikTok access token
            user_id: TikTok user ID

        Returns:
            User information dictionary
        """

        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            params = {
                "fields": "display_name,username,avatar_url,follower_count"
            }

            result = await self._make_request(
                method="GET",
                url=f"{self.base_url}/user/info",
                headers=headers,
                params=params
            )

            user_data = result.get("data", {}).get("user", {})

            return {
                "user_id": user_id,
                "username": user_data.get("username", f"user_{user_id}"),
                "display_name": user_data.get("display_name"),
                "avatar_url": user_data.get("avatar_url")
            }

        except Exception as e:
            logger.error(f"Failed to get TikTok user info for {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "username": f"user_{user_id}",
                "display_name": None,
                "avatar_url": None
            }

    async def send_dm(
        self,
        access_token: str,
        recipient_id: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Send direct message on TikTok (E06-001)

        Args:
            access_token: TikTok access token
            recipient_id: TikTok user ID of recipient
            message_text: Message text to send

        Returns:
            Result with message ID
        """

        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            data = {
                "recipient_user_id": recipient_id,
                "message": {
                    "text": message_text
                }
            }

            result = await self._make_request(
                method="POST",
                url=f"{self.base_url}/message/send",
                headers=headers,
                data=data
            )

            logger.info(f"Sent TikTok DM to {recipient_id}: {message_text[:50]}")

            return {
                "success": True,
                "message_id": result.get("data", {}).get("message_id"),
                "recipient_id": recipient_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send TikTok DM to {recipient_id}: {str(e)}")
            raise


# Singleton instance
tiktok_service = TikTokIntegrationService()
