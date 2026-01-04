"""
Speech-to-Text Service using faster-whisper.

This service handles audio transcription using OpenAI's Whisper model
optimized with faster-whisper for improved performance.

Features:
- Multi-format support (MP3, WAV, M4A, OGG, FLAC)
- Automatic language detection
- Confidence scoring
- Audio preprocessing
- Error handling
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from io import BytesIO
import tempfile

from faster_whisper import WhisperModel
from pydub import AudioSegment
import soundfile as sf

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """
    Service for transcribing audio to text using Whisper.

    Uses faster-whisper for optimized performance on CPU.
    Supports multiple audio formats and provides confidence scores.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize the STT service.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Computation type (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

        # Supported audio formats
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm'}

        logger.info(f"Initializing STT service with model: {model_size}")
        self._load_model()

    def _load_model(self):
        """Load the Whisper model."""
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info(f"Whisper model '{self.model_size}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise

    def _convert_to_wav(self, audio_path: str) -> str:
        """
        Convert audio file to WAV format if needed.

        Args:
            audio_path: Path to input audio file

        Returns:
            Path to WAV file (original or converted)
        """
        file_ext = Path(audio_path).suffix.lower()

        # If already WAV, return as-is
        if file_ext == '.wav':
            return audio_path

        try:
            logger.info(f"Converting {file_ext} to WAV...")

            # Load audio with pydub
            audio = AudioSegment.from_file(audio_path)

            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
                logger.debug("Converted to mono")

            # Normalize audio
            audio = audio.normalize()

            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav'
            )
            temp_wav.close()

            # Export as WAV
            audio.export(
                temp_wav.name,
                format='wav',
                parameters=["-ar", "16000"]  # 16kHz sample rate
            )

            logger.info(f"Audio converted to WAV: {temp_wav.name}")
            return temp_wav.name

        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")

            # Check if this is an ffmpeg issue
            error_msg = str(e)
            if "cannot find the file specified" in error_msg.lower() or "ffmpeg" in error_msg.lower():
                raise ValueError(
                    f"Audio conversion failed: ffmpeg is not installed. "
                    f"Please install ffmpeg (https://ffmpeg.org/) or upload WAV files instead. "
                    f"Current format: {file_ext}"
                )
            else:
                raise ValueError(f"Failed to convert audio format: {str(e)}")

    def _preprocess_audio(self, audio_path: str) -> str:
        """
        Preprocess audio file for better transcription.

        Args:
            audio_path: Path to audio file

        Returns:
            Path to preprocessed audio file
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)

            # Convert to mono if needed
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Normalize volume
            audio = audio.normalize()

            # Remove silence from beginning and end
            audio = audio.strip_silence(
                silence_thresh=-40,  # dB
                padding=100  # ms
            )

            # Save preprocessed audio
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav'
            )
            temp_file.close()

            audio.export(
                temp_file.name,
                format='wav',
                parameters=["-ar", "16000"]
            )

            return temp_file.name

        except Exception as e:
            logger.warning(f"Audio preprocessing failed, using original: {str(e)}")
            return audio_path

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr'). Auto-detect if None.
            preprocess: Whether to preprocess audio

        Returns:
            Dictionary with transcription results:
            {
                "text": "transcribed text",
                "language": "en",
                "confidence": 0.95,
                "segments": [...],
                "duration": 10.5
            }
        """
        if not self.model:
            raise RuntimeError("Whisper model not loaded")

        # Validate file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Check file format
        file_ext = Path(audio_path).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(
                f"Unsupported audio format: {file_ext}. "
                f"Supported formats: {self.supported_formats}"
            )

        logger.info(f"Transcribing audio: {audio_path}")
        temp_files = []

        try:
            # Preprocess if requested
            if preprocess:
                processed_path = self._preprocess_audio(audio_path)
                temp_files.append(processed_path)
                audio_path = processed_path

            # Convert to WAV if needed
            wav_path = self._convert_to_wav(audio_path)
            if wav_path != audio_path:
                temp_files.append(wav_path)

            # Transcribe with Whisper
            segments, info = self.model.transcribe(
                wav_path,
                language=language,
                beam_size=5,
                vad_filter=True,  # Voice Activity Detection
                vad_parameters=dict(
                    #threshold=0.5,
                    min_speech_duration_ms=250
                )
            )

            # Collect segments
            all_segments = []
            full_text = []
            total_confidence = 0
            segment_count = 0

            for segment in segments:
                all_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": segment.avg_logprob
                })
                full_text.append(segment.text.strip())
                total_confidence += segment.avg_logprob
                segment_count += 1

            # Calculate average confidence
            avg_confidence = (total_confidence / segment_count) if segment_count > 0 else 0

            # Normalize confidence to 0-1 range (log prob is negative)
            # Whisper log probs typically range from -1 to 0
            normalized_confidence = max(0, min(1, (avg_confidence + 1)))

            result = {
                "text": " ".join(full_text),
                "language": info.language,
                "language_probability": info.language_probability,
                "confidence": round(normalized_confidence, 3),
                "duration": info.duration,
                "segments": all_segments,
                "num_segments": len(all_segments)
            }

            logger.info(
                f"Transcription complete: {len(result['text'])} chars, "
                f"language: {result['language']}, "
                f"confidence: {result['confidence']}"
            )

            return result

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {str(e)}")

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        format: str = 'mp3',
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio from bytes.

        Args:
            audio_bytes: Audio file as bytes
            format: Audio format (mp3, wav, etc.)
            language: Language code (auto-detect if None)

        Returns:
            Transcription result dictionary
        """
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f'.{format}'
        )

        try:
            # Write bytes to file
            temp_file.write(audio_bytes)
            temp_file.close()

            # Transcribe
            result = self.transcribe(temp_file.name, language=language)
            return result

        finally:
            # Cleanup
            try:
                os.unlink(temp_file.name)
            except:
                pass


# Singleton instance
_stt_service = None


def get_stt_service(
    model_size: str = "base",
    device: str = "cpu"
) -> SpeechToTextService:
    """
    Get or create the STT service instance (singleton).

    Args:
        model_size: Whisper model size (tiny, base, small, medium, large)
        device: Device to run on (cpu, cuda)

    Returns:
        SpeechToTextService instance
    """
    global _stt_service

    if _stt_service is None:
        _stt_service = SpeechToTextService(
            model_size=model_size,
            device=device
        )

    return _stt_service

