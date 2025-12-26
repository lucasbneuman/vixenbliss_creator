"""
Auto-Bio Generator Service
Generates avatar biographies, personalities, and backstories using LLM
"""

import os
from typing import Dict, Optional
from pydantic import BaseModel
import anthropic
from openai import AsyncOpenAI


class AvatarBiography(BaseModel):
    """Generated biography components"""
    name: str
    age: int
    backstory: str  # 2-3 sentences
    personality_traits: list[str]  # 5-7 traits
    interests: list[str]  # 5-10 interests
    goals: list[str]  # 3-5 goals
    communication_style: str  # How they interact
    tone_of_voice: str  # Friendly, confident, playful, etc.
    audience_relationship: str  # How they relate to followers
    catchphrase: Optional[str] = None


class BioGeneratorService:
    """Service for generating avatar biographies using LLM"""

    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.use_anthropic = bool(self.anthropic_key)

    async def generate_biography(
        self,
        niche: str,
        aesthetic_style: str,
        age: int,
        ethnicity: str,
        name_suggestion: Optional[str] = None
    ) -> AvatarBiography:
        """
        Generate complete biography for avatar

        Uses Claude 3.5 Sonnet (preferred) or GPT-4
        """

        prompt = self._build_bio_prompt(
            niche=niche,
            aesthetic_style=aesthetic_style,
            age=age,
            ethnicity=ethnicity,
            name_suggestion=name_suggestion
        )

        if self.use_anthropic:
            bio_data = await self._generate_with_anthropic(prompt)
        else:
            bio_data = await self._generate_with_openai(prompt)

        return AvatarBiography(**bio_data)

    def _build_bio_prompt(
        self,
        niche: str,
        aesthetic_style: str,
        age: int,
        ethnicity: str,
        name_suggestion: Optional[str]
    ) -> str:
        """Build LLM prompt for biography generation"""

        prompt = f"""You are an expert at creating compelling, authentic social media personalities.

Create a detailed biography for an AI avatar with these characteristics:
- Niche: {niche}
- Aesthetic Style: {aesthetic_style}
- Age: {age}
- Background: {ethnicity}
{f"- Name (suggestion): {name_suggestion}" if name_suggestion else ""}

Generate the following components in JSON format:

{{
  "name": "A catchy, memorable name that fits the niche",
  "age": {age},
  "backstory": "2-3 sentences describing their background, how they got into {niche}, and what drives them",
  "personality_traits": ["5-7 distinctive personality traits"],
  "interests": ["5-10 specific interests related to {niche} and beyond"],
  "goals": ["3-5 aspirational goals they're working towards"],
  "communication_style": "How they communicate with their audience (e.g., 'encouraging and supportive', 'direct and no-nonsense')",
  "tone_of_voice": "Their vocal/written tone (e.g., 'warm and friendly', 'bold and confident')",
  "audience_relationship": "How they position themselves relative to their audience (e.g., 'big sister figure', 'knowledgeable mentor')",
  "catchphrase": "Optional: a signature phrase they might use"
}}

IMPORTANT:
- Make it AUTHENTIC and relatable
- Avoid clichés and generic descriptions
- The personality should feel REAL, not robotic
- Tailor everything specifically to the {niche} niche
- Make interests specific and concrete (not just "fitness" but "morning trail runs, powerlifting, meal prep")
- Communication style should match the niche audience

Return ONLY the JSON object, no other text."""

        return prompt

    async def _generate_with_anthropic(self, prompt: str) -> Dict:
        """Generate biography using Claude 3.5 Sonnet"""

        client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)

        try:
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.9,  # Higher creativity for personalities
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Parse JSON response
            import json
            bio_data = json.loads(response_text)

            return bio_data

        except Exception as e:
            raise Exception(f"Anthropic biography generation failed: {str(e)}")

    async def _generate_with_openai(self, prompt: str) -> Dict:
        """Generate biography using GPT-4"""

        client = AsyncOpenAI(api_key=self.openai_key)

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at creating authentic social media personalities. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content

            # Parse JSON response
            import json
            bio_data = json.loads(response_text)

            return bio_data

        except Exception as e:
            raise Exception(f"OpenAI biography generation failed: {str(e)}")

    async def generate_location_and_interests(
        self,
        biography: AvatarBiography,
        niche: str
    ) -> Dict[str, any]:
        """
        Generate realistic location and additional interests

        This creates geographic and contextual details for the avatar
        """

        prompt = f"""Based on this avatar's profile:

Name: {biography.name}
Niche: {niche}
Personality: {', '.join(biography.personality_traits[:3])}
Current Interests: {', '.join(biography.interests[:5])}

Generate realistic location and contextual details in JSON format:

{{
  "location": {{
    "city": "A realistic city that fits their lifestyle",
    "state": "State/Province",
    "country": "Country",
    "vibe": "Description of their location (e.g., 'sunny coastal city', 'bustling urban metropolis')"
  }},
  "lifestyle_context": {{
    "typical_day": "Brief description of a typical day",
    "favorite_spots": ["3-5 types of places they frequent"],
    "community": "How they engage with their local community"
  }},
  "additional_interests": ["3-5 interests that add depth beyond the niche"],
  "cultural_background": "Brief cultural context that influences their content"
}}

Make it REALISTIC and consistent with their personality and niche."""

        if self.use_anthropic:
            client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
        else:
            client = AsyncOpenAI(api_key=self.openai_key)
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content

        import json
        return json.loads(response_text)


# Singleton instance
bio_generator_service = BioGeneratorService()
