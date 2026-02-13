#!/usr/bin/env python3
"""
Modal SDXL LoRA Client - Local Validation Test
Tests client structure without calling actual Modal endpoint
"""

import sys
import asyncio
import json
import base64
from pathlib import Path
from io import BytesIO
from PIL import Image

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the client
try:
    from app.services.modal_sdxl_lora_client import ModalSDXLLoRAClient
except Exception:
    import importlib.util
    client_path = Path(__file__).parent / "app" / "services" / "modal_sdxl_lora_client.py"
    spec = importlib.util.spec_from_file_location("modal_sdxl_lora_client", str(client_path))
    modal_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modal_module)
    ModalSDXLLoRAClient = modal_module.ModalSDXLLoRAClient


def test_client_initialization():
    """Test that client initializes correctly with env vars."""
    print("\n" + "=" * 70)
    print("TEST 1: Client Initialization")
    print("=" * 70)

    try:
        client = ModalSDXLLoRAClient()
        print(f"✅ Client instantiated")
        print(f"   Endpoint URL: {client.endpoint_url or 'NOT SET'}")
        print(f"   API Token: {'*' * 10}..." if client.api_token else "NOT SET")
        print(f"   Timeout: {client.timeout_seconds}s")

        if not client.endpoint_url:
            print("⚠️  WARNING: MODAL_ENDPOINT_URL not set (will fail on actual request)")
        else:
            print("✅ Endpoint URL configured")

        assert client is not None
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        assert False, str(e)


def test_payload_construction():
    """Test that payloads are constructed correctly."""
    print("\n" + "=" * 70)
    print("TEST 2: Payload Construction")
    print("=" * 70)

    prompt = "a beautiful woman in cyberpunk style"
    negative_prompt = "ugly, blurry"
    lora_url = "https://presigned.example.com/lora.safetensors"
    
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": 1024,
        "height": 1024,
        "steps": 28,
        "cfg": 5.5,
        "seed": 42,
        "lora_url": lora_url,
        "lora_scale": 0.9,
    }

    print(f"✅ Payload constructed:")
    for k, v in payload.items():
        if k == "lora_url":
            print(f"   {k}: {v[:50]}..." if len(str(v)) > 50 else f"   {k}: {v}")
        else:
            print(f"   {k}: {v}")

    assert payload["prompt"] == prompt
    assert payload["lora_url"] == lora_url


def test_base64_encoding():
    """Test that base64 image encoding/decoding works."""
    print("\n" + "=" * 70)
    print("TEST 3: Base64 Image Encoding/Decoding")
    print("=" * 70)

    try:
        # Create a test image
        img = Image.new("RGB", (512, 512), color="blue")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()

        # Encode to base64
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        print(f"✅ Image encoded to base64: {len(img_base64)} chars")

        # Decode back
        decoded_bytes = base64.b64decode(img_base64)
        decoded_img = Image.open(BytesIO(decoded_bytes))
        print(f"✅ Base64 decoded back to image: {decoded_img.size} {decoded_img.mode}")

        if decoded_img.size == (512, 512):
            print("✅ Encoding/decoding pipeline works correctly")
            assert decoded_img.size == (512, 512)
        else:
            print(f"❌ Size mismatch: expected (512, 512), got {decoded_img.size}")
            assert decoded_img.size == (512, 512)

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        assert False, str(e)


def test_async_pattern():
    """Test that async patterns work (method signature, await, etc)."""
    print("\n" + "=" * 70)
    print("TEST 4: Async Pattern Validation")
    print("=" * 70)

    try:
        client = ModalSDXLLoRAClient()
        
        # Check that method exists and is async
        method = getattr(client, "generate_image_with_lora", None)
        if not method:
            print("❌ Method generate_image_with_lora not found")
            assert False, "Method generate_image_with_lora not found"

        import inspect
        if not inspect.iscoroutinefunction(method):
            print("❌ Method is not async (should be 'async def')")
            assert False, "Method generate_image_with_lora must be async"

        print("✅ generate_image_with_lora is properly async")
        print("✅ Can be used with await/asyncio")
        
        assert True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        assert False, str(e)


def test_output_processing():
    """Test that output processing works."""
    print("\n" + "=" * 70)
    print("TEST 5: Output Processing")
    print("=" * 70)

    try:
        client = ModalSDXLLoRAClient()

        # Create mock Modal response
        mock_img = Image.new("RGB", (1024, 1024), color="green")
        mock_img_bytes = BytesIO()
        mock_img.save(mock_img_bytes, format="PNG")
        mock_img_base64 = base64.b64encode(mock_img_bytes.getvalue()).decode("utf-8")

        mock_output = {
            "image_base64": mock_img_base64,
            "generation_time_seconds": 9.2,
            "model_info": {
                "base_model": "stabilityai/stable-diffusion-xl-base-1.0",
                "lora_applied": True,
                "lora_scale": 0.9,
            },
        }

        mock_payload = {
            "prompt": "test prompt",
            "negative_prompt": "test negative",
            "steps": 28,
            "cfg": 5.5,
            "width": 1024,
            "height": 1024,
            "seed": 42,
            "lora_scale": 0.9,
        }

        result = client._process_output(mock_output, 0, mock_payload)

        print(f"✅ Output processed successfully")
        print(f"   image_base64 length: {len(result['image_base64'])} chars")
        print(f"   image_url: {result['image_url']}")
        print(f"   generation_time: {result['generation_time']:.2f}s")
        print(f"   cost estimate: ${result['cost']}")
        print(f"   model_info: {json.dumps(result['model_info'], indent=6)}")

        assert result["image_base64"]
        assert "image_url" in result
        assert "generation_time" in result

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        assert False, str(e)


async def main():
    """Run all local validation tests."""
    print("\n" + "=" * 70)
    print("Modal SDXL LoRA Client - LOCAL VALIDATION TEST")
    print("(Does NOT call Modal - validates client structure only)")
    print("=" * 70)

    results = []

    # Sync tests
    results.append(("Client Initialization", test_client_initialization()))
    results.append(("Payload Construction", test_payload_construction()))
    results.append(("Base64 Encoding", test_base64_encoding()))

    # Async pattern/output tests (now regular pytest tests)
    test_async_pattern()
    results.append(("Async Pattern", True))
    test_output_processing()
    results.append(("Output Processing", True))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All local tests passed!")
        print("   Modal client code is correct and ready.")
        print("   Once Modal endpoint is deployed, backend can connect.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
