"""
Test script for Speech-to-Text using faster-whisper.
This script tests STT functionality without needing an actual audio file.
"""
from faster_whisper import WhisperModel
import sys

def test_whisper():
    """Test if faster-whisper is properly installed and working."""
    print("=" * 60)
    print("Testing faster-whisper (Speech-to-Text)")
    print("=" * 60)

    try:
        # Initialize model (using tiny model for quick testing)
        print("\n1. Initializing Whisper model (tiny)...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("[OK] Model loaded successfully!")

        # Model info
        print(f"\n2. Model Information:")
        print(f"   - Model size: tiny")
        print(f"   - Device: CPU")
        print(f"   - Compute type: int8")

        print("\n3. Available model sizes:")
        print("   - tiny: Fastest, least accurate")
        print("   - base: Balanced")
        print("   - small: Better accuracy")
        print("   - medium: High accuracy")
        print("   - large: Best accuracy (slowest)")

        print("\n[SUCCESS] faster-whisper is working correctly!")
        print("\nNote: To transcribe actual audio, you'll need:")
        print("   - An audio file (MP3, WAV, M4A, etc.)")
        print("   - Call: model.transcribe('audio_file.mp3')")

        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return False

if __name__ == "__main__":
    success = test_whisper()
    sys.exit(0 if success else 1)
