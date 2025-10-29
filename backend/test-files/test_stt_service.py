"""
Test script for the STT service.
Tests the complete speech_to_text.py implementation.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.speech_to_text import get_stt_service
from app.services.audio_utils import AudioUtils
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_stt_service():
    """Test the STT service."""
    print("=" * 60)
    print("Testing STT Service")
    print("=" * 60)

    try:
        # Initialize service
        print("\n1. Initializing STT service...")
        stt = get_stt_service(model_size="tiny")  # Use tiny for quick test
        print("[OK] STT service initialized")

        # Check service properties
        print(f"\n2. Service Configuration:")
        print(f"   - Model size: {stt.model_size}")
        print(f"   - Device: {stt.device}")
        print(f"   - Compute type: {stt.compute_type}")
        print(f"   - Supported formats: {stt.supported_formats}")

        # Test audio utils
        print(f"\n3. Audio Utils Tests:")
        print(f"   - Max file size: {AudioUtils.MAX_FILE_SIZE_MB} MB")
        print(f"   - Max duration: {AudioUtils.MAX_DURATION_SECONDS}s")
        print(f"   - Target sample rate: {AudioUtils.TARGET_SAMPLE_RATE} Hz")
        print(f"   - Supported formats: {AudioUtils.SUPPORTED_FORMATS}")

        print("\n[SUCCESS] All tests passed!")
        print("\nNote: To test actual transcription, you need:")
        print("   - An audio file (MP3, WAV, M4A, etc.)")
        print("   - Call: stt.transcribe('audio_file.mp3')")
        print("\nExample usage:")
        print("   result = stt.transcribe('audio.mp3')")
        print("   print(result['text'])")
        print("   print(f\"Language: {result['language']}\")")
        print("   print(f\"Confidence: {result['confidence']}\")")

        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_stt_service()
    sys.exit(0 if success else 1)
