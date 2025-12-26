"""
Smart Scheduler Service
Intelligent scheduling based on timezone, engagement patterns, and anti-ban measures
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import random
from sqlalchemy.orm import Session
from uuid import UUID
import pytz

from app.models.social_account import SocialAccount, ScheduledPost, Platform

logger = logging.getLogger(__name__)


class SmartSchedulerService:
    """Service for intelligent post scheduling"""

    def __init__(self):
        # Optimal posting times by platform (in UTC hours)
        self.optimal_hours = {
            Platform.INSTAGRAM: [13, 14, 15, 17, 18, 19],  # 1PM-3PM, 5PM-7PM UTC
            Platform.TIKTOK: [14, 15, 16, 18, 19, 20, 21],  # 2PM-4PM, 6PM-9PM UTC
            Platform.TWITTER: [12, 13, 17, 18],  # 12PM-1PM, 5PM-6PM UTC
            Platform.ONLYFANS: [20, 21, 22, 23]  # 8PM-11PM UTC (evening)
        }

        # Minimum time between posts (in hours)
        self.min_interval = {
            Platform.INSTAGRAM: 4,  # 4 hours
            Platform.TIKTOK: 3,  # 3 hours
            Platform.TWITTER: 1,  # 1 hour
            Platform.ONLYFANS: 6  # 6 hours
        }

        # Maximum posts per day
        self.max_posts_per_day = {
            Platform.INSTAGRAM: 3,
            Platform.TIKTOK: 5,
            Platform.TWITTER: 10,
            Platform.ONLYFANS: 2
        }

    def get_optimal_posting_time(
        self,
        platform: Platform,
        user_timezone: str = "America/New_York",
        target_date: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate optimal posting time based on timezone and engagement patterns

        Args:
            platform: Social media platform
            user_timezone: User's timezone (e.g., "America/New_York")
            target_date: Target date for posting (defaults to today)

        Returns:
            Optimal posting datetime in UTC
        """

        if target_date is None:
            target_date = datetime.utcnow()

        # Get optimal hours for platform
        optimal_hours = self.optimal_hours.get(platform, [12, 18])

        # Convert to user's timezone
        user_tz = pytz.timezone(user_timezone)
        utc = pytz.UTC

        # Get user's current time
        user_time = utc.localize(target_date).astimezone(user_tz)

        # Find next optimal hour in user's timezone
        current_hour = user_time.hour
        next_optimal_hours = [h for h in optimal_hours if h > current_hour]

        if not next_optimal_hours:
            # Use first optimal hour of next day
            next_optimal_hour = optimal_hours[0]
            user_time = user_time + timedelta(days=1)
        else:
            next_optimal_hour = next_optimal_hours[0]

        # Create datetime with optimal hour
        optimal_time = user_time.replace(
            hour=next_optimal_hour,
            minute=random.randint(0, 59),  # Randomize minutes
            second=0,
            microsecond=0
        )

        # Convert back to UTC
        return optimal_time.astimezone(utc).replace(tzinfo=None)

    def schedule_batch_posts(
        self,
        db: Session,
        social_account: SocialAccount,
        content_piece_ids: List[UUID],
        start_date: Optional[datetime] = None,
        use_pattern_randomization: bool = True
    ) -> List[ScheduledPost]:
        """
        Schedule multiple posts with anti-ban pattern randomization

        Args:
            db: Database session
            social_account: Social media account
            content_piece_ids: List of content piece IDs to schedule
            start_date: Start date for scheduling
            use_pattern_randomization: Apply anti-ban randomization

        Returns:
            List of created ScheduledPost objects
        """

        if start_date is None:
            start_date = datetime.utcnow()

        # Get user's timezone from account settings
        user_timezone = social_account.posting_schedule.get("timezone", "UTC")

        # Get existing scheduled posts count for today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        existing_posts_today = db.query(ScheduledPost).filter(
            ScheduledPost.social_account_id == social_account.id,
            ScheduledPost.scheduled_time >= today_start,
            ScheduledPost.scheduled_time < today_end,
            ScheduledPost.status == "pending"
        ).count()

        # Check daily limit
        max_daily = self.max_posts_per_day.get(social_account.platform, 3)

        scheduled_posts = []
        current_time = start_date
        posts_scheduled_today = existing_posts_today

        for idx, content_id in enumerate(content_piece_ids):
            # Check if we've hit daily limit
            if posts_scheduled_today >= max_daily:
                # Move to next day
                current_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                posts_scheduled_today = 0

            # Get optimal posting time
            optimal_time = self.get_optimal_posting_time(
                platform=social_account.platform,
                user_timezone=user_timezone,
                target_date=current_time
            )

            # Apply pattern randomization if enabled
            if use_pattern_randomization:
                optimal_time = self._apply_pattern_randomization(
                    scheduled_time=optimal_time,
                    platform=social_account.platform
                )

            # Get last post time for this account
            last_post = db.query(ScheduledPost).filter(
                ScheduledPost.social_account_id == social_account.id,
                ScheduledPost.status.in_(["pending", "published"])
            ).order_by(ScheduledPost.scheduled_time.desc()).first()

            if last_post:
                # Ensure minimum interval
                min_interval_hours = self.min_interval.get(social_account.platform, 4)
                min_time = last_post.scheduled_time + timedelta(hours=min_interval_hours)

                if optimal_time < min_time:
                    optimal_time = min_time

            # Create scheduled post
            scheduled_post = ScheduledPost(
                social_account_id=social_account.id,
                content_piece_id=content_id,
                avatar_id=social_account.avatar_id,
                scheduled_time=optimal_time,
                timezone=user_timezone,
                status="pending",
                metadata={
                    "scheduler_version": "smart_v1",
                    "pattern_randomization": use_pattern_randomization
                }
            )

            db.add(scheduled_post)
            scheduled_posts.append(scheduled_post)

            # Update counters
            current_time = optimal_time
            posts_scheduled_today += 1

        db.commit()

        logger.info(f"Scheduled {len(scheduled_posts)} posts for account {social_account.id}")

        return scheduled_posts

    def _apply_pattern_randomization(
        self,
        scheduled_time: datetime,
        platform: Platform
    ) -> datetime:
        """
        Apply pattern randomization to avoid detection (E04-004)

        Randomizes:
        - Posting time (±30 minutes)
        - Day of week variation
        """

        # Randomize minutes (±30 minutes)
        minute_offset = random.randint(-30, 30)
        randomized_time = scheduled_time + timedelta(minutes=minute_offset)

        # Randomly skip a day occasionally (10% chance)
        if random.random() < 0.1:
            randomized_time += timedelta(days=1)
            logger.info(f"Pattern randomization: Skipped a day for {platform.value}")

        return randomized_time

    def reschedule_failed_post(
        self,
        db: Session,
        scheduled_post: ScheduledPost,
        retry_delay_hours: int = 2
    ) -> ScheduledPost:
        """
        Reschedule a failed post with exponential backoff

        Args:
            db: Database session
            scheduled_post: Failed scheduled post
            retry_delay_hours: Hours to wait before retry

        Returns:
            Updated ScheduledPost
        """

        retry_count = int(scheduled_post.retry_count)

        if retry_count >= 3:
            # Max retries exceeded
            scheduled_post.status = "failed"
            logger.error(f"Post {scheduled_post.id} failed after 3 retries")
        else:
            # Calculate retry time with exponential backoff
            backoff_multiplier = 2 ** retry_count  # 1x, 2x, 4x
            retry_delay = retry_delay_hours * backoff_multiplier

            new_time = datetime.utcnow() + timedelta(hours=retry_delay)

            # Update scheduled post
            scheduled_post.scheduled_time = new_time
            scheduled_post.retry_count = str(retry_count + 1)
            scheduled_post.status = "pending"

            logger.info(f"Rescheduled post {scheduled_post.id} to {new_time} (retry {retry_count + 1})")

        db.commit()
        return scheduled_post

    def get_next_posts_to_publish(
        self,
        db: Session,
        limit: int = 100
    ) -> List[ScheduledPost]:
        """
        Get posts that are ready to be published

        Args:
            db: Database session
            limit: Maximum number of posts to retrieve

        Returns:
            List of posts ready for publishing
        """

        now = datetime.utcnow()

        posts = db.query(ScheduledPost).filter(
            ScheduledPost.status == "pending",
            ScheduledPost.scheduled_time <= now
        ).order_by(ScheduledPost.scheduled_time).limit(limit).all()

        return posts

    def analyze_engagement_patterns(
        self,
        db: Session,
        social_account_id: UUID,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze engagement patterns to optimize future posting times

        Args:
            db: Database session
            social_account_id: Social account ID
            days_back: Number of days to analyze

        Returns:
            Engagement analysis with optimal posting times
        """

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Get published posts
        posts = db.query(ScheduledPost).filter(
            ScheduledPost.social_account_id == social_account_id,
            ScheduledPost.status == "published",
            ScheduledPost.published_at >= cutoff_date
        ).all()

        if not posts:
            return {
                "posts_analyzed": 0,
                "optimal_hours": [],
                "message": "Not enough data"
            }

        # Analyze by hour of day
        hour_engagement = {}

        for post in posts:
            hour = post.published_at.hour
            engagement = post.metadata.get("engagement_score", 0)

            if hour not in hour_engagement:
                hour_engagement[hour] = []

            hour_engagement[hour].append(engagement)

        # Calculate average engagement by hour
        hour_averages = {
            hour: sum(scores) / len(scores)
            for hour, scores in hour_engagement.items()
        }

        # Get top 5 hours
        optimal_hours = sorted(hour_averages.keys(), key=lambda h: hour_averages[h], reverse=True)[:5]

        return {
            "posts_analyzed": len(posts),
            "optimal_hours": optimal_hours,
            "hour_averages": hour_averages,
            "recommendation": f"Best times to post: {', '.join([f'{h}:00' for h in optimal_hours])}"
        }


# Singleton instance
smart_scheduler = SmartSchedulerService()
