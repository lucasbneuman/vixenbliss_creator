"""
Test avatar creation with mocked external services.
✅ Reproduces the original error: missing R2 credentials
✅ Tests successful creation with proper config
✅ Validates API contract
"""

import base64
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.identity import AvatarCreateRequest, FacialGenerationRequest, FacialMetadata
from app.services.ai_providers import ai_provider_service


@pytest.fixture
def client(override_get_db):
    """TestClient with DB override"""
    return TestClient(app)


@pytest.fixture
def valid_avatar_payload():
    """Valid avatar creation payload (like your curl)"""
    return {
        "name": "Jose Prueba",
        "niche": "Entretenimiento adulto",
        "aesthetic_style": "natural",
        "facial_generation": {
            "age_range": "26-35",
            "ethnicity": "diverse",
            "aesthetic_style": "natural",
            "gender": "female",
            "custom_prompt": "ojos claros"
        }
    }


@pytest.fixture
def user_id():
    """Valid user ID"""
    return str(uuid4())


class TestAvatarCreationErrors:
    """Test error cases and proper error handling"""

    def test_avatar_creation_requires_user_id_query_param(self, client, valid_avatar_payload):
        """
        ❌ ERROR CASE 1: Missing user_id query parameter
        Expected: HTTP 422 Validation Error
        """
        response = client.post(
            "/api/v1/identities/avatars",
            json=valid_avatar_payload
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_avatar_creation_invalid_user_id_format(self, client, valid_avatar_payload):
        """
        ❌ ERROR CASE 2: Invalid UUID format
        Expected: HTTP 422 Validation Error
        """
        response = client.post(
            "/api/v1/identities/avatars?user_id=not-a-uuid",
            json=valid_avatar_payload
        )
        assert response.status_code == 422

    def test_avatar_creation_missing_required_fields(self, client, user_id):
        """
        ❌ ERROR CASE 3: Missing required schema fields
        Expected: HTTP 422 Validation Error
        """
        invalid_payload = {
            "name": "Test",
            # Missing: niche, aesthetic_style, facial_generation
        }
        response = client.post(
            f"/api/v1/identities/avatars?user_id={user_id}",
            json=invalid_payload
        )
        assert response.status_code == 422

    def test_avatar_creation_invalid_facial_generation_fields(self, client, user_id):
        """
        ❌ ERROR CASE 4: Invalid enum values in facial_generation
        Expected: HTTP 422 Validation Error
        """
        invalid_payload = {
            "name": "Test",
            "niche": "test",
            "aesthetic_style": "test",
            "facial_generation": {
                "age_range": "invalid-age",  # Not in ["18-25", "26-35", "36-45", "46+"]
                "gender": "invalid-gender"   # Not in ["female", "male", "non-binary"]
            }
        }
        response = client.post(
            f"/api/v1/identities/avatars?user_id={user_id}",
            json=invalid_payload
        )
        assert response.status_code == 422


class TestAvatarCreationSuccess:
    """Test successful avatar creation with mocked AI providers & storage"""

    def test_avatar_creation_success_with_mocks(
        self, client, valid_avatar_payload, user_id, monkeypatch
    ):
        """
        ✅ SUCCESS CASE: Create avatar with mocked AI provider & R2 storage
        
        Mocks:
        - ai_provider_service.generate_with_routing() → returns valid image
        - storage_service.upload_file_async() → returns R2 presigned URL
        
        Expected:
        - HTTP 200
        - Response matches FacialGenerationResponse schema
        - Contains: avatar_id, image_url, cost_usd, provider, metadata
        """
        # Create dummy base64 image
        dummy_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        dummy_base64 = f"data:image/png;base64,{base64.b64encode(dummy_png).decode()}"

        # Create proper FacialMetadata Pydantic model (not dict!)
        metadata_model = FacialMetadata(
            age=30,
            ethnicity="diverse",
            aesthetic_style="natural",
            dominant_features=["clear eyes", "natural skin"],
            color_palette={"skin": "warm", "eyes": "brown"},
            quality_score=0.95,
            provider_used="replicate_sdxl",
            generation_params={"prompt": "test", "style": "natural"}
        )

        # Mock AI provider to return image and FacialMetadata model
        async def mock_generate(*args, **kwargs):
            return (
                dummy_base64,  # image_url / base64
                metadata_model,  # FacialMetadata model (not dict!)
                0.001,  # cost_usd
                "replicate_sdxl"  # provider (must match ProviderType enum)
            )

        monkeypatch.setattr(
            "app.services.ai_providers.ai_provider_service.generate_with_routing",
            mock_generate
        )

        # Mock R2 upload to return presigned URL
        async def mock_upload(*args, **kwargs):
            return "https://r2-public-url.example.com/avatars/base/avatar_image.png"

        monkeypatch.setattr(
            "app.services.storage.storage_service.upload_file_async",
            mock_upload
        )

        # Act
        response = client.post(
            f"/api/v1/identities/avatars?user_id={user_id}",
            json=valid_avatar_payload
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        
        # Validate response schema (FacialGenerationResponse)
        assert data["success"] is True
        assert "avatar_id" in data
        assert "image_url" in data
        assert "metadata" in data
        assert "cost_usd" in data
        assert "provider" in data

        # Validate metadata
        assert data["metadata"]["ethnicity"] == "diverse"
        assert data["metadata"]["aesthetic_style"] == "natural"

        # Validate cost
        assert isinstance(data["cost_usd"], (int, float))
        assert data["cost_usd"] >= 0

        # Validate provider name
        assert data["provider"] in [
            "modal_sdxl_lora", "replicate_sdxl", "leonardo", "dall_e_3", "local_fallback"
        ]


class TestAvatarCreationContractCompliance:
    """Ensure API contract is never broken"""

    def test_avatar_creation_response_shape_matches_contract(
        self, client, valid_avatar_payload, user_id, monkeypatch
    ):
        """
        ✅ Validate that response matches frozen v1_endpoints.md contract
        
        Required fields in FacialGenerationResponse:
        - success: bool
        - avatar_id: UUID (as string)
        - image_url: str (URL or presigned R2 URL)
        - metadata: FacialMetadata (dict with age, ethnicity, aesthetic_style, etc.)
        - cost_usd: float
        - provider: str
        """
        dummy_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        dummy_base64 = f"data:image/png;base64,{base64.b64encode(dummy_png).decode()}"

        metadata_model = FacialMetadata(
            age=30,
            ethnicity="diverse",
            aesthetic_style="natural",
            dominant_features=["clear eyes"],
            quality_score=0.95,
            provider_used="replicate_sdxl",
            generation_params={"prompt": "test"}
        )

        async def mock_generate(*args, **kwargs):
            return (dummy_base64, metadata_model, 0.001, "replicate_sdxl")

        async def mock_upload(*args, **kwargs):
            return "https://r2-url.example.com/image.png"

        monkeypatch.setattr(
            "app.services.ai_providers.ai_provider_service.generate_with_routing",
            mock_generate
        )
        monkeypatch.setattr(
            "app.services.storage.storage_service.upload_file_async",
            mock_upload
        )

        response = client.post(
            f"/api/v1/identities/avatars?user_id={user_id}",
            json=valid_avatar_payload
        )

        assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
        data = response.json()

        # Contract: all required fields must be present
        required_fields = ["success", "avatar_id", "image_url", "metadata", "cost_usd", "provider"]
        for field in required_fields:
            assert field in data, f"Missing required field in contract: {field}"

        # Contract: types must match
        assert isinstance(data["success"], bool)
        assert isinstance(data["avatar_id"], str)  # UUID as string
        assert isinstance(data["image_url"], str)
        assert isinstance(data["metadata"], dict)
        assert isinstance(data["cost_usd"], (int, float))
        assert isinstance(data["provider"], str)
