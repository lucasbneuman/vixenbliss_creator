"""
Test content generation with mocked external services.
✅ Reproduces original errors: missing lora_weights_url, avatar not found
✅ Tests successful creation with mocks
✅ Validates API contract for /api/v1/content/* endpoints
"""

import base64
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.avatar import Avatar
from app.models.user import User
from app.models.content_piece import ContentPiece
from app.schemas.content import (
    ContentGenerationRequest,
    BatchGenerationRequest,
    HookGenerationRequest,
    SafetyCheckRequest,
    ContentPieceResponse,
    BatchGenerationResponse
)


@pytest.fixture
def client(override_get_db):
    """TestClient with DB override"""
    return TestClient(app)


@pytest.fixture
def user(test_db_session):
    """Create test user with unique email"""
    import uuid as uuid_module
    unique_id = str(uuid_module.uuid4())[:8]
    user = User(
        id=UUID(int=1),
        email=f"test-{unique_id}@example.com",
        password_hash="hashed_password_here",
        name="Test User"
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def avatar_without_lora(test_db_session, user):
    """Avatar without trained LoRA weights (blocker)"""
    avatar = Avatar(
        id=UUID(int=2),
        user_id=user.id,
        name="Test Avatar",
        niche="fitness",
        aesthetic_style="natural",
        lora_weights_url=None,  # ❌ BLOCKER: No LoRA trained yet
        stage="draft"
    )
    test_db_session.add(avatar)
    test_db_session.commit()
    test_db_session.refresh(avatar)
    return avatar


@pytest.fixture
def avatar_with_lora(test_db_session, user):
    """Avatar with trained LoRA weights (ready for content generation)"""
    avatar = Avatar(
        id=UUID(int=3),
        user_id=user.id,
        name="Trained Avatar",
        niche="fitness",
        aesthetic_style="natural",
        lora_weights_url="https://r2.example.com/lora/avatar-3.safetensors",  # ✅ Ready
        stage="active",
        meta_data={
            "personality": "energetic, motivational",
            "bio": "Fitness coach",
            "generation_config": {
                "steps": 28,
                "cfg_scale": 3.5
            }
        }
    )
    test_db_session.add(avatar)
    test_db_session.commit()
    test_db_session.refresh(avatar)
    return avatar


@pytest.fixture
def valid_content_generation_payload(avatar_with_lora):
    """Valid content generation request"""
    return {
        "avatar_id": str(avatar_with_lora.id),
        "custom_prompt": "athletic woman in gym, detailed, professional lighting",
        "platform": "instagram",
        "tier": "capa1"
    }


@pytest.fixture
def valid_batch_generation_payload(avatar_with_lora):
    """Valid batch generation request"""
    return {
        "avatar_id": str(avatar_with_lora.id),
        "num_pieces": 10,
        "platform": "instagram",
        "include_hooks": True,
        "safety_check": True,
        "upload_to_storage": False
    }


@pytest.fixture
def dummy_image_base64():
    """Minimal valid PNG as base64"""
    # Minimal PNG: 8x8 pixel image
    minimal_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x08\x00\x00\x00\x08'
        b'\x08\x02\x00\x00\x00k\xb4\x9bb\x00\x00\x00\x19tEXtSoftware\x00Adobe'
        b' ImageReadyq\xc9e<\x00\x00\x00"IDATx\xdab\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return base64.b64encode(minimal_png).decode()


# ============================================================================
# ERROR CASE TESTS
# ============================================================================

class TestContentGenerationErrors:
    """Test error cases and proper error handling"""

    @pytest.mark.unit
    def test_generate_content_avatar_not_found(self, client):
        """
        ❌ ERROR CASE 1: Avatar does not exist
        Expected: HTTP 404 "Avatar not found"
        """
        payload = {
            "avatar_id": str(uuid4()),
            "custom_prompt": "test prompt",
            "platform": "instagram"
        }
        response = client.post("/api/v1/content/generate", json=payload)
        assert response.status_code == 404
        assert "Avatar not found" in response.json()["detail"]

    @pytest.mark.unit
    def test_generate_content_missing_lora_weights(self, client, avatar_without_lora):
        """
        ❌ ERROR CASE 2: Avatar has no trained LoRA weights
        Expected: HTTP 400 "Avatar has no trained LoRA weights"
        
        Context: This is a BLOCKER from System 1.
        Content generation REQUIRES avatar to have lora_weights_url set.
        """
        payload = {
            "avatar_id": str(avatar_without_lora.id),
            "custom_prompt": "test prompt",
            "platform": "instagram"
        }
        response = client.post("/api/v1/content/generate", json=payload)
        assert response.status_code == 400
        assert "no trained LoRA weights" in response.json()["detail"]

    @pytest.mark.unit
    def test_generate_content_missing_prompt_and_template(self, client, avatar_with_lora):
        """
        ❌ ERROR CASE 3: Neither template_id nor custom_prompt provided
        Expected: HTTP 400 "Either template_id or custom_prompt required"
        """
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            # No template_id or custom_prompt
            "platform": "instagram"
        }
        response = client.post("/api/v1/content/generate", json=payload)
        assert response.status_code == 400

    @pytest.mark.unit
    def test_batch_generation_missing_avatar(self, client):
        """
        ❌ ERROR CASE 4: Avatar not found for batch generation
        Expected: HTTP 404 "Avatar not found"
        """
        payload = {
            "avatar_id": str(uuid4()),
            "num_pieces": 10,
            "platform": "instagram"
        }
        response = client.post("/api/v1/content/batch/sync", json=payload)
        assert response.status_code == 404

    @pytest.mark.unit
    def test_batch_generation_missing_lora(self, client, avatar_without_lora):
        """
        ❌ ERROR CASE 5: Avatar without LoRA for batch generation
        Expected: HTTP 400 "Avatar has no trained LoRA weights"
        """
        payload = {
            "avatar_id": str(avatar_without_lora.id),
            "num_pieces": 10,
            "platform": "instagram"
        }
        response = client.post("/api/v1/content/batch/sync", json=payload)
        assert response.status_code == 400

    @pytest.mark.unit
    def test_batch_generation_invalid_num_pieces(self, client, avatar_with_lora):
        """
        ❌ ERROR CASE 6: num_pieces outside allowed range (1-100)
        Expected: HTTP 422 Validation error
        """
        # Test too many pieces
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            "num_pieces": 200,
            "platform": "instagram"
        }
        response = client.post("/api/v1/content/batch/sync", json=payload)
        assert response.status_code == 422

        # Test zero pieces
        payload["num_pieces"] = 0
        response = client.post("/api/v1/content/batch/sync", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    def test_batch_generation_invalid_platform(self, client, avatar_with_lora):
        """
        ❌ ERROR CASE 7: Invalid platform specified
        Expected: HTTP 422 Validation error (or handled gracefully)
        """
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            "num_pieces": 10,
            "platform": "invalid_platform"
        }
        response = client.post("/api/v1/content/batch/sync", json=payload)
        # Depending on platform validation - 422 or 400
        assert response.status_code in [400, 422]

    @pytest.mark.unit
    def test_templates_invalid_avatar(self, client):
        """
        ❌ ERROR CASE 8: Get templates for non-existent avatar
        Expected: HTTP 404 "Avatar not found"
        """
        response = client.get(
            "/api/v1/content/templates",
            params={"avatar_id": str(uuid4())}
        )
        assert response.status_code == 404

    @pytest.mark.unit
    def test_get_template_not_found(self, client):
        """
        ❌ ERROR CASE 9: Get specific template that doesn't exist
        Expected: HTTP 404
        """
        response = client.get("/api/v1/content/templates/INVALID-ID")
        assert response.status_code == 404

    @pytest.mark.unit
    def test_safety_check_missing_image_url(self, client):
        """
        ❌ ERROR CASE 10: Safety check without image_url
        Expected: HTTP 422 Validation error
        """
        payload = {
            # Missing: image_url (required)
            "prompt": "test"
        }
        response = client.post("/api/v1/content/safety-check", json=payload)
        assert response.status_code == 422


# ============================================================================
# SUCCESS CASE TESTS (WITH MOCKS)
# ============================================================================

class TestContentGenerationSuccess:
    """Test successful operations with mocked external services"""

    @pytest.mark.unit
    async def test_generate_content_success_with_mocks(
        self,
        client,
        avatar_with_lora,
        dummy_image_base64
    ):
        """
        ✅ SUCCESS CASE 1: Generate single content piece with mocked LoRA inference
        
        Mocks:
        - lora_inference_engine.generate_image_with_lora() → returns image_url + metadata
        
        Expected:
        - HTTP 200
        - Response matches ContentPieceResponse schema
        - DB: ContentPiece created with correct relationships
        """
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            "custom_prompt": "athletic woman in gym",
            "platform": "instagram",
            "tier": "capa1"
        }

        # Mock the LoRA inference engine
        with patch(
            "app.services.lora_inference.lora_inference_engine.generate_image_with_lora"
        ) as mock_lora:
            mock_lora.return_value = {
                "image_base64": dummy_image_base64,
                "generation_time": 8.5,
                "parameters": {
                    "prompt": "TOK_avatar3, athletic woman in gym",
                    "steps": 28,
                    "cfg": 3.5
                },
                "cost": 0.01
            }

            response = client.post("/api/v1/content/generate", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Validate response schema
        assert "id" in data
        assert "avatar_id" in data
        assert "content_type" in data
        assert "access_tier" in data
        assert "url" in data
        assert data["avatar_id"] == str(avatar_with_lora.id)
        assert data["content_type"] == "image"
        assert data["access_tier"] == "capa1"
        assert "data:image/png;base64," in data["url"]

    @pytest.mark.unit
    async def test_generate_content_with_template_mock(
        self,
        client,
        avatar_with_lora,
        dummy_image_base64
    ):
        """
        ✅ SUCCESS CASE 2: Generate with template (vs custom prompt)
        
        Expected:
        - HTTP 200
        - Template prompt is used
        - Resulting image saved to DB
        """
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            "template_id": "FIT-001",  # Fitness template
            "platform": "instagram"
        }

        with patch(
            "app.services.lora_inference.lora_inference_engine.generate_with_template"
        ) as mock_gen:
            mock_gen.return_value = {
                "image_base64": dummy_image_base64,
                "generation_time": 9.0,
                "parameters": {
                    "prompt": "TOK_avatar3, athletic woman in fitted sportswear",
                    "steps": 28,
                    "cfg": 3.5
                },
                "cost": 0.01
            }

            response = client.post("/api/v1/content/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["avatar_id"] == str(avatar_with_lora.id)

    @pytest.mark.unit
    def test_get_templates_success(self, client, avatar_with_lora):
        """
        ✅ SUCCESS CASE 3: Get templates for avatar
        
        Expected:
        - HTTP 200
        - Response matches TemplateListResponse schema
        - Contains: templates[], total, categories[]
        """
        response = client.get(
            "/api/v1/content/templates",
            params={"avatar_id": str(avatar_with_lora.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert "categories" in data
        assert isinstance(data["templates"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["categories"], list)

    @pytest.mark.unit
    def test_get_templates_no_params(self, client):
        """
        ✅ SUCCESS CASE 4: Get all templates
        
        Expected:
        - HTTP 200
        - All templates returned (in-memory library)
        """
        response = client.get("/api/v1/content/templates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["templates"]) > 0

    @pytest.mark.unit
    def test_get_specific_template(self, client):
        """
        ✅ SUCCESS CASE 5: Get specific template by ID
        
        Expected:
        - HTTP 200
        - Template dict with expected fields
        """
        # First get all templates to find a valid ID
        response = client.get("/api/v1/content/templates")
        templates = response.json()["templates"]

        if templates:
            template_id = templates[0]["id"]
            response = client.get(f"/api/v1/content/templates/{template_id}")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "category" in data
            assert "tier" in data

    @pytest.mark.unit
    def test_get_content_for_avatar(self, client, avatar_with_lora, test_db_session):
        """
        ✅ SUCCESS CASE 6: Get content pieces for avatar
        
        Setup: Create sample content pieces in DB
        
        Expected:
        - HTTP 200
        - List of ContentPieceResponse objects
        - Filtered by avatar_id
        """
        # Create sample content pieces
        piece1 = ContentPiece(
            id=UUID(int=10),
            avatar_id=avatar_with_lora.id,
            content_type="image",
            access_tier="capa1",
            url="https://r2.example.com/content/avatar-3/piece-10.jpg",
            hook_text="Amazing fitness content!",
            safety_rating="safe"
        )
        piece2 = ContentPiece(
            id=UUID(int=11),
            avatar_id=avatar_with_lora.id,
            content_type="image",
            access_tier="capa1",
            url="https://r2.example.com/content/avatar-3/piece-11.jpg",
            hook_text="Transform your body!",
            safety_rating="safe"
        )
        test_db_session.add_all([piece1, piece2])
        test_db_session.commit()

        response = client.get(
            f"/api/v1/content/avatar/{avatar_with_lora.id}/content",
            params={"limit": 50, "offset": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all(piece["avatar_id"] == str(avatar_with_lora.id) for piece in data)

    @pytest.mark.unit
    def test_get_avatar_content_stats(self, client, avatar_with_lora, test_db_session):
        """
        ✅ SUCCESS CASE 7: Get content statistics for avatar
        
        Setup: Create content pieces with different tiers/safety ratings
        
        Expected:
        - HTTP 200
        - Response contains: avatar_id, total_content, tier_distribution, safety_distribution
        """
        # Create diverse content pieces
        for i in range(5):
            piece = ContentPiece(
                id=UUID(int=100 + i),
                avatar_id=avatar_with_lora.id,
                content_type="image",
                access_tier="capa1" if i < 3 else "capa2",
                url=f"https://r2.example.com/content/piece-{i}.jpg",
                safety_rating="safe" if i < 4 else "suggestive"
            )
            test_db_session.add(piece)
        test_db_session.commit()

        response = client.get(
            f"/api/v1/content/stats/{avatar_with_lora.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["avatar_id"] == str(avatar_with_lora.id)
        assert "total_content" in data
        assert data["total_content"] == 5
        assert "tier_distribution" in data
        assert "safety_distribution" in data

    @pytest.mark.unit
    def test_safety_check_mock(self, client):
        """
        ✅ SUCCESS CASE 8: Safety check with mocked OpenAI Moderation
        
        Mocks:
        - openai.Moderation.create() → returns moderation scores
        
        Expected:
        - HTTP 200
        - Response matches SafetyCheckResponse schema
        - Contains: rating, access_tier, scores, flagged_categories, safe
        """
        payload = {
            "image_url": "https://r2.example.com/content/test.jpg",
            "prompt": "athletic woman in gym"
        }

        with patch("app.services.content_safety.content_safety_service.check_image_safety") as mock_check:
            mock_check.return_value = {
                "rating": "safe",
                "access_tier": "capa1",
                "scores": {
                    "sexual": 0.1,
                    "violence": 0.0,
                    "hate": 0.0,
                    "self_harm": 0.0
                },
                "flagged_categories": [],
                "safe": True
            }

            response = client.post("/api/v1/content/safety-check", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == "safe"
        assert data["safe"] is True
        assert "scores" in data
        assert "flagged_categories" in data

    @pytest.mark.unit
    async def test_hooks_generation_mock(self, client, avatar_with_lora):
        """
        ✅ SUCCESS CASE 9: Generate hooks with mocked LLM
        
        Mocks:
        - hook_generator.generate_hooks() → returns captions
        
        Expected:
        - HTTP 200
        - Response matches HookGenerationResponse schema
        - Contains: hooks[], platform, content_type
        """
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            "content_type": "image",
            "platform": "instagram",
            "num_variations": 3
        }

        with patch("app.services.hook_generator.hook_generator.generate_hooks") as mock_hooks:
            mock_hooks.return_value = [
                "Transform your fitness journey today! 💪",
                "No pain, no gain! Are you ready? 🔥",
                "Your best self is one workout away! 💯"
            ]

            response = client.post("/api/v1/content/hooks", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "hooks" in data
        assert "platform" in data
        assert "content_type" in data
        assert len(data["hooks"]) > 0


# ============================================================================
# CONTRACT COMPLIANCE TESTS
# ============================================================================

class TestContentAPIContracts:
    """Validate API contracts are maintained (frozen endpoints)"""

    @pytest.mark.contract
    def test_generate_content_response_schema(self, client, avatar_with_lora, dummy_image_base64):
        """
        Contract: ContentPieceResponse must include required fields
        
        Required fields:
        - id (UUID)
        - avatar_id (UUID)
        - content_type (str)
        - access_tier (str)
        - url (str)
        
        Optional fields:
        - hook_text, safety_rating, created_at, metadata
        """
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            "custom_prompt": "test",
            "platform": "instagram"
        }

        with patch(
            "app.services.lora_inference.lora_inference_engine.generate_image_with_lora"
        ) as mock_lora:
            mock_lora.return_value = {
                "image_base64": dummy_image_base64,
                "generation_time": 1.0,
                "parameters": {},
                "cost": 0.01
            }

            response = client.post("/api/v1/content/generate", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Validate required fields exist and are valid types
        assert "id" in data and isinstance(data["id"], str)
        assert "avatar_id" in data and isinstance(data["avatar_id"], str)
        assert "content_type" in data and data["content_type"] in ["image", "video"]
        assert "access_tier" in data and data["access_tier"] in ["capa1", "capa2", "capa3"]
        assert "url" in data and isinstance(data["url"], str)

    @pytest.mark.contract
    def test_batch_generation_status_codes(self, client, avatar_with_lora):
        """
        Contract: /api/v1/content/batch/sync must return correct status codes
        
        - 200: Success
        - 400: Invalid input (avatar not found, no lora, etc)
        - 404: Avatar not found
        - 422: Validation error
        """
        # Test 200 success path with mock
        payload = {
            "avatar_id": str(avatar_with_lora.id),
            "num_pieces": 5,
            "platform": "instagram"
        }

        with patch("app.services.batch_processor.batch_processor.process_batch") as mock_batch:
            mock_batch.return_value = {
                "success": True,
                "avatar_id": str(avatar_with_lora.id),
                "total_pieces": 5,
                "content_pieces": [],
                "statistics": {},
                "config": {}
            }

            response = client.post("/api/v1/content/batch/sync", json=payload)
            assert response.status_code == 200

        # Test 404 for missing avatar
        payload["avatar_id"] = str(uuid4())
        response = client.post("/api/v1/content/batch/sync", json=payload)
        assert response.status_code == 404

        # Test 422 for invalid num_pieces
        payload["avatar_id"] = str(avatar_with_lora.id)
        payload["num_pieces"] = 200
        response = client.post("/api/v1/content/batch/sync", json=payload)
        assert response.status_code == 422

    @pytest.mark.contract
    def test_template_list_contract(self, client):
        """
        Contract: TemplateListResponse schema is fixed
        
        Must include:
        - templates: List[Dict]
        - total: int
        - categories: List[str]
        """
        response = client.get("/api/v1/content/templates")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["templates"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["categories"], list)
        assert data["total"] == len(data["templates"])
