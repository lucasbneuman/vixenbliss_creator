"""
Health Monitoring Service
Monitor social media accounts for shadowban, rate limits, and suspicious activity
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.social_account import SocialAccount, AccountStatus, Platform
from app.services.instagram_integration import instagram_service
from app.services.tiktok_integration import tiktok_service

logger = logging.getLogger(__name__)


class HealthMonitoringService:
    """Service for monitoring social media account health"""

    def __init__(self):
        self.platform_services = {
            Platform.INSTAGRAM: instagram_service,
            Platform.TIKTOK: tiktok_service
        }

        # Health check intervals (in hours)
        self.check_intervals = {
            Platform.INSTAGRAM: 6,  # Every 6 hours
            Platform.TIKTOK: 4,  # Every 4 hours
            Platform.TWITTER: 6,
            Platform.ONLYFANS: 12
        }

        # Critical health thresholds
        self.critical_thresholds = {
            "health_score_min": 50,
            "consecutive_failures": 3,
            "rate_limit_duration_hours": 24
        }

    async def check_account_health(
        self,
        db: Session,
        social_account: SocialAccount
    ) -> Dict[str, Any]:
        """
        Comprehensive health check for a social media account

        Args:
            db: Database session
            social_account: Social account to check

        Returns:
            Health report with status, issues, and recommendations
        """

        logger.info(f"Running health check for {social_account.platform.value} account {social_account.id}")

        # Decrypt access token
        service = self.platform_services.get(social_account.platform)

        if not service:
            logger.warning(f"No service available for platform {social_account.platform.value}")
            return {
                "healthy": False,
                "error": f"Platform {social_account.platform.value} not supported"
            }

        try:
            decrypted_token = service.decrypt_token(social_account.access_token)

            # Run platform-specific health check
            health_result = await service.check_account_health(decrypted_token)

            # Update social account with health data
            social_account.health_score = str(health_result["health_score"])
            social_account.last_health_check = datetime.utcnow()

            # Determine account status
            new_status = self._determine_account_status(health_result, social_account)

            if new_status != social_account.status:
                logger.warning(f"Account {social_account.id} status changed: {social_account.status} → {new_status}")
                social_account.status = new_status

                # Send alert if account became unhealthy
                if new_status in [AccountStatus.SHADOWBANNED, AccountStatus.SUSPENDED, AccountStatus.RATE_LIMITED]:
                    await self._send_health_alert(social_account, health_result)

            # Update metadata
            social_account.metadata["last_health_check"] = health_result
            social_account.metadata["health_history"] = social_account.metadata.get("health_history", [])
            social_account.metadata["health_history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "health_score": health_result["health_score"],
                "status": new_status.value
            })

            # Keep only last 30 health checks
            social_account.metadata["health_history"] = social_account.metadata["health_history"][-30:]

            db.commit()

            return {
                "account_id": str(social_account.id),
                "platform": social_account.platform.value,
                "username": social_account.username,
                "healthy": health_result["healthy"],
                "health_score": health_result["health_score"],
                "status": new_status.value,
                "issues": self._identify_issues(health_result),
                "recommendations": self._generate_recommendations(health_result, social_account),
                "last_checked": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed for account {social_account.id}: {str(e)}")

            # Mark as disconnected if token is invalid
            if "token" in str(e).lower() or "auth" in str(e).lower():
                social_account.status = AccountStatus.DISCONNECTED

            social_account.health_score = "0"
            social_account.last_health_check = datetime.utcnow()
            db.commit()

            return {
                "account_id": str(social_account.id),
                "healthy": False,
                "health_score": 0,
                "error": str(e),
                "status": social_account.status.value
            }

    def _determine_account_status(
        self,
        health_result: Dict[str, Any],
        social_account: SocialAccount
    ) -> AccountStatus:
        """Determine account status based on health check results"""

        # Check for shadowban
        if health_result.get("shadowbanned"):
            return AccountStatus.SHADOWBANNED

        # Check for rate limiting
        if health_result.get("rate_limited"):
            return AccountStatus.RATE_LIMITED

        # Check health score
        health_score = health_result.get("health_score", 0)

        if health_score < self.critical_thresholds["health_score_min"]:
            return AccountStatus.SUSPENDED

        # Account is healthy
        return AccountStatus.ACTIVE

    def _identify_issues(self, health_result: Dict[str, Any]) -> List[str]:
        """Identify specific issues from health check"""

        issues = []

        if health_result.get("shadowbanned"):
            issues.append("Account appears to be shadowbanned")

        if health_result.get("rate_limited"):
            issues.append("Rate limit detected - posting paused")

        if health_result.get("health_score", 100) < 50:
            issues.append("Low health score - account may have restrictions")

        if health_result.get("engagement_rate", 0) < 1:
            issues.append("Low engagement rate detected")

        if health_result.get("error"):
            issues.append(f"Error: {health_result['error']}")

        return issues

    def _generate_recommendations(
        self,
        health_result: Dict[str, Any],
        social_account: SocialAccount
    ) -> List[str]:
        """Generate recommendations based on health status"""

        recommendations = []

        health_score = health_result.get("health_score", 0)

        if health_score < 50:
            recommendations.append("Pause automated posting for 48 hours")
            recommendations.append("Review recent content for policy violations")

        if health_result.get("shadowbanned"):
            recommendations.append("Stop posting for 7-14 days")
            recommendations.append("Avoid using banned hashtags")
            recommendations.append("Engage naturally with other accounts")

        if health_result.get("rate_limited"):
            recommendations.append("Wait 24 hours before resuming posting")
            recommendations.append("Reduce posting frequency")

        if health_result.get("engagement_rate", 100) < 1:
            recommendations.append("Improve content quality")
            recommendations.append("Post at optimal times")
            recommendations.append("Use better hashtags and captions")

        return recommendations

    async def _send_health_alert(
        self,
        social_account: SocialAccount,
        health_result: Dict[str, Any]
    ):
        """Send alert when account health is critical"""

        logger.critical(
            f"HEALTH ALERT: {social_account.platform.value} account {social_account.username} "
            f"is {social_account.status.value} (health score: {health_result['health_score']})"
        )

        # In production, send email/Slack/Discord notification
        # For now, just log

    async def check_all_accounts(self, db: Session) -> List[Dict[str, Any]]:
        """
        Check health of all active social accounts

        Args:
            db: Database session

        Returns:
            List of health check results
        """

        # Get all accounts that need checking
        accounts_to_check = self._get_accounts_needing_check(db)

        logger.info(f"Checking health for {len(accounts_to_check)} accounts")

        results = []

        for account in accounts_to_check:
            try:
                result = await self.check_account_health(db, account)
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to check account {account.id}: {str(e)}")
                results.append({
                    "account_id": str(account.id),
                    "error": str(e),
                    "healthy": False
                })

        return results

    def _get_accounts_needing_check(self, db: Session) -> List[SocialAccount]:
        """Get accounts that need health checking"""

        accounts = []

        for platform in Platform:
            check_interval_hours = self.check_intervals.get(platform, 6)
            cutoff_time = datetime.utcnow() - timedelta(hours=check_interval_hours)

            # Get accounts that haven't been checked recently
            platform_accounts = db.query(SocialAccount).filter(
                SocialAccount.platform == platform,
                (
                    (SocialAccount.last_health_check.is_(None)) |
                    (SocialAccount.last_health_check < cutoff_time)
                ),
                SocialAccount.status.in_([
                    AccountStatus.ACTIVE,
                    AccountStatus.RATE_LIMITED,
                    AccountStatus.SHADOWBANNED
                ])
            ).all()

            accounts.extend(platform_accounts)

        return accounts

    async def auto_pause_unhealthy_accounts(self, db: Session) -> int:
        """
        Automatically pause posting for unhealthy accounts

        Args:
            db: Database session

        Returns:
            Number of accounts paused
        """

        unhealthy_accounts = db.query(SocialAccount).filter(
            SocialAccount.status.in_([
                AccountStatus.SHADOWBANNED,
                AccountStatus.SUSPENDED,
                AccountStatus.RATE_LIMITED
            ]),
            SocialAccount.auto_post_enabled == True
        ).all()

        paused_count = 0

        for account in unhealthy_accounts:
            account.auto_post_enabled = False
            account.metadata["auto_paused_at"] = datetime.utcnow().isoformat()
            account.metadata["auto_paused_reason"] = account.status.value
            paused_count += 1

            logger.warning(f"Auto-paused posting for account {account.id} ({account.status.value})")

        db.commit()

        return paused_count

    def get_health_dashboard_data(self, db: Session, user_id: UUID) -> Dict[str, Any]:
        """
        Get health dashboard data for all user accounts

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dashboard data with account health overview
        """

        accounts = db.query(SocialAccount).filter(
            SocialAccount.user_id == user_id
        ).all()

        platform_summary = {}

        for platform in Platform:
            platform_accounts = [a for a in accounts if a.platform == platform]

            if not platform_accounts:
                continue

            healthy_count = len([a for a in platform_accounts if a.status == AccountStatus.ACTIVE])
            total_count = len(platform_accounts)

            avg_health_score = sum(int(a.health_score) for a in platform_accounts) / total_count if total_count > 0 else 0

            platform_summary[platform.value] = {
                "total_accounts": total_count,
                "healthy_accounts": healthy_count,
                "unhealthy_accounts": total_count - healthy_count,
                "average_health_score": round(avg_health_score, 1),
                "accounts": [
                    {
                        "id": str(a.id),
                        "username": a.username,
                        "status": a.status.value,
                        "health_score": int(a.health_score),
                        "last_checked": a.last_health_check.isoformat() if a.last_health_check else None
                    }
                    for a in platform_accounts
                ]
            }

        return {
            "total_accounts": len(accounts),
            "healthy_accounts": len([a for a in accounts if a.status == AccountStatus.ACTIVE]),
            "platforms": platform_summary,
            "last_updated": datetime.utcnow().isoformat()
        }


# Singleton instance
health_monitoring_service = HealthMonitoringService()
