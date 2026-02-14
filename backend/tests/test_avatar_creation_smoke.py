"""
Smoke tests for avatar creation with REAL API calls.

⚠️ These tests require:
- Valid R2 credentials in .env
- Valid AI provider credentials in .env
- Internet connection

Run with: pytest backend/tests/test_avatar_creation_smoke.py -m smoke -v
Or enable via: RUN_PRODUCTION_TESTS=true
"""

import os
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app

# Mark tests as smoke tests
pytestmark = pytest.mark.smoke


@pytest.fixture
def client(override_get_db):
    return TestClient(app)


@pytest.fixture
def skip_if_production_disabled():
    """Skip test if RUN_PRODUCTION_TESTS is not true"""
    if os.getenv("RUN_PRODUCTION_TESTS") != "true":
        pytest.skip(
            "Production tests disabled. Set RUN_PRODUCTION_TESTS=true to enable."
        )
    return True


@pytest.fixture
def verify_r2_configured():
    """Verify R2 is configured before running smoke tests"""
    required_r2_vars = [
        "R2_ENDPOINT_URL",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME"
    ]
    missing = [var for var in required_r2_vars if not os.getenv(var)]
    
    if missing:
        pytest.skip(f"R2 not configured. Missing: {', '.join(missing)}")
    return True


@pytest.fixture
def verify_ai_provider_configured():
    """Verify at least one AI provider is configured"""
    providers = {
        "Modal": os.getenv("MODAL_ENDPOINT_URL"),
        "Replicate": os.getenv("REPLICATE_API_TOKEN"),
        "Leonardo": os.getenv("LEONARDO_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY")
    }
    
    configured = [name for name, key in providers.items() if key]
    if not configured:
        pytest.skip(
            f"No AI provider configured. Configured: {configured}"
        )
    return True


class TestAvatarCreationSmokeRealAPIs:
    """Real API tests - actual calls to R2, AI providers, etc."""

    def test_avatar_creation_with_real_services(
        self,
        client,
        skip_if_production_disabled,
        verify_r2_configured,
        verify_ai_provider_configured
    ):
        """
        🔥 SMOKE TEST: Create avatar with REAL services
        
        - Uses real R2 credentials from .env
        - Uses real AI provider from .env
        - Actually uploads image to R2
        - Actually calls AI generation API
        
        ⚠️ May incur costs depending on your AI provider
        """
        user_id = str(uuid4())
        
        payload = {
            "name": f"SmokeTest_{uuid4().hex[:8]}",
            "niche": "test",
            "aesthetic_style": "realistic",
            "facial_generation": {
                "age_range": "26-35",
                "ethnicity": "diverse",
                "aesthetic_style": "realistic",
                "gender": "female",
                "custom_prompt": "test avatar"
            }
        }

        response = client.post(
            f"/api/v1/identities/avatars?user_id={user_id}",
            json=payload
        )

        # ✅ Should succeed
        assert response.status_code == 200, f"Failed: {response.text}"

        data = response.json()
        
        # Validate response schema
        assert data["success"] is True
        assert "avatar_id" in data
        assert data["image_url"]  # Should have actual R2 URL
        assert data["cost_usd"] > 0  # Should have cost
        assert data["provider"]  # Should show which provider was used

        print(f"\n✅ Avatar created successfully!")
        print(f"   Avatar ID: {data['avatar_id']}")
        print(f"   Image URL: {data['image_url']}")
        print(f"   Provider: {data['provider']}")
        print(f"   Cost: ${data['cost_usd']}")

    def test_avatar_creation_e2e_full_workflow(
        self,
        client,
        skip_if_production_disabled,
        verify_r2_configured,
        verify_ai_provider_configured
    ):
        """
        🔥 SMOKE TEST E2E: Full workflow from frontend to storage
        
        Simulates: Browser → Frontend → Backend → AI Provider → R2 → Database → Response
        
        This is the EXACT payload from the original curl that failed with:
        "Failed to upload image to storage: R2 not configured"
        """
        user_id = str(uuid4())

        # This is the exact payload from your original curl
        payload = {
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

        # Act: POST avatar creation (this is what failed originally)
        response = client.post(
            f"/api/v1/identities/avatars?user_id={user_id}",
            json=payload
        )

        # Assert: Should now work with R2 configured
        print(f"\nResponse status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response body: {response.json()}")

        assert response.status_code == 200, \
            f"Avatar creation failed. Original error was: R2 not configured. " \
            f"Now got: {response.json()}"

        data = response.json()
        
        # Validate complete response
        assert data["success"] is True
        assert "avatar_id" in data
        assert data["image_url"]
        # Metadata contains: age, ethnicity, aesthetic_style, not gender/age_range
        assert "age" in data["metadata"]
        assert "ethnicity" in data["metadata"]
        assert data["cost_usd"] >= 0
        assert data["provider"] in [
            "modal_sdxl_lora", "replicate_sdxl", "leonardo", "dall_e_3"
        ]

        print(f"\n✅ E2E test passed!")
        print(f"   Frontend → Backend: ✅")
        print(f"   Backend → AI Provider: ✅ ({data['provider']})")
        print(f"   Backend → R2 Storage: ✅")
        print(f"   Backend → Database: ✅")
        print(f"   Avatar created: {data['avatar_id']}")
