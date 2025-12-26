"""
Hook Generator - Automatic Social Media Hook Creation
Uses Claude 3.5 Sonnet or GPT-4 to generate engaging hooks
"""

import os
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic
import openai
from enum import Enum


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    ONLYFANS = "onlyfans"


class HookStyle(str, Enum):
    QUESTION = "question"
    CHALLENGE = "challenge"
    STORY = "story"
    TIP = "tip"
    TEASER = "teaser"
    RELATABLE = "relatable"


class HookGenerator:
    """Service for generating engaging social media hooks"""

    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.use_claude = bool(self.anthropic_key)

        if self.use_claude:
            self.client = AsyncAnthropic(api_key=self.anthropic_key)
        else:
            openai.api_key = self.openai_key

    async def generate_hooks(
        self,
        avatar_personality: Dict[str, Any],
        content_type: str,
        platform: Platform,
        template_info: Optional[Dict[str, Any]] = None,
        num_variations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate engaging hooks for content

        Args:
            avatar_personality: Avatar's personality traits
            content_type: Type of content (fitness, lifestyle, etc.)
            platform: Target social media platform
            template_info: Optional template metadata
            num_variations: Number of hook variations to generate

        Returns:
            List of hook variations with metadata
        """

        # Build context from avatar personality
        personality_context = self._build_personality_context(avatar_personality)

        # Build prompt for LLM
        prompt = self._build_hook_prompt(
            personality_context=personality_context,
            content_type=content_type,
            platform=platform,
            template_info=template_info,
            num_variations=num_variations
        )

        # Generate hooks using Claude or GPT-4
        if self.use_claude:
            hooks_text = await self._generate_with_claude(prompt)
        else:
            hooks_text = await self._generate_with_gpt4(prompt)

        # Parse and structure hooks
        hooks = self._parse_hooks(hooks_text, num_variations)

        return hooks

    def _build_personality_context(self, personality: Dict[str, Any]) -> str:
        """Build personality context string"""

        traits = personality.get("personality_traits", [])
        interests = personality.get("interests", [])
        goals = personality.get("goals", [])
        tone = personality.get("tone_of_voice", "friendly and authentic")

        context = f"""
Avatar Personality:
- Personality Traits: {', '.join(traits) if traits else 'confident, authentic, engaging'}
- Interests: {', '.join(interests) if interests else 'fitness, wellness, lifestyle'}
- Goals: {', '.join(goals) if goals else 'inspire others, build community'}
- Tone of Voice: {tone}
"""
        return context.strip()

    def _build_hook_prompt(
        self,
        personality_context: str,
        content_type: str,
        platform: Platform,
        template_info: Optional[Dict[str, Any]],
        num_variations: int
    ) -> str:
        """Build prompt for LLM hook generation"""

        platform_specs = {
            Platform.INSTAGRAM: {
                "max_length": 150,
                "style": "aspirational, visual storytelling, authentic",
                "emojis": "use sparingly, 1-2 max"
            },
            Platform.TIKTOK: {
                "max_length": 100,
                "style": "bold, attention-grabbing, trend-aware",
                "emojis": "use generously, 3-5"
            },
            Platform.TWITTER: {
                "max_length": 280,
                "style": "punchy, conversational, witty",
                "emojis": "use minimally, 0-1"
            },
            Platform.ONLYFANS: {
                "max_length": 200,
                "style": "personal, exclusive, teasing",
                "emojis": "use strategically, 2-3"
            }
        }

        specs = platform_specs.get(platform, platform_specs[Platform.INSTAGRAM])

        template_context = ""
        if template_info:
            template_context = f"""
Content Template Context:
- Category: {template_info.get('category', 'lifestyle')}
- Pose: {template_info.get('pose_description', 'natural pose')}
- Setting: {template_info.get('lighting', 'natural lighting')}
- Tags: {', '.join(template_info.get('tags', []))}
"""

        prompt = f"""You are an expert social media copywriter specializing in {platform.value} content.

{personality_context}

{template_context}

Content Type: {content_type}

Platform Requirements for {platform.value}:
- Maximum Length: {specs['max_length']} characters
- Style: {specs['style']}
- Emoji Usage: {specs['emojis']}

Generate {num_variations} engaging hook variations for this content post.

Each hook should:
1. Match the avatar's personality and tone
2. Be platform-appropriate
3. Drive engagement (comments, saves, shares)
4. Create curiosity or connection
5. Use different hook styles (question, challenge, story, tip, teaser, relatable)

Format your response as a numbered list (1-{num_variations}), with each hook on its own line.
Include a brief style tag in parentheses at the end of each hook.

Example format:
1. [Hook text here] (style: question)
2. [Hook text here] (style: teaser)

Generate the hooks now:"""

        return prompt

    async def _generate_with_claude(self, prompt: str) -> str:
        """Generate hooks using Claude 3.5 Sonnet"""

        try:
            message = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.8,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return message.content[0].text

        except Exception as e:
            raise Exception(f"Claude hook generation failed: {str(e)}")

    async def _generate_with_gpt4(self, prompt: str) -> str:
        """Generate hooks using GPT-4"""

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media copywriter."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=1024
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"GPT-4 hook generation failed: {str(e)}")

    def _parse_hooks(self, hooks_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse LLM output into structured hooks"""

        import re

        hooks = []
        lines = hooks_text.strip().split('\n')

        for line in lines:
            # Match numbered hooks: "1. Hook text (style: question)"
            match = re.match(r'^\d+\.\s*(.+?)\s*\(style:\s*(\w+)\)\s*$', line.strip())

            if match:
                hook_text = match.group(1).strip()
                style = match.group(2).strip()

                hooks.append({
                    "text": hook_text,
                    "style": style,
                    "length": len(hook_text),
                    "emoji_count": self._count_emojis(hook_text)
                })

        # If parsing failed, try simpler format
        if len(hooks) < expected_count:
            hooks = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove number prefix if exists
                    cleaned = re.sub(r'^\d+\.\s*', '', line)
                    if cleaned:
                        hooks.append({
                            "text": cleaned,
                            "style": "general",
                            "length": len(cleaned),
                            "emoji_count": self._count_emojis(cleaned)
                        })

        return hooks[:expected_count]

    def _count_emojis(self, text: str) -> int:
        """Count emojis in text (approximate)"""
        import emoji
        try:
            return emoji.emoji_count(text)
        except:
            # Fallback: count common emoji patterns
            return len(re.findall(r'[\U0001F300-\U0001F9FF]', text))

    async def generate_hook_variations(
        self,
        base_hook: str,
        num_variations: int = 3
    ) -> List[str]:
        """
        Generate variations of an existing hook

        Args:
            base_hook: Original hook text
            num_variations: Number of variations to generate

        Returns:
            List of hook variations
        """

        prompt = f"""Generate {num_variations} variations of this social media hook.

Original hook:
"{base_hook}"

Create variations that:
1. Keep the core message
2. Use different wording/structure
3. Maintain similar length
4. Are equally engaging

Format as numbered list (1-{num_variations}):"""

        if self.use_claude:
            variations_text = await self._generate_with_claude(prompt)
        else:
            variations_text = await self._generate_with_gpt4(prompt)

        # Parse variations
        import re
        variations = []
        for line in variations_text.split('\n'):
            match = re.match(r'^\d+\.\s*(.+)$', line.strip())
            if match:
                variations.append(match.group(1).strip())

        return variations[:num_variations]

    async def generate_cta(
        self,
        content_type: str,
        platform: Platform,
        goal: str = "engagement"
    ) -> str:
        """
        Generate call-to-action for content

        Args:
            content_type: Type of content
            platform: Target platform
            goal: CTA goal (engagement, conversion, growth)

        Returns:
            CTA text
        """

        prompt = f"""Generate a compelling call-to-action (CTA) for a {content_type} post on {platform.value}.

Goal: {goal}

The CTA should:
1. Be concise (1-2 sentences)
2. Be platform-appropriate
3. Drive the desired action
4. Feel natural, not salesy

Provide only the CTA text, no explanation:"""

        if self.use_claude:
            cta = await self._generate_with_claude(prompt)
        else:
            cta = await self._generate_with_gpt4(prompt)

        return cta.strip().strip('"').strip("'")

    def estimate_hook_cost(self, num_hooks: int) -> float:
        """
        Estimate cost for hook generation

        Args:
            num_hooks: Number of hooks to generate

        Returns:
            Estimated cost in USD
        """

        # Claude 3.5 Sonnet: ~$0.003 per generation
        # GPT-4: ~$0.005 per generation
        cost_per_generation = 0.003 if self.use_claude else 0.005

        # Each generation produces 5 hooks
        num_generations = (num_hooks + 4) // 5

        return num_generations * cost_per_generation


# Singleton instance
hook_generator = HookGenerator()
