"""
Social Integration Base Service
Common functionality for all social media integrations
"""

import os
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class SocialIntegrationService(ABC):
    """Base class for social media platform integrations"""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
        self.fernet = Fernet(self.encryption_key)

    # Encryption
    def encrypt_token(self, token: str) -> str:
        """Encrypt access token for storage"""
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt access token"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    # OAuth
    @abstractmethod
    async def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        pass

    @abstractmethod
    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        pass

    # Account Info
    @abstractmethod
    async def get_account_info(self, access_token: str) -> Dict[str, Any]:
        """Get account information from platform"""
        pass

    # Content Publishing
    @abstractmethod
    async def publish_post(
        self,
        access_token: str,
        media_urls: list[str],
        caption: Optional[str] = None,
        hashtags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish post to platform"""
        pass

    @abstractmethod
    async def delete_post(self, access_token: str, post_id: str) -> bool:
        """Delete post from platform"""
        pass

    # Health Monitoring
    @abstractmethod
    async def check_account_health(self, access_token: str) -> Dict[str, Any]:
        """Check account health status"""
        pass

    async def detect_shadowban(self, access_token: str) -> bool:
        """Detect if account is shadowbanned"""
        # Default implementation - override in platform-specific services
        try:
            health = await self.check_account_health(access_token)
            return health.get("shadowbanned", False)
        except Exception as e:
            logger.error(f"Shadowban detection failed: {str(e)}")
            return False

    async def check_rate_limits(self, access_token: str) -> Dict[str, Any]:
        """Check current rate limit status"""
        # Default implementation - override in platform-specific services
        return {
            "rate_limited": False,
            "reset_at": None,
            "remaining_requests": None
        }

    # Retry Logic
    async def publish_with_retry(
        self,
        access_token: str,
        media_urls: list[str],
        caption: Optional[str] = None,
        hashtags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Publish post with exponential backoff retry"""

        last_error = None

        for attempt in range(max_retries):
            try:
                result = await self.publish_post(
                    access_token=access_token,
                    media_urls=media_urls,
                    caption=caption,
                    hashtags=hashtags,
                    metadata=metadata
                )

                logger.info(f"Post published successfully on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Publish attempt {attempt + 1} failed: {str(e)}")

                # Check if it's a rate limit error
                if "rate limit" in str(e).lower() or "429" in str(e):
                    # Wait longer for rate limits
                    wait_time = 60 * (2 ** attempt)  # 60s, 120s, 240s
                    logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                elif attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

        # All retries failed
        logger.error(f"All {max_retries} publish attempts failed")
        raise Exception(f"Failed to publish after {max_retries} attempts: {str(last_error)}")

    # Helper Methods
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=timeout
                )

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"{self.platform_name} API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"{self.platform_name} API error: {e.response.status_code}")

            except httpx.RequestError as e:
                logger.error(f"{self.platform_name} request failed: {str(e)}")
                raise Exception(f"Request to {self.platform_name} failed: {str(e)}")

    def _add_hashtags_to_caption(self, caption: str, hashtags: list[str]) -> str:
        """Add hashtags to caption"""
        if not hashtags:
            return caption

        hashtag_str = " ".join([f"#{tag.lstrip('#')}" for tag in hashtags])
        return f"{caption}\n\n{hashtag_str}" if caption else hashtag_str


import asyncio
