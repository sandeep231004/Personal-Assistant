"""
Quick script to convert audio files to WAV format for testing.
This works WITHOUT ffmpeg by using scipy for basic WAV operations.
"""
import sys
from pathlib import Path

def convert_mp3_to_wav_simple(input_file: str, output_file: str = None):
    """
    Convert MP3 to WAV using pydub (requires ffmpeg).
    If ffmpeg not available, direct WAV conversion only.
    """
    if not output_file:
        output_file = Path(input_file).stem + ".wav"

    try:
        from pydub import AudioSegment

        # Load audio
        audio = AudioSegment.from_file(input_file)

        # Convert to mono, 16kHz (optimal for Whisper)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)

        # Export as WAV
        audio.export(output_file, format="wav")
        print(f"✅ Converted: {input_file} → {output_file}")
        return output_file

    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        print("\nThis requires ffmpeg to be installed.")
        print("Please install ffmpeg or use online converter: https://convertio.co/mp3-wav/")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_wav.py <input_audio_file>")
        print("Example: python convert_to_wav.py test.mp3")
        sys.exit(1)

    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    convert_mp3_to_wav_simple(input_file)