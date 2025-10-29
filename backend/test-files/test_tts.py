"""
Test script for Text-to-Speech using edge-tts.
This script generates sample speech and saves it to a file.
"""
import edge_tts
import asyncio
import os
import sys

async def test_edge_tts():
    """Test if edge-tts is properly installed and working."""
    print("=" * 60)
    print("Testing edge-tts (Text-to-Speech)")
    print("=" * 60)

    try:
        # Test text
        test_text = "Hello! This is a test of the text-to-speech system. The voice integration is working perfectly!"

        print("\n1. Testing TTS with sample text...")
        print(f"   Text: \"{test_text}\"")

        # Available voices
        print("\n2. Getting available voices...")
        voices = await edge_tts.list_voices()

        # Show some popular voices
        print("\n3. Popular English voices:")
        en_voices = [v for v in voices if v["Locale"].startswith("en-")][:5]
        for v in en_voices:
            print(f"   - {v['ShortName']}: {v['Gender']} ({v['Locale']})")

        # Generate speech
        print("\n4. Generating speech sample...")
        voice = "en-US-AriaNeural"  # Default voice
        output_file = "test_output.mp3"

        communicate = edge_tts.Communicate(test_text, voice)
        await communicate.save(output_file)

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"[OK] Audio generated successfully!")
            print(f"   - File: {output_file}")
            print(f"   - Size: {file_size} bytes")
            print(f"   - Voice: {voice}")

            # Cleanup
            os.remove(output_file)
            print(f"\n[OK] Test file cleaned up")
        else:
            print(f"[ERROR] Failed to generate audio file")
            return False

        print("\n[SUCCESS] edge-tts is working correctly!")
        print(f"\nTotal voices available: {len(voices)}")
        print(f"English voices available: {len(en_voices)}")

        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_edge_tts())
    sys.exit(0 if success else 1)
