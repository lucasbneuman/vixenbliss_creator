"""
Lead Scoring Service
ML-based lead scoring and conversion probability prediction (E06-003)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.models.conversation import (
    Conversation,
    Message,
    UpsellEvent,
    FunnelStage,
    LeadQualification,
    SenderType
)

logger = logging.getLogger(__name__)


class LeadScoringService:
    """
    Advanced lead scoring system with ML-based conversion prediction

    Scoring algorithm factors:
    - Message frequency and engagement (30%)
    - Sentiment trend (20%)
    - Funnel progression speed (20%)
    - Response time (15%)
    - Content of messages (15%)
    """

    def __init__(self):
        # Scoring weights
        self.weights = {
            "message_frequency": 0.30,
            "sentiment_trend": 0.20,
            "funnel_progression": 0.20,
            "response_time": 0.15,
            "message_content": 0.15
        }

        # Conversion probability thresholds
        self.conversion_thresholds = {
            "high": 0.70,  # >70% likely to convert
            "medium": 0.40,  # 40-70% likely
            "low": 0.40  # <40% likely
        }

    def calculate_lead_score(
        self,
        db: Session,
        conversation: Conversation
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive lead score (0-100) with ML-based conversion probability

        Args:
            db: Database session
            conversation: Conversation object

        Returns:
            Dictionary with score, probability, and breakdown
        """

        logger.info(f"Calculating lead score for conversation {conversation.id}")

        # Get all messages for this conversation
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).all()

        if not messages:
            return {
                "lead_score": 10,
                "conversion_probability": 0.05,
                "qualification": LeadQualification.COLD_LEAD.value,
                "breakdown": {},
                "recommendation": "Wait for user engagement"
            }

        # Calculate individual scoring components
        message_freq_score = self._calculate_message_frequency_score(conversation, messages)
        sentiment_score = self._calculate_sentiment_trend_score(messages)
        funnel_score = self._calculate_funnel_progression_score(conversation, messages)
        response_time_score = self._calculate_response_time_score(messages)
        content_score = self._calculate_message_content_score(messages)

        # Calculate weighted total score (0-100)
        total_score = (
            message_freq_score * self.weights["message_frequency"] +
            sentiment_score * self.weights["sentiment_trend"] +
            funnel_score * self.weights["funnel_progression"] +
            response_time_score * self.weights["response_time"] +
            content_score * self.weights["message_content"]
        )

        total_score = min(100, max(0, total_score))

        # Calculate conversion probability (0.0-1.0)
        conversion_probability = self._predict_conversion_probability(
            total_score,
            conversation,
            messages
        )

        # Determine qualification status
        if total_score >= 71:
            qualification = LeadQualification.HOT_LEAD
        elif total_score >= 41:
            qualification = LeadQualification.WARM_LEAD
        else:
            qualification = LeadQualification.COLD_LEAD

        # Generate recommendation
        recommendation = self._generate_scoring_recommendation(
            total_score,
            conversion_probability,
            conversation
        )

        return {
            "lead_score": int(total_score),
            "conversion_probability": round(conversion_probability, 3),
            "qualification": qualification.value,
            "breakdown": {
                "message_frequency": round(message_freq_score, 1),
                "sentiment_trend": round(sentiment_score, 1),
                "funnel_progression": round(funnel_score, 1),
                "response_time": round(response_time_score, 1),
                "message_content": round(content_score, 1)
            },
            "recommendation": recommendation,
            "last_updated": datetime.utcnow().isoformat()
        }

    def _calculate_message_frequency_score(
        self,
        conversation: Conversation,
        messages: List[Message]
    ) -> float:
        """Score based on message frequency and engagement (0-100)"""

        user_messages = [m for m in messages if m.sender_type == SenderType.USER]

        if not user_messages:
            return 0.0

        # Messages per day
        conversation_age_days = (datetime.utcnow() - conversation.created_at).days + 1
        messages_per_day = len(user_messages) / conversation_age_days

        # Score calculation
        if messages_per_day >= 5:
            return 100.0
        elif messages_per_day >= 3:
            return 80.0
        elif messages_per_day >= 1:
            return 50.0
        elif messages_per_day >= 0.5:
            return 30.0
        else:
            return 10.0

    def _calculate_sentiment_trend_score(self, messages: List[Message]) -> float:
        """Score based on sentiment trend (0-100)"""

        # Get messages with sentiment scores
        messages_with_sentiment = [
            m for m in messages
            if m.sentiment_score is not None and m.sender_type == SenderType.USER
        ]

        if not messages_with_sentiment:
            return 50.0  # Neutral

        # Calculate average sentiment
        avg_sentiment = sum(m.sentiment_score for m in messages_with_sentiment) / len(messages_with_sentiment)

        # Check if sentiment is improving (recent messages more positive)
        if len(messages_with_sentiment) >= 3:
            recent_sentiment = sum(m.sentiment_score for m in messages_with_sentiment[-3:]) / 3
            early_sentiment = sum(m.sentiment_score for m in messages_with_sentiment[:3]) / 3

            sentiment_trend = recent_sentiment - early_sentiment
        else:
            sentiment_trend = 0.0

        # Convert sentiment to score (0-100)
        # Sentiment ranges from -1.0 (negative) to 1.0 (positive)
        sentiment_score = (avg_sentiment + 1.0) * 50  # Maps -1..1 to 0..100

        # Apply trend bonus/penalty
        if sentiment_trend > 0.2:
            sentiment_score += 15
        elif sentiment_trend < -0.2:
            sentiment_score -= 15

        return min(100.0, max(0.0, sentiment_score))

    def _calculate_funnel_progression_score(
        self,
        conversation: Conversation,
        messages: List[Message]
    ) -> float:
        """Score based on funnel progression speed (0-100)"""

        conversation_age_hours = (datetime.utcnow() - conversation.created_at).total_seconds() / 3600

        # Base score by current funnel stage
        if conversation.funnel_stage == FunnelStage.CONVERSION:
            base_score = 90.0
        elif conversation.funnel_stage == FunnelStage.QUALIFICATION:
            base_score = 60.0
        else:  # LEAD_MAGNET
            base_score = 30.0

        # Adjust for progression speed
        if conversation.funnel_stage == FunnelStage.CONVERSION:
            if conversation_age_hours < 24:
                return 100.0  # Very fast progression
            elif conversation_age_hours < 48:
                return 90.0
            else:
                return 80.0

        elif conversation.funnel_stage == FunnelStage.QUALIFICATION:
            if conversation_age_hours < 12:
                return 75.0
            elif conversation_age_hours < 24:
                return 65.0
            else:
                return 55.0

        else:  # Still in lead magnet
            if conversation_age_hours > 48:
                return 20.0  # Slow progression
            else:
                return 35.0

    def _calculate_response_time_score(self, messages: List[Message]) -> float:
        """Score based on user's response time (0-100)"""

        user_messages = [m for m in messages if m.sender_type == SenderType.USER]

        if len(user_messages) < 2:
            return 50.0  # Not enough data

        # Calculate average time between user messages
        response_times = []

        for i in range(1, len(user_messages)):
            time_diff = (user_messages[i].created_at - user_messages[i-1].created_at).total_seconds() / 60
            response_times.append(time_diff)

        avg_response_time_minutes = sum(response_times) / len(response_times)

        # Score based on response speed
        if avg_response_time_minutes < 5:
            return 100.0  # Very engaged
        elif avg_response_time_minutes < 30:
            return 80.0
        elif avg_response_time_minutes < 120:
            return 60.0
        elif avg_response_time_minutes < 360:
            return 40.0
        else:
            return 20.0

    def _calculate_message_content_score(self, messages: List[Message]) -> float:
        """Score based on message content quality (0-100)"""

        user_messages = [m for m in messages if m.sender_type == SenderType.USER]

        if not user_messages:
            return 0.0

        # Check for intent signals
        purchase_intent_keywords = [
            "buy", "purchase", "price", "cost", "how much", "subscribe",
            "premium", "exclusive", "custom", "special", "interested"
        ]

        question_keywords = ["what", "how", "when", "where", "why", "can you", "do you"]

        purchase_intent_count = 0
        question_count = 0
        total_length = 0

        for msg in user_messages:
            text_lower = msg.message_text.lower()

            # Count purchase intent signals
            if any(keyword in text_lower for keyword in purchase_intent_keywords):
                purchase_intent_count += 1

            # Count questions (shows engagement)
            if any(keyword in text_lower for keyword in question_keywords):
                question_count += 1

            total_length += len(msg.message_text)

        # Calculate score
        avg_message_length = total_length / len(user_messages)

        score = 30.0  # Base score

        # Longer messages = more engaged
        if avg_message_length > 50:
            score += 20.0
        elif avg_message_length > 20:
            score += 10.0

        # Purchase intent signals
        score += min(30.0, purchase_intent_count * 15.0)

        # Questions show engagement
        score += min(20.0, question_count * 10.0)

        return min(100.0, score)

    def _predict_conversion_probability(
        self,
        lead_score: float,
        conversation: Conversation,
        messages: List[Message]
    ) -> float:
        """
        Predict conversion probability using sigmoid function

        Args:
            lead_score: Calculated lead score (0-100)
            conversation: Conversation object
            messages: List of messages

        Returns:
            Conversion probability (0.0-1.0)
        """

        # Base probability from lead score
        # Use sigmoid function for smooth probability curve
        import math

        # Normalize score to 0-10 range
        normalized_score = lead_score / 10

        # Sigmoid: P = 1 / (1 + e^(-k*(x - x0)))
        # k = steepness, x0 = midpoint
        k = 0.8
        x0 = 5.0

        base_probability = 1 / (1 + math.exp(-k * (normalized_score - x0)))

        # Apply boosters/penalties
        probability = base_probability

        # Boost if already in conversion stage
        if conversation.funnel_stage == FunnelStage.CONVERSION:
            probability *= 1.3

        # Boost if high message frequency
        if conversation.message_count > 20:
            probability *= 1.15

        # Penalty if conversation is stale
        hours_since_last_message = (datetime.utcnow() - conversation.last_message_at).total_seconds() / 3600 if conversation.last_message_at else 999

        if hours_since_last_message > 48:
            probability *= 0.7
        elif hours_since_last_message > 24:
            probability *= 0.85

        # Cap at 0.95 (never 100% certain)
        probability = min(0.95, probability)

        return probability

    def _generate_scoring_recommendation(
        self,
        lead_score: float,
        conversion_probability: float,
        conversation: Conversation
    ) -> str:
        """Generate actionable recommendation based on score"""

        if lead_score >= 80 and conversion_probability >= 0.7:
            return "HIGH PRIORITY: Present premium offer immediately. Very likely to convert."

        elif lead_score >= 60 and conversion_probability >= 0.5:
            return "WARM LEAD: Continue engagement, present mid-tier offer soon."

        elif lead_score >= 40 and conversion_probability >= 0.3:
            return "NURTURE: Build more rapport before presenting offers."

        elif lead_score < 40:
            if conversation.message_count < 5:
                return "NEW LEAD: Focus on value delivery and engagement."
            else:
                return "LOW ENGAGEMENT: Consider re-engagement campaign or pause."

        else:
            return "CONTINUE CURRENT STRATEGY: Monitor for engagement signals."

    def bulk_rescore_conversations(
        self,
        db: Session,
        user_id: Optional[UUID] = None,
        avatar_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Recalculate scores for multiple conversations

        Args:
            db: Database session
            user_id: Filter by user ID (optional)
            avatar_id: Filter by avatar ID (optional)

        Returns:
            List of updated scoring results
        """

        query = db.query(Conversation).filter(Conversation.is_active == True)

        if user_id:
            query = query.filter(Conversation.user_id == user_id)

        if avatar_id:
            query = query.filter(Conversation.avatar_id == avatar_id)

        conversations = query.all()

        results = []

        for conversation in conversations:
            score_data = self.calculate_lead_score(db, conversation)

            # Update conversation
            conversation.lead_score = score_data["lead_score"]
            conversation.conversion_probability = score_data["conversion_probability"]
            conversation.update_lead_score(score_data["lead_score"])

            results.append({
                "conversation_id": str(conversation.id),
                "lead_username": conversation.lead_username,
                **score_data
            })

        db.commit()

        logger.info(f"Rescored {len(results)} conversations")

        return results


# Singleton instance
lead_scoring_service = LeadScoringService()
