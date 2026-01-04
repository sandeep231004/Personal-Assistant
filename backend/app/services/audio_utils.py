"""
Audio processing utilities for voice integration.

Provides helper functions for audio format validation, conversion,
and preprocessing.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from pydub import AudioSegment
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioUtils:
    """Utility class for audio processing operations."""

    # Supported formats
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm'}

    # Audio constraints
    MAX_FILE_SIZE_MB = 10
    MAX_DURATION_SECONDS = 60
    TARGET_SAMPLE_RATE = 16000  # 16kHz for STT

    @staticmethod
    def validate_audio_file(file_path: str, check_size: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate audio file.

        Args:
            file_path: Path to audio file
            check_size: Whether to check file size

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        # Check format
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in AudioUtils.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {file_ext}. Supported: {AudioUtils.SUPPORTED_FORMATS}"

        # Check file size
        if check_size:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > AudioUtils.MAX_FILE_SIZE_MB:
                return False, f"File too large: {file_size_mb:.2f} MB (max: {AudioUtils.MAX_FILE_SIZE_MB} MB)"

        return True, None

    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """
        Get audio file information.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with audio info
        """
        try:
            audio = AudioSegment.from_file(file_path)

            return {
                "duration": len(audio) / 1000.0,  # Convert ms to seconds
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "sample_width": audio.sample_width,
                "frame_count": audio.frame_count(),
                "file_size": os.path.getsize(file_path),
                "format": Path(file_path).suffix.lower()
            }
        except Exception as e:
            logger.error(f"Failed to get audio info: {str(e)}")
            return {}

    @staticmethod
    def convert_to_mono(audio: AudioSegment) -> AudioSegment:
        """
        Convert stereo audio to mono.

        Args:
            audio: AudioSegment object

        Returns:
            Mono AudioSegment
        """
        if audio.channels > 1:
            return audio.set_channels(1)
        return audio

    @staticmethod
    def normalize_volume(audio: AudioSegment) -> AudioSegment:
        """
        Normalize audio volume.

        Args:
            audio: AudioSegment object

        Returns:
            Normalized AudioSegment
        """
        return audio.normalize()

    @staticmethod
    def trim_silence(
        audio: AudioSegment,
        silence_thresh: int = -40,
        padding: int = 100
    ) -> AudioSegment:
        """
        Remove silence from beginning and end.

        Args:
            audio: AudioSegment object
            silence_thresh: Silence threshold in dB
            padding: Padding in milliseconds

        Returns:
            Trimmed AudioSegment
        """
        return audio.strip_silence(
            silence_thresh=silence_thresh,
            padding=padding
        )

    @staticmethod
    def change_sample_rate(
        audio: AudioSegment,
        target_rate: int = 16000
    ) -> AudioSegment:
        """
        Change audio sample rate.

        Args:
            audio: AudioSegment object
            target_rate: Target sample rate in Hz

        Returns:
            Resampled AudioSegment
        """
        return audio.set_frame_rate(target_rate)

    @staticmethod
    def get_format_from_bytes(audio_bytes: bytes) -> Optional[str]:
        """
        Try to detect audio format from bytes.

        Args:
            audio_bytes: Audio file bytes

        Returns:
            Format string or None
        """
        # Check magic bytes
        if audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff\xfb'):
            return 'mp3'
        elif audio_bytes.startswith(b'RIFF'):
            return 'wav'
        elif audio_bytes.startswith(b'ftyp'):
            return 'm4a'
        elif audio_bytes.startswith(b'OggS'):
            return 'ogg'
        elif audio_bytes.startswith(b'fLaC'):
            return 'flac'

        return None

    @staticmethod
    def validate_duration(file_path: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Check if audio duration is within limits.

        Args:
            file_path: Path to audio file

        Returns:
            Tuple of (is_valid, error_message, duration)
        """
        try:
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0  # Convert to seconds

            if duration > AudioUtils.MAX_DURATION_SECONDS:
                return False, f"Audio too long: {duration:.1f}s (max: {AudioUtils.MAX_DURATION_SECONDS}s)", duration

            if duration < 0.1:  # Minimum 0.1 seconds
                return False, "Audio too short (min: 0.1s)", duration

            return True, None, duration

        except Exception as e:
            return False, f"Failed to check duration: {str(e)}", None


def preprocess_for_stt(audio_path: str, output_path: str = None) -> str:
    """
    Preprocess audio file for STT.

    Applies:
    - Mono conversion
    - Volume normalization
    - Silence trimming
    - 16kHz sample rate

    Args:
        audio_path: Input audio file path
        output_path: Output file path (temp file if None)

    Returns:
        Path to preprocessed audio file
    """
    try:
        # Load audio
        audio = AudioSegment.from_file(audio_path)

        # Apply preprocessing
        audio = AudioUtils.convert_to_mono(audio)
        audio = AudioUtils.normalize_volume(audio)
        audio = AudioUtils.trim_silence(audio)
        audio = AudioUtils.change_sample_rate(audio, AudioUtils.TARGET_SAMPLE_RATE)

        # Save
        if output_path is None:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            output_path = temp_file.name
            temp_file.close()

        audio.export(
            output_path,
            format='wav',
            parameters=["-ar", str(AudioUtils.TARGET_SAMPLE_RATE)]
        )

        logger.info(f"Preprocessed audio saved to: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise


def estimate_transcription_time(audio_duration: float, model_size: str = "base") -> float:
    """
    Estimate transcription time based on audio duration and model size.

    Args:
        audio_duration: Audio duration in seconds
        model_size: Whisper model size

    Returns:
        Estimated time in seconds
    """
    # Rough estimates (CPU)
    speed_factors = {
        'tiny': 0.5,    # 2x faster than real-time
        'base': 1.0,    # Real-time
        'small': 2.0,   # 2x slower
        'medium': 4.0,  # 4x slower
        'large': 8.0    # 8x slower
    }

    factor = speed_factors.get(model_size, 1.0)
    return audio_duration * factor
