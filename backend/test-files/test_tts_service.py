"""
Test script for the TTS service.
Tests the complete text_to_speech.py implementation.
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.text_to_speech import get_tts_service
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_tts_service():
    """Test the TTS service."""
    print("=" * 60)
    print("Testing TTS Service")
    print("=" * 60)

    try:
        # Initialize service
        print("\n1. Initializing TTS service...")
        tts = get_tts_service()
        print("[OK] TTS service initialized")

        # Check service properties
        print(f"\n2. Service Configuration:")
        print(f"   - Default voice: {tts.default_voice}")
        print(f"   - Popular voices available: {len(tts.POPULAR_VOICES)}")

        # Test getting voices
        print(f"\n3. Fetching available voices...")
        voices = await tts.get_available_voices()
        print(f"[OK] Found {len(voices)} total voices")

        # Show some popular voices
        print(f"\n4. Sample Popular Voices:")
        for key, voice_id in list(tts.POPULAR_VOICES.items())[:5]:
            print(f"   - {key}: {voice_id}")

        # Test synthesis
        print(f"\n5. Testing speech synthesis...")
        test_text = "Hello! This is a test of the text-to-speech service. It's working great!"

        audio_bytes = await tts.synthesize(test_text)
        print(f"[OK] Synthesized {len(audio_bytes)} bytes of audio")

        # Test saving to file
        print(f"\n6. Testing file save...")
        output_file = "test_tts_output.mp3"
        await tts.synthesize_to_file(test_text, output_file)

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"[OK] Audio saved: {output_file} ({file_size} bytes)")

            # Cleanup
            os.remove(output_file)
            print(f"[OK] Test file cleaned up")
        else:
            print(f"[ERROR] File not created")
            return False

        print("\n[SUCCESS] All TTS tests passed!")
        print("\nExample usage:")
        print("   tts = get_tts_service()")
        print("   audio = await tts.synthesize('Hello world')")
        print("   # or synchronous:")
        print("   audio = tts.synthesize_sync('Hello world')")

        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tts_service())
    sys.exit(0 if success else 1)
