"""
Voice Synthesis Service
Multi-provider voice/TTS generation (E08-002)
"""

import logging
from typing import Dict, Any, Optional
import httpx
import os
import base64

logger = logging.getLogger(__name__)


class VoiceSynthesisService:
    """
    Multi-provider voice synthesis service

    Providers:
    - ElevenLabs: High quality, $0.30/1K characters
    - Play.ht: Good quality, $0.20/1K characters
    - Azure TTS: Basic quality, $0.016/1K characters
    """

    def __init__(self):
        # Provider configurations
        self.providers = {
            "elevenlabs": {
                "name": "ElevenLabs",
                "cost_per_1k_chars": 0.30,
                "quality": "high",
                "api_key_env": "ELEVENLABS_API_KEY",
                "base_url": "https://api.elevenlabs.io/v1"
            },
            "playht": {
                "name": "Play.ht",
                "cost_per_1k_chars": 0.20,
                "quality": "medium",
                "api_key_env": "PLAYHT_API_KEY",
                "user_id_env": "PLAYHT_USER_ID",
                "base_url": "https://api.play.ht/api/v2"
            },
            "azure": {
                "name": "Azure TTS",
                "cost_per_1k_chars": 0.016,
                "quality": "basic",
                "api_key_env": "AZURE_SPEECH_KEY",
                "region_env": "AZURE_SPEECH_REGION",
                "base_url": "https://{region}.tts.speech.microsoft.com"
            }
        }

        # Default provider routing
        self.default_provider = "playht"  # Balanced quality/cost

    async def generate_voice(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate voice audio from text

        Args:
            text: Text to synthesize
            voice_id: Voice ID (provider-specific)
            language: Language code (en, es, fr, etc.)
            provider: Specific provider to use (or auto-select)

        Returns:
            Voice generation result with audio data
        """

        logger.info(f"Generating voice: '{text[:50]}...' (language: {language})")

        # Select provider
        provider_name = provider or self.default_provider

        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        # Call provider-specific method
        if provider_name == "elevenlabs":
            return await self._generate_elevenlabs(text, voice_id, language)
        elif provider_name == "playht":
            return await self._generate_playht(text, voice_id, language)
        elif provider_name == "azure":
            return await self._generate_azure(text, voice_id, language)
        else:
            raise ValueError(f"Provider not implemented: {provider_name}")

    async def _generate_elevenlabs(
        self,
        text: str,
        voice_id: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """Generate voice using ElevenLabs"""

        api_key = os.getenv(self.providers["elevenlabs"]["api_key_env"])

        if not api_key:
            raise ValueError("ElevenLabs API key not found")

        base_url = self.providers["elevenlabs"]["base_url"]

        # Default voice if not specified
        if not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/text-to-speech/{voice_id}",
                json=payload,
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()

            audio_data = response.content

            # Calculate cost
            char_count = len(text)
            cost = (char_count / 1000) * self.providers["elevenlabs"]["cost_per_1k_chars"]

            # Encode audio as base64 for transport
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            return {
                "provider": "elevenlabs",
                "audio_data": audio_base64,
                "audio_format": "mp3",
                "char_count": char_count,
                "cost": cost,
                "voice_id": voice_id,
                "language": language
            }

    async def _generate_playht(
        self,
        text: str,
        voice_id: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """Generate voice using Play.ht"""

        api_key = os.getenv(self.providers["playht"]["api_key_env"])
        user_id = os.getenv(self.providers["playht"]["user_id_env"])

        if not api_key or not user_id:
            raise ValueError("Play.ht credentials not found")

        base_url = self.providers["playht"]["base_url"]

        # Default voice if not specified
        if not voice_id:
            voice_id = "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json"

        payload = {
            "text": text,
            "voice": voice_id,
            "output_format": "mp3",
            "voice_engine": "PlayHT2.0"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/tts",
                json=payload,
                headers={
                    "AUTHORIZATION": api_key,
                    "X-USER-ID": user_id,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()

            result_data = response.json()
            audio_url = result_data["url"]

            # Download audio
            audio_response = await client.get(audio_url)
            audio_response.raise_for_status()

            audio_data = audio_response.content

            # Calculate cost
            char_count = len(text)
            cost = (char_count / 1000) * self.providers["playht"]["cost_per_1k_chars"]

            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            return {
                "provider": "playht",
                "audio_data": audio_base64,
                "audio_format": "mp3",
                "char_count": char_count,
                "cost": cost,
                "voice_id": voice_id,
                "language": language
            }

    async def _generate_azure(
        self,
        text: str,
        voice_id: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """Generate voice using Azure TTS"""

        api_key = os.getenv(self.providers["azure"]["api_key_env"])
        region = os.getenv(self.providers["azure"]["region_env"], "eastus")

        if not api_key:
            raise ValueError("Azure Speech API key not found")

        base_url = self.providers["azure"]["base_url"].format(region=region)

        # Default voice if not specified
        if not voice_id:
            # Map language to default voice
            voice_map = {
                "en": "en-US-JennyNeural",
                "es": "es-ES-ElviraNeural",
                "fr": "fr-FR-DeniseNeural"
            }
            voice_id = voice_map.get(language, "en-US-JennyNeural")

        # Build SSML
        ssml = f"""
        <speak version='1.0' xml:lang='{language}'>
            <voice xml:lang='{language}' name='{voice_id}'>
                {text}
            </voice>
        </speak>
        """

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/cognitiveservices/v1",
                content=ssml,
                headers={
                    "Ocp-Apim-Subscription-Key": api_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
                }
            )
            response.raise_for_status()

            audio_data = response.content

            # Calculate cost
            char_count = len(text)
            cost = (char_count / 1000) * self.providers["azure"]["cost_per_1k_chars"]

            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            return {
                "provider": "azure",
                "audio_data": audio_base64,
                "audio_format": "mp3",
                "char_count": char_count,
                "cost": cost,
                "voice_id": voice_id,
                "language": language
            }

    def select_optimal_provider(
        self,
        budget: Optional[float] = None,
        priority: str = "balanced"
    ) -> str:
        """
        Select optimal provider based on criteria

        Args:
            budget: Budget per 1K characters
            priority: Selection priority (quality, cost, balanced)

        Returns:
            Recommended provider name
        """

        if priority == "quality":
            return "elevenlabs"
        elif priority == "cost":
            return "azure"
        elif priority == "balanced":
            return "playht"

        # Budget-based selection
        if budget:
            if budget >= 0.30:
                return "elevenlabs"
            elif budget >= 0.20:
                return "playht"
            else:
                return "azure"

        return "playht"  # Default to balanced


# Singleton instance
voice_synthesis_service = VoiceSynthesisService()
