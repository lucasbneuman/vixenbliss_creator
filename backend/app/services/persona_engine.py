"""
Persona Engine Service
Manages avatar personality, generates embeddings for RAG, and maintains consistency
"""

import os
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.avatar import Avatar
from app.models.identity_component import IdentityComponent
from app.services.bio_generator import bio_generator_service, AvatarBiography


class PersonaEngineService:
    """Service for persona management and embedding generation"""

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = AsyncOpenAI(api_key=self.openai_key) if self.openai_key else None

    async def create_complete_persona(
        self,
        db: Session,
        avatar_id: UUID,
        niche: str,
        aesthetic_style: str,
        age: int,
        ethnicity: str,
        name_suggestion: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Create complete persona for avatar including biography, location, and embeddings

        Workflow:
        1. Generate biography with LLM
        2. Generate location and lifestyle context
        3. Create embeddings for personality traits
        4. Store in identity_components with pgvector
        5. Return complete persona data
        """

        # Step 1: Generate core biography
        biography = await bio_generator_service.generate_biography(
            niche=niche,
            aesthetic_style=aesthetic_style,
            age=age,
            ethnicity=ethnicity,
            name_suggestion=name_suggestion
        )

        # Step 2: Generate location and additional context
        location_data = await bio_generator_service.generate_location_and_interests(
            biography=biography,
            niche=niche
        )

        # Step 3: Build personality profile text for embedding
        personality_text = self._build_personality_text(biography, location_data)

        # Step 4: Generate embeddings using OpenAI
        embedding = await self._generate_embedding(personality_text)

        # Step 5: Store in database
        await self._store_persona(
            db=db,
            avatar_id=avatar_id,
            biography=biography,
            location_data=location_data,
            embedding=embedding
        )

        # Step 6: Update avatar name
        avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()
        if avatar:
            avatar.name = biography.name
            avatar.metadata = avatar.metadata or {}
            avatar.metadata["persona"] = {
                "biography": biography.model_dump(),
                "location": location_data
            }
            db.commit()

        return {
            "biography": biography.model_dump(),
            "location": location_data,
            "personality_embedding": embedding[:10],  # First 10 dimensions for preview
            "persona_text": personality_text
        }

    def _build_personality_text(
        self,
        biography: AvatarBiography,
        location_data: Dict
    ) -> str:
        """Build comprehensive personality text for embedding"""

        text = f"""Name: {biography.name}
Age: {biography.age}

Backstory: {biography.backstory}

Personality Traits: {', '.join(biography.personality_traits)}

Core Interests: {', '.join(biography.interests)}

Goals and Aspirations: {', '.join(biography.goals)}

Communication Style: {biography.communication_style}

Tone of Voice: {biography.tone_of_voice}

Audience Relationship: {biography.audience_relationship}

Location: {location_data.get('location', {}).get('city')}, {location_data.get('location', {}).get('state')}
Location Vibe: {location_data.get('location', {}).get('vibe')}

Lifestyle: {location_data.get('lifestyle_context', {}).get('typical_day')}

Favorite Spots: {', '.join(location_data.get('lifestyle_context', {}).get('favorite_spots', []))}

Cultural Background: {location_data.get('cultural_background')}

Additional Interests: {', '.join(location_data.get('additional_interests', []))}
"""

        if biography.catchphrase:
            text += f"\nCatchphrase: {biography.catchphrase}"

        return text

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI ada-002"""

        if not self.openai_client:
            # Return dummy embedding if OpenAI not configured
            return [0.0] * 1536

        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )

            embedding = response.data[0].embedding
            return embedding

        except Exception as e:
            print(f"Embedding generation failed: {str(e)}")
            return [0.0] * 1536

    async def _store_persona(
        self,
        db: Session,
        avatar_id: UUID,
        biography: AvatarBiography,
        location_data: Dict,
        embedding: List[float]
    ):
        """Store persona components in identity_components table"""

        # Biography component
        bio_component = IdentityComponent(
            avatar_id=avatar_id,
            component_type="biography",
            content=biography.model_dump(),
            metadata={
                "generated_by": "auto-bio-generator",
                "model": "claude-3.5-sonnet"
            }
        )
        db.add(bio_component)

        # Location component
        location_component = IdentityComponent(
            avatar_id=avatar_id,
            component_type="location_context",
            content=location_data,
            metadata={}
        )
        db.add(location_component)

        # Personality embedding component (for RAG)
        personality_text = self._build_personality_text(biography, location_data)

        embedding_component = IdentityComponent(
            avatar_id=avatar_id,
            component_type="personality_embedding",
            content={
                "personality_text": personality_text,
                "embedding_dimension": len(embedding)
            },
            embedding=embedding,  # Stores in pgvector column
            metadata={
                "model": "text-embedding-ada-002"
            }
        )
        db.add(embedding_component)

        db.commit()

    async def get_persona(
        self,
        db: Session,
        avatar_id: UUID
    ) -> Optional[Dict]:
        """Retrieve complete persona for avatar"""

        components = db.query(IdentityComponent).filter(
            IdentityComponent.avatar_id == avatar_id,
            IdentityComponent.component_type.in_([
                "biography",
                "location_context",
                "personality_embedding"
            ])
        ).all()

        persona_data = {}

        for comp in components:
            if comp.component_type == "biography":
                persona_data["biography"] = comp.content
            elif comp.component_type == "location_context":
                persona_data["location"] = comp.content
            elif comp.component_type == "personality_embedding":
                persona_data["personality_text"] = comp.content.get("personality_text")

        return persona_data if persona_data else None

    async def find_similar_personas(
        self,
        db: Session,
        avatar_id: UUID,
        limit: int = 5
    ) -> List[Dict]:
        """Find similar avatars using vector similarity search"""

        # Get this avatar's embedding
        embedding_comp = db.query(IdentityComponent).filter(
            IdentityComponent.avatar_id == avatar_id,
            IdentityComponent.component_type == "personality_embedding"
        ).first()

        if not embedding_comp or not embedding_comp.embedding:
            return []

        # TODO: Implement pgvector similarity search
        # For now, return empty list
        # In production, use: SELECT * FROM identity_components ORDER BY embedding <=> query_embedding LIMIT 5

        return []


# Singleton instance
persona_engine_service = PersonaEngineService()
