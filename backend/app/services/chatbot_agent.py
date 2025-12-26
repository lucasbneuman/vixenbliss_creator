"""
Chatbot Agent Service
LangGraph agent for automated DM conversations (E06-001)
"""

import logging
from typing import Dict, Any, Optional, List, Annotated, TypedDict
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID
import json

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.models.conversation import Conversation, Message, FunnelStage, SenderType
from app.models.avatar import Avatar

logger = logging.getLogger(__name__)


class ConversationState(TypedDict):
    """State for conversation agent"""
    messages: List[Dict[str, str]]
    conversation_id: str
    avatar_id: str
    funnel_stage: str
    lead_score: int
    user_message: str
    bot_response: str
    intent: Optional[str]
    sentiment: Optional[float]
    should_advance_funnel: bool
    should_upsell: bool
    metadata: Dict[str, Any]


class ChatbotAgent:
    """
    LangGraph agent for automated DM conversations
    Implements 3-stage funnel: Lead Magnet → Qualification → Conversion
    """

    def __init__(self):
        # Initialize LLM providers
        self.llm_claude = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.7
        )

        self.llm_openai = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )

        # Default to Claude
        self.llm = self.llm_claude

        # Build conversation graph
        self.graph = self._build_conversation_graph()

    def _build_conversation_graph(self) -> StateGraph:
        """Build LangGraph workflow for conversation handling"""

        workflow = StateGraph(ConversationState)

        # Add nodes
        workflow.add_node("analyze_message", self._analyze_message)
        workflow.add_node("lead_magnet_stage", self._lead_magnet_response)
        workflow.add_node("qualification_stage", self._qualification_response)
        workflow.add_node("conversion_stage", self._conversion_response)
        workflow.add_node("generate_response", self._generate_response)

        # Define edges
        workflow.set_entry_point("analyze_message")

        workflow.add_conditional_edges(
            "analyze_message",
            self._route_by_funnel_stage,
            {
                "lead_magnet": "lead_magnet_stage",
                "qualification": "qualification_stage",
                "conversion": "conversion_stage"
            }
        )

        workflow.add_edge("lead_magnet_stage", "generate_response")
        workflow.add_edge("qualification_stage", "generate_response")
        workflow.add_edge("conversion_stage", "generate_response")
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    def _analyze_message(self, state: ConversationState) -> ConversationState:
        """Analyze user message for intent and sentiment"""

        user_message = state["user_message"]

        # Use LLM to analyze message
        analysis_prompt = f"""Analyze this message from a potential customer:

Message: "{user_message}"

Provide:
1. Intent (one of: greeting, question, purchase_intent, objection, casual_chat, explicit_content_request)
2. Sentiment score (-1.0 to 1.0, where -1 is very negative, 0 is neutral, 1 is very positive)

Respond in JSON format:
{{"intent": "...", "sentiment": 0.0}}
"""

        try:
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            analysis = json.loads(response.content)

            state["intent"] = analysis.get("intent", "casual_chat")
            state["sentiment"] = float(analysis.get("sentiment", 0.5))

            logger.info(f"Message analysis: intent={state['intent']}, sentiment={state['sentiment']}")

        except Exception as e:
            logger.error(f"Failed to analyze message: {str(e)}")
            state["intent"] = "casual_chat"
            state["sentiment"] = 0.5

        return state

    def _route_by_funnel_stage(self, state: ConversationState) -> str:
        """Route to appropriate funnel stage handler"""
        funnel_stage = state.get("funnel_stage", "lead_magnet")

        if funnel_stage == FunnelStage.LEAD_MAGNET.value:
            return "lead_magnet"
        elif funnel_stage == FunnelStage.QUALIFICATION.value:
            return "qualification"
        else:
            return "conversion"

    def _lead_magnet_response(self, state: ConversationState) -> ConversationState:
        """
        Stage 1: Lead Magnet
        Goal: Hook the lead, provide value, build rapport
        """

        intent = state.get("intent", "casual_chat")

        # Determine if we should advance to qualification
        advance_triggers = ["purchase_intent", "question"]
        state["should_advance_funnel"] = intent in advance_triggers and state["lead_score"] >= 30

        state["metadata"]["stage_strategy"] = "lead_magnet"
        state["metadata"]["response_type"] = "value_proposition"

        return state

    def _qualification_response(self, state: ConversationState) -> ConversationState:
        """
        Stage 2: Qualification
        Goal: Ask questions, validate interest, build desire
        """

        intent = state.get("intent", "casual_chat")

        # Determine if we should advance to conversion
        advance_triggers = ["purchase_intent", "explicit_content_request"]
        state["should_advance_funnel"] = intent in advance_triggers and state["lead_score"] >= 60

        # Check if we should present upsell
        state["should_upsell"] = state["lead_score"] >= 70

        state["metadata"]["stage_strategy"] = "qualification"
        state["metadata"]["response_type"] = "engagement_questions"

        return state

    def _conversion_stage(self, state: ConversationState) -> ConversationState:
        """
        Stage 3: Conversion
        Goal: Present offer, handle objections, close sale
        """

        intent = state.get("intent", "casual_chat")
        lead_score = state.get("lead_score", 0)

        # Always ready to upsell in conversion stage
        state["should_upsell"] = True

        # E07-002: Determine which offer tier to present based on lead score
        if lead_score >= 80:
            # Hot lead - present premium pack (Capa 2)
            state["metadata"]["offer_tier"] = "capa2"
            state["metadata"]["offer_type"] = "premium_pack"
            state["metadata"]["recommended_pack"] = "deluxe_pack"
        elif lead_score >= 60:
            # Warm lead - present premium pack starter
            state["metadata"]["offer_tier"] = "capa2"
            state["metadata"]["offer_type"] = "premium_pack"
            state["metadata"]["recommended_pack"] = "starter_pack"
        else:
            # Default - present basic subscription (Capa 1)
            state["metadata"]["offer_tier"] = "capa1"
            state["metadata"]["offer_type"] = "subscription"

        state["metadata"]["stage_strategy"] = "conversion"
        state["metadata"]["response_type"] = "pricing_offer"

        return state

    def _generate_response(self, state: ConversationState) -> ConversationState:
        """Generate final response using LLM with avatar personality context"""

        # Build conversation history
        messages = state.get("messages", [])
        history_context = "\n".join([
            f"{'User' if msg['sender'] == 'user' else 'You'}: {msg['content']}"
            for msg in messages[-10:]  # Last 10 messages for context
        ])

        # Get avatar personality (this would come from database in production)
        avatar_context = state.get("metadata", {}).get("avatar_personality", {})
        personality_traits = avatar_context.get("personality_traits", "Flirty, playful, confident")
        tone = avatar_context.get("tone", "casual and engaging")

        # Build prompt based on funnel stage
        funnel_stage = state.get("funnel_stage", "lead_magnet")
        user_message = state["user_message"]
        intent = state.get("intent", "casual_chat")

        if funnel_stage == FunnelStage.LEAD_MAGNET.value:
            system_prompt = f"""You are roleplaying as a content creator with this personality: {personality_traits}

Your tone is: {tone}

Current goal: Hook the lead and build rapport. Provide value and intrigue.

Conversation so far:
{history_context}

User's latest message: "{user_message}"
Detected intent: {intent}

Respond naturally as yourself. Keep it short (1-2 sentences). Be engaging and flirty but not pushy."""

        elif funnel_stage == FunnelStage.QUALIFICATION.value:
            system_prompt = f"""You are roleplaying as a content creator with this personality: {personality_traits}

Your tone is: {tone}

Current goal: Qualify the lead's interest. Ask engaging questions to understand their preferences.

Conversation so far:
{history_context}

User's latest message: "{user_message}"
Detected intent: {intent}

Respond naturally. Ask 1 specific question about their interests or preferences. Keep it flirty and personal."""

        else:  # Conversion stage
            # E07-002: Get recommended offer based on lead score
            offer_tier = state.get("metadata", {}).get("offer_tier", "capa1")
            offer_type = state.get("metadata", {}).get("offer_type", "subscription")
            recommended_pack = state.get("metadata", {}).get("recommended_pack")

            # Build offer description
            if offer_tier == "capa2" and recommended_pack:
                # Premium pack offer
                pack_prices = {
                    "starter_pack": "$29.99 - 10 exclusive photos",
                    "deluxe_pack": "$59.99 - 25 premium photos",
                    "ultimate_pack": "$99.99 - 50 exclusive photos",
                    "vip_pack": "$149.99 - 100 premium photos + bonus"
                }
                offer_description = pack_prices.get(recommended_pack, "$59.99 - 25 premium photos")
                upsell_offers = [f"Premium Photo Pack: {offer_description}"]
            else:
                # Basic subscription offer
                upsell_offers = [
                    "Basic subscription ($9.99/month) - Access to my exclusive content"
                ]

            system_prompt = f"""You are roleplaying as a content creator with this personality: {personality_traits}

Your tone is: {tone}

Current goal: Present an offer and close the sale.

Conversation so far:
{history_context}

User's latest message: "{user_message}"
Detected intent: {intent}

RECOMMENDED OFFER (present this naturally):
{upsell_offers[0]}

Respond naturally. Present the offer in a sexy and enticing way without being pushy. Make them want it."""

        try:
            response = self.llm.invoke([SystemMessage(content=system_prompt)])
            bot_response = response.content

            state["bot_response"] = bot_response
            logger.info(f"Generated response for {funnel_stage}: {bot_response[:100]}...")

        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            # Fallback response
            state["bot_response"] = "Hey! 😊 Tell me more about what you're looking for..."

        return state

    async def process_message(
        self,
        db: Session,
        conversation: Conversation,
        user_message_text: str,
        platform_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process incoming user message and generate bot response

        Args:
            db: Database session
            conversation: Conversation object
            user_message_text: User's message text
            platform_message_id: Platform's message ID

        Returns:
            Bot response with metadata
        """

        logger.info(f"Processing message for conversation {conversation.id}")

        # Get avatar for personality context
        avatar = db.query(Avatar).filter(Avatar.id == conversation.avatar_id).first()

        avatar_personality = {
            "personality_traits": avatar.metadata.get("personality_traits", "Flirty, playful, confident"),
            "tone": avatar.metadata.get("tone", "casual and engaging"),
            "interests": avatar.metadata.get("interests", []),
            "bio": avatar.metadata.get("bio", "")
        }

        # Get conversation history
        recent_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(10).all()

        history = [
            {
                "sender": "user" if msg.sender_type == SenderType.USER else "bot",
                "content": msg.message_text
            }
            for msg in reversed(recent_messages)
        ]

        # Build initial state
        initial_state: ConversationState = {
            "messages": history,
            "conversation_id": str(conversation.id),
            "avatar_id": str(conversation.avatar_id),
            "funnel_stage": conversation.funnel_stage.value,
            "lead_score": conversation.lead_score,
            "user_message": user_message_text,
            "bot_response": "",
            "intent": None,
            "sentiment": None,
            "should_advance_funnel": False,
            "should_upsell": False,
            "metadata": {
                "avatar_personality": avatar_personality,
                "available_offers": []  # Would be populated from database
            }
        }

        # Run LangGraph workflow
        final_state = self.graph.invoke(initial_state)

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            sender_type=SenderType.USER,
            platform_message_id=platform_message_id,
            message_text=user_message_text,
            sentiment_score=final_state.get("sentiment"),
            intent_detected=final_state.get("intent")
        )
        db.add(user_message)

        # Save bot response
        bot_message = Message(
            conversation_id=conversation.id,
            sender_type=SenderType.BOT,
            message_text=final_state["bot_response"],
            bot_confidence_score=0.85,
            metadata=final_state.get("metadata", {})
        )
        db.add(bot_message)

        # Update conversation metrics
        conversation.message_count += 2
        conversation.user_message_count += 1
        conversation.bot_message_count += 1
        conversation.last_message_at = datetime.utcnow()

        # Update sentiment
        if final_state.get("sentiment"):
            if conversation.avg_sentiment_score == 0.5:
                conversation.avg_sentiment_score = final_state["sentiment"]
            else:
                conversation.avg_sentiment_score = (conversation.avg_sentiment_score * 0.8) + (final_state["sentiment"] * 0.2)

        # Update lead score based on engagement
        score_delta = self._calculate_score_delta(final_state)
        new_score = conversation.lead_score + score_delta
        conversation.update_lead_score(new_score)

        # Advance funnel if triggered
        if final_state.get("should_advance_funnel"):
            conversation.advance_funnel_stage()
            logger.info(f"Advanced conversation {conversation.id} to {conversation.funnel_stage.value}")

        db.commit()

        return {
            "bot_response": final_state["bot_response"],
            "intent": final_state.get("intent"),
            "sentiment": final_state.get("sentiment"),
            "lead_score": conversation.lead_score,
            "funnel_stage": conversation.funnel_stage.value,
            "should_upsell": final_state.get("should_upsell", False),
            "metadata": final_state.get("metadata", {})
        }

    def _calculate_score_delta(self, state: ConversationState) -> int:
        """Calculate lead score change based on message analysis"""

        delta = 0

        # Positive intent boosts score
        intent = state.get("intent", "casual_chat")
        intent_scores = {
            "purchase_intent": +15,
            "explicit_content_request": +20,
            "question": +5,
            "greeting": +2,
            "casual_chat": +1,
            "objection": -5
        }
        delta += intent_scores.get(intent, 0)

        # Positive sentiment boosts score
        sentiment = state.get("sentiment", 0.5)
        if sentiment > 0.7:
            delta += 5
        elif sentiment < 0.3:
            delta -= 5

        return delta


# Singleton instance
chatbot_agent = ChatbotAgent()
