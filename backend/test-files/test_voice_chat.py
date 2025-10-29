"""
Test script for voice-chat endpoint.
Sends audio, gets response, and saves the audio output.
"""
import requests
import base64
import json
from pathlib import Path


def test_voice_chat(audio_file_path: str, session_id: str = "test-session", voice: str = "en-US-AriaNeural"):
    """
    Test the voice-chat endpoint.

    Args:
        audio_file_path: Path to audio file (WAV recommended)
        session_id: Session ID for conversation
        voice: Voice to use for TTS response
    """
    url = "http://localhost:8000/api/voice-chat"

    print(f"\n{'='*60}")
    print(f"🎤 Testing Voice Chat Endpoint")
    print(f"{'='*60}")
    print(f"Audio file: {audio_file_path}")
    print(f"Session ID: {session_id}")
    print(f"Voice: {voice}")
    print(f"{'='*60}\n")

    # Check if file exists
    if not Path(audio_file_path).exists():
        print(f"❌ Error: File not found: {audio_file_path}")
        return

    try:
        # Prepare the request
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': (Path(audio_file_path).name, f, 'audio/wav')}
            data = {
                'session_id': session_id,
                'voice': voice
            }

            print("📤 Sending request...")
            response = requests.post(url, files=files, data=data)

        # Check response
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return

        # Parse JSON response
        result = response.json()

        print("\n✅ SUCCESS! Response received:\n")
        print(f"📝 Transcript: {result['transcript']}")
        print(f"🤖 Response Text: {result['response_text'][:200]}{'...' if len(result['response_text']) > 200 else ''}")
        print(f"🛠️  Tools Used: {', '.join(result['tools_used']) if result['tools_used'] else 'None'}")
        print(f"🌍 Language: {result['language']}")
        print(f"📊 Confidence: {result['confidence']}")

        # Decode and save audio
        audio_base64 = result['response_audio_base64']
        audio_bytes = base64.b64decode(audio_base64)

        # Save audio file
        output_file = f"voice_response_{session_id}.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_bytes)

        print(f"\n🔊 Audio saved to: {output_file}")
        print(f"   Size: {len(audio_bytes):,} bytes ({len(audio_bytes)/1024:.1f} KB)")
        print(f"\n▶️  You can now play the audio file!")

        # Save full response as JSON
        json_output = f"voice_response_{session_id}.json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"📄 Full response saved to: {json_output}")

        return result

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server.")
        print("Make sure the server is running: python -m uvicorn app.main:app")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    # Get audio file from command line or use default
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        print("Usage: python test_voice_chat.py <audio_file.wav> [session_id] [voice]")
        print("\nExample:")
        print("  python test_voice_chat.py harvard.wav")
        print("  python test_voice_chat.py test.wav my-session en-GB-RyanNeural")
        sys.exit(1)

    session_id = sys.argv[2] if len(sys.argv) > 2 else "test-session"
    voice = sys.argv[3] if len(sys.argv) > 3 else "en-US-AriaNeural"

    test_voice_chat(audio_file, session_id, voice)
