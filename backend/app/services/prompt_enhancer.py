"""
Prompt Enhancer
Uses GPT-4o mini to improve prompts before sending to generation engine.
"""

import os
import json
from typing import List, Dict, Any
from openai import AsyncOpenAI


class PromptEnhancer:
    def __init__(self) -> None:
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("PROMPT_ENHANCER_MODEL", "gpt-4o-mini")
        self.client = AsyncOpenAI(api_key=self.openai_key) if self.openai_key else None

    async def enhance_prompt(
        self,
        base_prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Enhance a single prompt with context.
        If OpenAI is not configured, returns base prompt.
        """

        if not self.client:
            return base_prompt

        system = (
            "You are a prompt engineer for photorealistic content generation. "
            "Rewrite the prompt to be more descriptive, consistent, and optimized "
            "for realistic results while preserving the original intent. "
            "Avoid mentioning watermark, text, or low quality. "
            "Return ONLY the improved prompt text."
        )

        user_payload = {
            "base_prompt": base_prompt,
            "context": context
        }

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
            ],
            temperature=0.4,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    async def enhance_prompts(
        self,
        prompts: List[str],
        context_items: List[Dict[str, Any]]
    ) -> List[str]:
        """Enhance a list of prompts with per-item context."""

        enhanced = []
        for prompt, context in zip(prompts, context_items):
            enhanced_prompt = await self.enhance_prompt(prompt, context)
            enhanced.append(enhanced_prompt)
        return enhanced


prompt_enhancer = PromptEnhancer()
