"""
Template Library - 50 Professional Content Templates
Pre-designed poses, angles, and prompts for content generation
"""

from typing import List, Dict, Any, Optional
from enum import Enum


class TemplateCategory(str, Enum):
    FITNESS = "fitness"
    LIFESTYLE = "lifestyle"
    GLAMOUR = "glamour"
    ARTISTIC = "artistic"
    WELLNESS = "wellness"
    BEACH = "beach"
    URBAN = "urban"
    NATURE = "nature"
    FASHION = "fashion"
    INTIMATE = "intimate"


class TemplateTier(str, Enum):
    CAPA1 = "capa1"  # Safe for social media
    CAPA2 = "capa2"  # Suggestive, premium content
    CAPA3 = "capa3"  # Explicit, high-tier subscribers


# 50 Professional Templates
CONTENT_TEMPLATES: List[Dict[str, Any]] = [
    # FITNESS (10 templates)
    {
        "id": "FIT-001",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "athletic woman in fitted sportswear, gym environment",
        "pose_description": "mid-workout pose, lifting dumbbells, focused expression",
        "lighting": "bright gym lighting, high contrast",
        "angle": "medium shot, slightly from below",
        "tags": ["gym", "strength", "fitness", "workout"]
    },
    {
        "id": "FIT-002",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in yoga pose, yoga studio setting",
        "pose_description": "warrior pose, balanced stance, serene expression",
        "lighting": "soft natural window light, peaceful ambiance",
        "angle": "full body shot, side angle",
        "tags": ["yoga", "flexibility", "wellness", "balance"]
    },
    {
        "id": "FIT-003",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "runner in athletic wear, outdoor park setting",
        "pose_description": "dynamic running pose, mid-stride, energetic",
        "lighting": "golden hour lighting, warm tones",
        "angle": "action shot, panning motion blur background",
        "tags": ["running", "cardio", "outdoor", "active"]
    },
    {
        "id": "FIT-004",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "fit woman in sports bra and leggings, home gym",
        "pose_description": "post-workout selfie pose, mirror reflection",
        "lighting": "natural home lighting, authentic feel",
        "angle": "selfie angle, upper body focus",
        "tags": ["fitness", "progress", "selfie", "mirror"]
    },
    {
        "id": "FIT-005",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman doing stretching exercises, outdoor setting",
        "pose_description": "hamstring stretch, flexible pose, calm",
        "lighting": "morning light, fresh atmosphere",
        "angle": "ground level shot, dynamic perspective",
        "tags": ["stretching", "flexibility", "outdoor", "morning"]
    },
    {
        "id": "FIT-006",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "crossfit athlete, gym box environment",
        "pose_description": "box jump preparation, powerful stance",
        "lighting": "dramatic gym lighting, shadows",
        "angle": "low angle, emphasizing strength",
        "tags": ["crossfit", "power", "athletic", "intense"]
    },
    {
        "id": "FIT-007",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in fitted workout set, posing with kettlebell",
        "pose_description": "confident pose with equipment, strong posture",
        "lighting": "studio lighting, clean background",
        "angle": "three-quarter view, flattering angle",
        "tags": ["strength", "equipment", "studio", "confidence"]
    },
    {
        "id": "FIT-008",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "pilates practitioner on reformer machine",
        "pose_description": "controlled pilates movement, focused",
        "lighting": "soft studio lighting, professional",
        "angle": "side view, showing form",
        "tags": ["pilates", "control", "studio", "reformer"]
    },
    {
        "id": "FIT-009",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman doing plank exercise, minimal background",
        "pose_description": "perfect plank form, core engaged, determined",
        "lighting": "clean lighting, focus on subject",
        "angle": "straight-on profile view",
        "tags": ["core", "plank", "form", "determination"]
    },
    {
        "id": "FIT-010",
        "category": TemplateCategory.FITNESS,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "athletic woman post-workout, towel around neck",
        "pose_description": "relaxed post-exercise pose, natural smile",
        "lighting": "natural gym lighting, authentic",
        "angle": "portrait shot, upper body",
        "tags": ["post-workout", "authentic", "relaxed", "smile"]
    },

    # LIFESTYLE (10 templates)
    {
        "id": "LIFE-001",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman enjoying morning coffee, cozy home setting",
        "pose_description": "relaxed seated pose, holding coffee mug, content",
        "lighting": "soft morning window light, warm tones",
        "angle": "medium shot, natural perspective",
        "tags": ["coffee", "morning", "cozy", "home"]
    },
    {
        "id": "LIFE-002",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman reading book in comfortable chair",
        "pose_description": "natural reading pose, engaged with book",
        "lighting": "ambient home lighting, peaceful",
        "angle": "side angle, showing environment",
        "tags": ["reading", "relaxation", "intellectual", "peaceful"]
    },
    {
        "id": "LIFE-003",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman cooking in modern kitchen",
        "pose_description": "engaged in meal preparation, natural motion",
        "lighting": "bright kitchen lighting, clean feel",
        "angle": "over-the-shoulder perspective",
        "tags": ["cooking", "kitchen", "domestic", "healthy"]
    },
    {
        "id": "LIFE-004",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman working on laptop, home office",
        "pose_description": "focused work pose, professional yet casual",
        "lighting": "natural desk lighting, productivity vibe",
        "angle": "slight overhead angle",
        "tags": ["work", "productivity", "home-office", "professional"]
    },
    {
        "id": "LIFE-005",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman tending to indoor plants",
        "pose_description": "caring for plants, gentle movements",
        "lighting": "natural window light, green ambiance",
        "angle": "medium shot, showing plants",
        "tags": ["plants", "nature", "care", "home"]
    },
    {
        "id": "LIFE-006",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in pajamas, morning routine",
        "pose_description": "natural morning pose, relaxed demeanor",
        "lighting": "soft bedroom lighting, intimate feel",
        "angle": "natural perspective, casual",
        "tags": ["morning", "routine", "pajamas", "casual"]
    },
    {
        "id": "LIFE-007",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman doing skincare routine, bathroom mirror",
        "pose_description": "applying skincare product, self-care moment",
        "lighting": "bright bathroom lighting, mirror reflection",
        "angle": "mirror selfie perspective",
        "tags": ["skincare", "self-care", "routine", "beauty"]
    },
    {
        "id": "LIFE-008",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman enjoying healthy smoothie bowl",
        "pose_description": "holding colorful smoothie bowl, genuine smile",
        "lighting": "bright natural light, fresh feel",
        "angle": "overhead flat lay + subject",
        "tags": ["healthy", "food", "nutrition", "wellness"]
    },
    {
        "id": "LIFE-009",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman meditating in serene home space",
        "pose_description": "cross-legged meditation pose, peaceful",
        "lighting": "soft diffused light, calm atmosphere",
        "angle": "frontal medium shot",
        "tags": ["meditation", "mindfulness", "peace", "wellness"]
    },
    {
        "id": "LIFE-010",
        "category": TemplateCategory.LIFESTYLE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman organizing closet, fashion focus",
        "pose_description": "selecting outfit, natural shopping pose",
        "lighting": "bright closet lighting, organized",
        "angle": "medium shot, showing wardrobe",
        "tags": ["fashion", "organization", "wardrobe", "style"]
    },

    # GLAMOUR (10 templates)
    {
        "id": "GLAM-001",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "glamorous woman in elegant evening dress",
        "pose_description": "sophisticated pose, hand on hip, confident",
        "lighting": "dramatic studio lighting, high contrast",
        "angle": "full body shot, flattering angle",
        "tags": ["elegant", "evening", "glamour", "sophisticated"]
    },
    {
        "id": "GLAM-002",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in luxurious silk robe, boudoir setting",
        "pose_description": "sensual seated pose, elegant posture",
        "lighting": "soft boudoir lighting, intimate",
        "angle": "medium shot, slightly from above",
        "tags": ["boudoir", "silk", "luxurious", "sensual"]
    },
    {
        "id": "GLAM-003",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman with professional makeup, beauty portrait",
        "pose_description": "classic beauty pose, perfect lighting on face",
        "lighting": "professional beauty lighting, flawless",
        "angle": "close-up portrait, face focus",
        "tags": ["beauty", "makeup", "portrait", "professional"]
    },
    {
        "id": "GLAM-004",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in designer lingerie, bedroom setting",
        "pose_description": "confident pose on bed, alluring expression",
        "lighting": "warm bedroom lighting, romantic",
        "angle": "three-quarter view, tasteful",
        "tags": ["lingerie", "bedroom", "confident", "designer"]
    },
    {
        "id": "GLAM-005",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in luxury hotel room, sophisticated setting",
        "pose_description": "relaxed pose by window, elegant demeanor",
        "lighting": "natural hotel lighting, upscale",
        "angle": "environmental portrait",
        "tags": ["luxury", "hotel", "travel", "sophisticated"]
    },
    {
        "id": "GLAM-006",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA3,
        "prompt_template": "artistic nude study, tasteful composition",
        "pose_description": "artistic pose, body as art, sophisticated",
        "lighting": "dramatic artistic lighting, shadows",
        "angle": "artistic angle, partial coverage",
        "tags": ["artistic", "nude", "sophisticated", "art"]
    },
    {
        "id": "GLAM-007",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in bathtub with rose petals, luxury spa",
        "pose_description": "relaxed bath pose, serene expression",
        "lighting": "soft candlelight, romantic ambiance",
        "angle": "overhead angle, artistic composition",
        "tags": ["spa", "luxury", "relaxation", "romantic"]
    },
    {
        "id": "GLAM-008",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in high fashion outfit, studio setting",
        "pose_description": "editorial fashion pose, strong presence",
        "lighting": "professional fashion lighting",
        "angle": "full body fashion shot",
        "tags": ["fashion", "editorial", "high-end", "studio"]
    },
    {
        "id": "GLAM-009",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman applying lipstick, vanity mirror close-up",
        "pose_description": "beauty routine moment, focused on lips",
        "lighting": "vanity mirror lighting, glamorous",
        "angle": "extreme close-up, mirror reflection",
        "tags": ["beauty", "makeup", "vanity", "close-up"]
    },
    {
        "id": "GLAM-010",
        "category": TemplateCategory.GLAMOUR,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in flowing gown, wind machine effect",
        "pose_description": "dynamic pose with fabric movement",
        "lighting": "dramatic studio lighting, cinematic",
        "angle": "full body, capturing motion",
        "tags": ["gown", "motion", "cinematic", "dramatic"]
    },

    # BEACH (8 templates)
    {
        "id": "BCH-001",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in bikini on tropical beach",
        "pose_description": "confident beach pose, natural smile",
        "lighting": "bright tropical sunlight, blue sky",
        "angle": "full body shot, ocean background",
        "tags": ["beach", "bikini", "tropical", "ocean"]
    },
    {
        "id": "BCH-002",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in sundress walking on beach",
        "pose_description": "walking pose, wind in hair, carefree",
        "lighting": "golden hour beach lighting",
        "angle": "medium shot, beach landscape",
        "tags": ["beach", "sundress", "walking", "golden-hour"]
    },
    {
        "id": "BCH-003",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in one-piece swimsuit, beach yoga",
        "pose_description": "yoga pose on beach, centered",
        "lighting": "morning beach light, serene",
        "angle": "side view, ocean horizon",
        "tags": ["beach", "yoga", "swimsuit", "wellness"]
    },
    {
        "id": "BCH-004",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in beach cover-up, sunset background",
        "pose_description": "relaxed standing pose, serene expression",
        "lighting": "sunset golden light, warm tones",
        "angle": "medium shot, sunset silhouette",
        "tags": ["beach", "sunset", "cover-up", "golden"]
    },
    {
        "id": "BCH-005",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in bikini lying on beach towel",
        "pose_description": "sunbathing pose, relaxed and natural",
        "lighting": "bright midday sun, beach atmosphere",
        "angle": "overhead shot, beach setting",
        "tags": ["beach", "sunbathing", "bikini", "relaxed"]
    },
    {
        "id": "BCH-006",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman emerging from ocean waves",
        "pose_description": "dynamic water pose, hair wet, confident",
        "lighting": "bright tropical light, water sparkles",
        "angle": "medium shot, water level",
        "tags": ["ocean", "waves", "dynamic", "water"]
    },
    {
        "id": "BCH-007",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman with surfboard on beach",
        "pose_description": "athletic pose with board, sporty",
        "lighting": "bright beach daylight",
        "angle": "full body, showing surfboard",
        "tags": ["surf", "athletic", "beach", "sporty"]
    },
    {
        "id": "BCH-008",
        "category": TemplateCategory.BEACH,
        "tier": TemplateTier.CAPA2,
        "prompt_template": "woman in beach hammock, tropical paradise",
        "pose_description": "relaxed hammock pose, peaceful",
        "lighting": "dappled shade lighting, tropical",
        "angle": "medium shot, paradise vibes",
        "tags": ["hammock", "tropical", "relaxation", "paradise"]
    },

    # URBAN (6 templates)
    {
        "id": "URB-001",
        "category": TemplateCategory.URBAN,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in street style outfit, city background",
        "pose_description": "confident street pose, modern fashion",
        "lighting": "urban daylight, city atmosphere",
        "angle": "full body, street photography style",
        "tags": ["street-style", "urban", "fashion", "city"]
    },
    {
        "id": "URB-002",
        "category": TemplateCategory.URBAN,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in coffee shop, urban lifestyle",
        "pose_description": "casual coffee shop pose, authentic",
        "lighting": "natural cafe lighting, cozy",
        "angle": "medium shot, environment visible",
        "tags": ["cafe", "coffee", "urban", "lifestyle"]
    },
    {
        "id": "URB-003",
        "category": TemplateCategory.URBAN,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman on city rooftop, skyline background",
        "pose_description": "confident pose, city views behind",
        "lighting": "golden hour city lighting",
        "angle": "three-quarter shot, skyline visible",
        "tags": ["rooftop", "skyline", "city", "golden-hour"]
    },
    {
        "id": "URB-004",
        "category": TemplateCategory.URBAN,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman walking through city street",
        "pose_description": "dynamic walking pose, motion",
        "lighting": "urban street lighting, authentic",
        "angle": "street level, capturing movement",
        "tags": ["walking", "street", "urban", "motion"]
    },
    {
        "id": "URB-005",
        "category": TemplateCategory.URBAN,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in urban park, city nature blend",
        "pose_description": "relaxed park pose, peaceful",
        "lighting": "dappled park lighting",
        "angle": "medium shot, natural setting",
        "tags": ["park", "urban-nature", "relaxed", "city"]
    },
    {
        "id": "URB-006",
        "category": TemplateCategory.URBAN,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman with shopping bags, urban shopping",
        "pose_description": "happy shopping pose, energetic",
        "lighting": "bright urban daylight",
        "angle": "full body, shopping district",
        "tags": ["shopping", "urban", "fashion", "lifestyle"]
    },

    # NATURE (6 templates)
    {
        "id": "NAT-001",
        "category": TemplateCategory.NATURE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in forest, natural environment",
        "pose_description": "standing among trees, peaceful",
        "lighting": "filtered forest sunlight, green tones",
        "angle": "medium shot, trees framing",
        "tags": ["forest", "nature", "trees", "peaceful"]
    },
    {
        "id": "NAT-002",
        "category": TemplateCategory.NATURE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in flower field, spring meadow",
        "pose_description": "natural pose among flowers, joyful",
        "lighting": "soft natural sunlight, vibrant colors",
        "angle": "full body, flower field visible",
        "tags": ["flowers", "meadow", "spring", "nature"]
    },
    {
        "id": "NAT-003",
        "category": TemplateCategory.NATURE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman by mountain lake, scenic view",
        "pose_description": "contemplative pose, nature appreciation",
        "lighting": "mountain daylight, clear sky",
        "angle": "medium shot, landscape background",
        "tags": ["mountain", "lake", "scenic", "contemplative"]
    },
    {
        "id": "NAT-004",
        "category": TemplateCategory.NATURE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in autumn forest, fall colors",
        "pose_description": "walking through leaves, seasonal",
        "lighting": "warm autumn sunlight, golden tones",
        "angle": "environmental portrait, leaves visible",
        "tags": ["autumn", "fall", "forest", "seasonal"]
    },
    {
        "id": "NAT-005",
        "category": TemplateCategory.NATURE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman at waterfall, adventurous setting",
        "pose_description": "adventurous pose, nature explorer",
        "lighting": "natural outdoor light, misty",
        "angle": "medium shot, waterfall background",
        "tags": ["waterfall", "adventure", "nature", "explorer"]
    },
    {
        "id": "NAT-006",
        "category": TemplateCategory.NATURE,
        "tier": TemplateTier.CAPA1,
        "prompt_template": "woman in meadow at sunset, pastoral",
        "pose_description": "peaceful standing pose, arms relaxed",
        "lighting": "golden sunset light, magical",
        "angle": "full body silhouette, sunset glow",
        "tags": ["meadow", "sunset", "pastoral", "peaceful"]
    },
]


class TemplateLibrary:
    """Service for managing and retrieving content templates"""

    def __init__(self):
        self.templates = CONTENT_TEMPLATES

    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all 50 templates"""
        return self.templates

    def get_by_category(self, category: TemplateCategory) -> List[Dict[str, Any]]:
        """Get templates by category"""
        return [t for t in self.templates if t["category"] == category]

    def get_by_tier(self, tier: TemplateTier) -> List[Dict[str, Any]]:
        """Get templates by access tier"""
        return [t for t in self.templates if t["tier"] == tier]

    def get_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get specific template by ID"""
        for template in self.templates:
            if template["id"] == template_id:
                return template
        return None

    def get_random_templates(
        self,
        count: int = 50,
        category: Optional[TemplateCategory] = None,
        tier: Optional[TemplateTier] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random selection of templates

        Args:
            count: Number of templates to return
            category: Optional category filter
            tier: Optional tier filter

        Returns:
            Random selection of templates
        """
        import random

        filtered = self.templates

        if category:
            filtered = [t for t in filtered if t["category"] == category]

        if tier:
            filtered = [t for t in filtered if t["tier"] == tier]

        if len(filtered) <= count:
            return filtered

        return random.sample(filtered, count)

    def get_templates_for_avatar(
        self,
        avatar_niche: str,
        count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get templates optimized for avatar's niche

        Args:
            avatar_niche: Avatar's primary niche
            count: Number of templates to return

        Returns:
            Niche-optimized template selection
        """

        # Niche to category mapping
        niche_mapping = {
            "fitness": [TemplateCategory.FITNESS, TemplateCategory.WELLNESS, TemplateCategory.LIFESTYLE],
            "wellness": [TemplateCategory.WELLNESS, TemplateCategory.LIFESTYLE, TemplateCategory.NATURE],
            "glamour": [TemplateCategory.GLAMOUR, TemplateCategory.FASHION, TemplateCategory.INTIMATE],
            "lifestyle": [TemplateCategory.LIFESTYLE, TemplateCategory.URBAN, TemplateCategory.NATURE],
            "beach": [TemplateCategory.BEACH, TemplateCategory.NATURE, TemplateCategory.LIFESTYLE],
            "fashion": [TemplateCategory.FASHION, TemplateCategory.GLAMOUR, TemplateCategory.URBAN],
            "artistic": [TemplateCategory.ARTISTIC, TemplateCategory.GLAMOUR, TemplateCategory.NATURE]
        }

        preferred_categories = niche_mapping.get(avatar_niche.lower(), [
            TemplateCategory.LIFESTYLE,
            TemplateCategory.FASHION,
            TemplateCategory.GLAMOUR
        ])

        # Gather templates from preferred categories
        templates = []
        for category in preferred_categories:
            templates.extend(self.get_by_category(category))

        # If not enough, add from other categories
        if len(templates) < count:
            remaining = [t for t in self.templates if t not in templates]
            templates.extend(remaining)

        # Return requested count
        return templates[:count]

    def get_tier_distribution(
        self,
        count: int = 50,
        capa1_ratio: float = 0.6,
        capa2_ratio: float = 0.3,
        capa3_ratio: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Get templates with specific tier distribution

        Args:
            count: Total templates to return
            capa1_ratio: Ratio of Capa 1 (safe) content
            capa2_ratio: Ratio of Capa 2 (suggestive) content
            capa3_ratio: Ratio of Capa 3 (explicit) content

        Returns:
            Templates distributed by tier
        """
        import random

        capa1_count = int(count * capa1_ratio)
        capa2_count = int(count * capa2_ratio)
        capa3_count = int(count * capa3_ratio)

        capa1_templates = self.get_by_tier(TemplateTier.CAPA1)
        capa2_templates = self.get_by_tier(TemplateTier.CAPA2)
        capa3_templates = self.get_by_tier(TemplateTier.CAPA3)

        selected = []

        # Add from each tier
        selected.extend(random.sample(capa1_templates, min(capa1_count, len(capa1_templates))))
        selected.extend(random.sample(capa2_templates, min(capa2_count, len(capa2_templates))))
        selected.extend(random.sample(capa3_templates, min(capa3_count, len(capa3_templates))))

        # Fill remaining with capa1
        while len(selected) < count:
            remaining = [t for t in capa1_templates if t not in selected]
            if not remaining:
                break
            selected.append(random.choice(remaining))

        return selected[:count]


# Singleton instance
template_library = TemplateLibrary()
