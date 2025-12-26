"""
A/B Testing Service
Test different chatbot strategies for optimization (E06-005)
"""

import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
import math

from app.models.conversation import ABTestVariant, Conversation

logger = logging.getLogger(__name__)


class ABTestingService:
    """
    A/B testing framework for chatbot optimization

    Test elements:
    - Welcome messages
    - CTAs (call-to-actions)
    - Pricing offers
    - Objection handling
    - Message tone
    """

    def __init__(self):
        # Statistical significance threshold
        self.confidence_threshold = 0.95  # 95% confidence level

        # Minimum sample size for valid test
        self.min_sample_size = 30

    def create_ab_test(
        self,
        db: Session,
        test_name: str,
        element_type: str,
        variants: List[Dict[str, Any]],
        description: Optional[str] = None
    ) -> List[ABTestVariant]:
        """
        Create A/B test with multiple variants

        Args:
            db: Database session
            test_name: Name of test (e.g., "welcome_message_test_v1")
            element_type: Type of element (welcome_message, cta, pricing_offer, objection_response)
            variants: List of variant configurations
            description: Test description

        Returns:
            List of created ABTestVariant objects

        Example variants:
        [
            {
                "variant_name": "control",
                "element_content": {"message": "Hey! 😊 Thanks for reaching out!"},
                "traffic_percentage": 50.0
            },
            {
                "variant_name": "variant_a",
                "element_content": {"message": "Hi there! 💕 Excited to chat with you!"},
                "traffic_percentage": 50.0
            }
        ]
        """

        # Validate traffic percentages sum to 100
        total_traffic = sum(v["traffic_percentage"] for v in variants)

        if not math.isclose(total_traffic, 100.0, rel_tol=0.01):
            raise ValueError(f"Traffic percentages must sum to 100%, got {total_traffic}%")

        created_variants = []

        for variant_config in variants:
            variant = ABTestVariant(
                test_name=test_name,
                variant_name=variant_config["variant_name"],
                description=description,
                element_type=element_type,
                element_content=variant_config["element_content"],
                traffic_percentage=variant_config["traffic_percentage"],
                is_active=True,
                test_started_at=datetime.utcnow()
            )

            db.add(variant)
            created_variants.append(variant)

        db.commit()

        for variant in created_variants:
            db.refresh(variant)

        logger.info(f"Created A/B test '{test_name}' with {len(created_variants)} variants")

        return created_variants

    def assign_variant(
        self,
        db: Session,
        test_name: str
    ) -> Optional[ABTestVariant]:
        """
        Assign a variant to a new conversation using traffic allocation

        Args:
            db: Database session
            test_name: Name of test

        Returns:
            Assigned ABTestVariant or None if test not found
        """

        # Get active variants for this test
        variants = db.query(ABTestVariant).filter(
            ABTestVariant.test_name == test_name,
            ABTestVariant.is_active == True
        ).all()

        if not variants:
            logger.warning(f"No active variants found for test '{test_name}'")
            return None

        # Use weighted random selection based on traffic percentage
        rand_value = random.uniform(0, 100)
        cumulative = 0.0

        for variant in variants:
            cumulative += variant.traffic_percentage

            if rand_value <= cumulative:
                logger.info(f"Assigned variant '{variant.variant_name}' for test '{test_name}'")
                return variant

        # Fallback to first variant
        return variants[0]

    def record_conversation_outcome(
        self,
        db: Session,
        conversation: Conversation,
        converted: bool = False,
        revenue: float = 0.0
    ):
        """
        Record outcome of conversation in A/B test

        Args:
            db: Database session
            conversation: Conversation object
            converted: Whether conversation converted
            revenue: Revenue generated
        """

        if not conversation.ab_test_variant_id:
            return  # Not part of A/B test

        variant = db.query(ABTestVariant).filter(
            ABTestVariant.id == conversation.ab_test_variant_id
        ).first()

        if not variant:
            logger.warning(f"Variant {conversation.ab_test_variant_id} not found")
            return

        # Update variant metrics
        variant.update_metrics(conversion=converted, revenue=revenue)

        # If variant has enough samples, calculate statistical significance
        if variant.total_conversations >= self.min_sample_size:
            self._calculate_statistical_significance(db, variant)

        db.commit()

        logger.info(f"Recorded outcome for variant '{variant.variant_name}': converted={converted}, revenue=${revenue}")

    def _calculate_statistical_significance(
        self,
        db: Session,
        variant: ABTestVariant
    ):
        """
        Calculate statistical significance using z-test for proportions

        Args:
            db: Database session
            variant: Variant to test
        """

        # Get all variants for this test
        all_variants = db.query(ABTestVariant).filter(
            ABTestVariant.test_name == variant.test_name,
            ABTestVariant.is_active == True
        ).all()

        if len(all_variants) < 2:
            return  # Need at least 2 variants to compare

        # Find control variant (usually named "control")
        control_variant = next((v for v in all_variants if v.variant_name == "control"), all_variants[0])

        if control_variant.id == variant.id:
            return  # Don't compare control to itself

        # Check if both have minimum sample size
        if control_variant.total_conversations < self.min_sample_size or variant.total_conversations < self.min_sample_size:
            return

        # Calculate z-score for proportion difference
        p1 = control_variant.conversion_rate / 100.0
        p2 = variant.conversion_rate / 100.0
        n1 = control_variant.total_conversations
        n2 = variant.total_conversations

        # Pooled proportion
        p_pool = (control_variant.total_conversions + variant.total_conversions) / (n1 + n2)

        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

        if se == 0:
            return

        # Z-score
        z = (p2 - p1) / se

        # Calculate confidence level (two-tailed test)
        # For z = 1.96, confidence = 0.95 (95%)
        confidence = self._calculate_confidence_from_z(abs(z))

        variant.confidence_level = confidence

        # Check if variant is statistically significant winner
        if confidence >= self.confidence_threshold and p2 > p1:
            variant.is_winner = True
            logger.info(f"Variant '{variant.variant_name}' is statistically significant winner (confidence: {confidence:.3f})")
        else:
            variant.is_winner = False

    def _calculate_confidence_from_z(self, z_score: float) -> float:
        """Calculate confidence level from z-score using normal distribution"""

        # Approximate using error function
        # For two-tailed test: confidence = erf(z / sqrt(2))

        try:
            confidence = math.erf(z_score / math.sqrt(2))
            return confidence
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {str(e)}")
            return 0.0

    def get_test_results(
        self,
        db: Session,
        test_name: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive results for an A/B test

        Args:
            db: Database session
            test_name: Name of test

        Returns:
            Test results with metrics for all variants
        """

        variants = db.query(ABTestVariant).filter(
            ABTestVariant.test_name == test_name
        ).all()

        if not variants:
            raise ValueError(f"Test '{test_name}' not found")

        # Find winner
        winner = next((v for v in variants if v.is_winner), None)

        # Calculate overall test metrics
        total_conversations = sum(v.total_conversations for v in variants)
        total_conversions = sum(v.total_conversions for v in variants)
        total_revenue = sum(v.avg_revenue_per_conversation * v.total_conversations for v in variants)

        overall_conversion_rate = (total_conversions / total_conversations * 100) if total_conversations > 0 else 0.0

        # Build variant results
        variant_results = []

        for variant in variants:
            variant_results.append({
                "variant_id": str(variant.id),
                "variant_name": variant.variant_name,
                "element_content": variant.element_content,
                "traffic_percentage": variant.traffic_percentage,
                "total_conversations": variant.total_conversations,
                "total_conversions": variant.total_conversions,
                "conversion_rate": variant.conversion_rate,
                "avg_revenue_per_conversation": variant.avg_revenue_per_conversation,
                "total_revenue": variant.avg_revenue_per_conversation * variant.total_conversations,
                "confidence_level": variant.confidence_level,
                "is_winner": variant.is_winner,
                "is_active": variant.is_active
            })

        # Sort by conversion rate
        variant_results.sort(key=lambda x: x["conversion_rate"], reverse=True)

        return {
            "test_name": test_name,
            "element_type": variants[0].element_type,
            "test_started_at": variants[0].test_started_at.isoformat() if variants[0].test_started_at else None,
            "test_ended_at": variants[0].test_ended_at.isoformat() if variants[0].test_ended_at else None,
            "total_conversations": total_conversations,
            "total_conversions": total_conversions,
            "overall_conversion_rate": round(overall_conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "winner": {
                "variant_name": winner.variant_name,
                "conversion_rate": winner.conversion_rate,
                "confidence_level": winner.confidence_level
            } if winner else None,
            "variants": variant_results,
            "recommendations": self._generate_test_recommendations(variants, winner),
            "last_updated": datetime.utcnow().isoformat()
        }

    def _generate_test_recommendations(
        self,
        variants: List[ABTestVariant],
        winner: Optional[ABTestVariant]
    ) -> List[str]:
        """Generate actionable recommendations from test results"""

        recommendations = []

        # Check sample size
        total_conversations = sum(v.total_conversations for v in variants)

        if total_conversations < self.min_sample_size:
            recommendations.append(f"Collect more data - need {self.min_sample_size - total_conversations} more conversations for statistical significance")
            return recommendations

        if winner:
            recommendations.append(f"Deploy variant '{winner.variant_name}' to 100% of traffic")
            recommendations.append(f"Expected conversion rate improvement: {winner.conversion_rate - variants[0].conversion_rate:.2f}%")
        else:
            # Find best performer (even if not statistically significant)
            best_variant = max(variants, key=lambda v: v.conversion_rate)

            if best_variant.confidence_level >= 0.80:
                recommendations.append(f"Variant '{best_variant.variant_name}' shows promise ({best_variant.confidence_level:.0%} confidence) - continue testing")
            else:
                recommendations.append("No clear winner yet - continue testing or try new variants")

        return recommendations

    def end_test(
        self,
        db: Session,
        test_name: str,
        deploy_winner: bool = False
    ) -> Dict[str, Any]:
        """
        End an A/B test and optionally deploy winner

        Args:
            db: Database session
            test_name: Name of test
            deploy_winner: If True, set winner to 100% traffic

        Returns:
            Final test results
        """

        variants = db.query(ABTestVariant).filter(
            ABTestVariant.test_name == test_name
        ).all()

        if not variants:
            raise ValueError(f"Test '{test_name}' not found")

        winner = next((v for v in variants if v.is_winner), None)

        # Mark test as ended
        for variant in variants:
            variant.is_active = False
            variant.test_ended_at = datetime.utcnow()

        # Deploy winner if requested
        if deploy_winner and winner:
            winner.traffic_percentage = 100.0
            winner.is_active = True

            logger.info(f"Deployed winner variant '{winner.variant_name}' to 100% traffic")

        db.commit()

        # Get final results
        results = self.get_test_results(db, test_name)

        logger.info(f"Ended A/B test '{test_name}'")

        return results


# Singleton instance
ab_testing_service = ABTestingService()
