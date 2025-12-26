"""
Prompt Presets Service
Manages customized prompts and style presets for avatar generation
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class PromptPreset(BaseModel):
    """Prompt preset configuration"""
    name: str
    category: str  # fitness, lifestyle, artistic, glamorous, etc.
    base_prompt: str
    negative_prompt: str
    style_keywords: List[str]
    lighting_suggestions: List[str]
    pose_suggestions: List[str]
    recommended_params: Dict[str, any]


# Built-in presets
PRESET_LIBRARY: Dict[str, PromptPreset] = {
    "fitness_athletic": PromptPreset(
        name="Fitness Athletic",
        category="fitness",
        base_prompt=(
            "Professional fitness photoshoot, athletic physique, "
            "confident and powerful pose, gym setting or outdoor athletic environment, "
            "sporty activewear, toned muscles, energetic vibe"
        ),
        negative_prompt=(
            "overweight, out of shape, lazy pose, poor lighting, "
            "amateur photo, low quality, distorted anatomy"
        ),
        style_keywords=["athletic", "fit", "energetic", "powerful", "sporty"],
        lighting_suggestions=["high contrast gym lighting", "natural outdoor light", "dramatic shadows"],
        pose_suggestions=["power pose", "mid-workout action", "flexing", "running stance"],
        recommended_params={
            "cfg_scale": 7.5,
            "steps": 30,
            "aesthetic_score": 8.0
        }
    ),

    "lifestyle_casual": PromptPreset(
        name="Lifestyle Casual",
        category="lifestyle",
        base_prompt=(
            "Lifestyle photography, casual everyday setting, natural and approachable, "
            "coffee shop, urban street, or cozy home interior, "
            "relaxed comfortable clothing, genuine smile, relatable vibe"
        ),
        negative_prompt=(
            "overly formal, stiff pose, studio backdrop, artificial, "
            "excessive editing, unrealistic"
        ),
        style_keywords=["casual", "relatable", "authentic", "everyday", "approachable"],
        lighting_suggestions=["soft natural window light", "golden hour", "cafe ambient lighting"],
        pose_suggestions=["candid moment", "laughing naturally", "casual sitting", "walking"],
        recommended_params={
            "cfg_scale": 6.5,
            "steps": 28,
            "aesthetic_score": 7.0
        }
    ),

    "glamorous_fashion": PromptPreset(
        name="Glamorous Fashion",
        category="glamorous",
        base_prompt=(
            "High fashion editorial photoshoot, glamorous and sophisticated, "
            "luxury fashion styling, elegant designer clothing, "
            "professional makeup and hair, editorial pose, vogue magazine style"
        ),
        negative_prompt=(
            "cheap clothing, poor styling, amateur, casual, "
            "bad makeup, messy hair, low fashion"
        ),
        style_keywords=["glamorous", "sophisticated", "luxury", "editorial", "haute couture"],
        lighting_suggestions=["studio beauty lighting", "rim lighting", "high key glamour"],
        pose_suggestions=["editorial pose", "high fashion stance", "elegant turn"],
        recommended_params={
            "cfg_scale": 8.0,
            "steps": 35,
            "aesthetic_score": 9.0
        }
    ),

    "artistic_creative": PromptPreset(
        name="Artistic Creative",
        category="artistic",
        base_prompt=(
            "Artistic creative portrait, unique perspective, artistic expression, "
            "creative lighting and composition, experimental style, "
            "artistic wardrobe, unconventional setting, gallery-worthy"
        ),
        negative_prompt=(
            "conventional, boring, standard portrait, typical, "
            "generic, unoriginal"
        ),
        style_keywords=["artistic", "creative", "unique", "experimental", "expressive"],
        lighting_suggestions=["creative lighting", "colored gels", "dramatic shadows", "silhouette"],
        pose_suggestions=["expressive gesture", "dynamic movement", "contemplative"],
        recommended_params={
            "cfg_scale": 7.0,
            "steps": 32,
            "aesthetic_score": 8.5
        }
    ),

    "wellness_yoga": PromptPreset(
        name="Wellness Yoga",
        category="fitness",
        base_prompt=(
            "Wellness and yoga photography, serene and balanced, "
            "yoga pose or meditation, natural peaceful setting, "
            "comfortable yoga attire, mindful expression, zen atmosphere"
        ),
        negative_prompt=(
            "tense, stressed, chaotic background, poor form, "
            "inappropriate clothing"
        ),
        style_keywords=["serene", "balanced", "mindful", "peaceful", "zen"],
        lighting_suggestions=["soft diffused light", "sunrise/sunset", "natural outdoor"],
        pose_suggestions=["yoga pose", "meditation", "stretching", "balanced stance"],
        recommended_params={
            "cfg_scale": 6.8,
            "steps": 30,
            "aesthetic_score": 7.5
        }
    ),

    "beach_vacation": PromptPreset(
        name="Beach Vacation",
        category="lifestyle",
        base_prompt=(
            "Beach vacation photography, tropical paradise setting, "
            "swimwear or summer clothing, sun-kissed glow, "
            "ocean or beach background, carefree vacation vibe"
        ),
        negative_prompt=(
            "winter clothing, indoor setting, pale skin, "
            "cold atmosphere, urban background"
        ),
        style_keywords=["tropical", "sunny", "vacation", "carefree", "summer"],
        lighting_suggestions=["bright sunny day", "golden hour beach", "natural sunlight"],
        pose_suggestions=["beach walking", "playful in water", "relaxed on sand"],
        recommended_params={
            "cfg_scale": 7.0,
            "steps": 28,
            "aesthetic_score": 8.0
        }
    )
}


class PromptPresetsService:
    """Service for managing prompt presets"""

    def get_preset(self, preset_name: str) -> Optional[PromptPreset]:
        """Get preset by name"""
        return PRESET_LIBRARY.get(preset_name)

    def list_presets(self, category: Optional[str] = None) -> List[PromptPreset]:
        """List all presets, optionally filtered by category"""
        presets = list(PRESET_LIBRARY.values())

        if category:
            presets = [p for p in presets if p.category == category]

        return presets

    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(set(p.category for p in PRESET_LIBRARY.values()))

    def build_prompt_from_preset(
        self,
        preset_name: str,
        custom_additions: Optional[str] = None,
        age_range: str = "26-35",
        ethnicity: str = "diverse"
    ) -> tuple[str, str]:
        """Build complete prompt from preset with customizations"""

        preset = self.get_preset(preset_name)
        if not preset:
            raise ValueError(f"Preset '{preset_name}' not found")

        # Age descriptors
        age_descriptors = {
            "18-25": "youthful, fresh-faced",
            "26-35": "mature, confident",
            "36-45": "refined, sophisticated",
            "46+": "elegant, distinguished"
        }

        # Build full prompt
        full_prompt = (
            f"{preset.base_prompt}, "
            f"{age_descriptors.get(age_range, 'mature')}, "
            f"{ethnicity} features, "
            f"professional photography, 8k resolution, sharp focus"
        )

        if custom_additions:
            full_prompt += f", {custom_additions}"

        # Add style keywords
        full_prompt += f", {', '.join(preset.style_keywords)}"

        return full_prompt, preset.negative_prompt

    def create_custom_preset(
        self,
        name: str,
        category: str,
        base_prompt: str,
        negative_prompt: str,
        **kwargs
    ) -> PromptPreset:
        """Create a custom preset (for user-defined presets)"""

        preset = PromptPreset(
            name=name,
            category=category,
            base_prompt=base_prompt,
            negative_prompt=negative_prompt,
            style_keywords=kwargs.get("style_keywords", []),
            lighting_suggestions=kwargs.get("lighting_suggestions", []),
            pose_suggestions=kwargs.get("pose_suggestions", []),
            recommended_params=kwargs.get("recommended_params", {})
        )

        # Note: In production, save to database
        # For now, just return the preset

        return preset


# Singleton instance
prompt_presets_service = PromptPresetsService()
