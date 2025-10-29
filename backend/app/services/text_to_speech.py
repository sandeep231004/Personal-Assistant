"""
Text-to-Speech Service using edge-tts.

This service handles text-to-speech conversion using Microsoft's
edge-tts library (Azure Neural TTS).

Features:
- 550+ natural-sounding voices
- Multiple languages and accents
- Free unlimited usage
- High-quality MP3 output
- Voice customization (rate, pitch, volume)
"""
import os
import logging
import asyncio
from typing import Optional, List, Dict
from pathlib import Path
import tempfile

import edge_tts

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """
    Service for converting text to speech using edge-tts.

    Uses Microsoft Azure Neural TTS for natural-sounding speech.
    Supports 550+ voices across multiple languages.
    """

    # Popular voices for quick access
    POPULAR_VOICES = {
        'en-US-female': 'en-US-AriaNeural',
        'en-US-male': 'en-US-GuyNeural',
        'en-GB-female': 'en-GB-SoniaNeural',
        'en-GB-male': 'en-GB-RyanNeural',
        'en-AU-female': 'en-AU-NatashaNeural',
        'en-AU-male': 'en-AU-WilliamNeural',
        'es-US-female': 'es-US-PalomaNeural',
        'es-US-male': 'es-US-AlonsoNeural',
        'fr-FR-female': 'fr-FR-DeniseNeural',
        'fr-FR-male': 'fr-FR-HenriNeural',
        'de-DE-female': 'de-DE-KatjaNeural',
        'de-DE-male': 'de-DE-ConradNeural',
    }

    def __init__(self, default_voice: str = "en-US-AriaNeural"):
        """
        Initialize the TTS service.

        Args:
            default_voice: Default voice to use
        """
        self.default_voice = default_voice
        self.available_voices = None
        logger.info(f"Initializing TTS service with default voice: {default_voice}")

    async def get_available_voices(self) -> List[Dict]:
        """
        Get list of all available voices.

        Returns:
            List of voice dictionaries with metadata
        """
        if self.available_voices is None:
            logger.info("Fetching available voices...")
            self.available_voices = await edge_tts.list_voices()
            logger.info(f"Found {len(self.available_voices)} voices")

        return self.available_voices

    async def get_voices_by_language(self, language_code: str) -> List[Dict]:
        """
        Get voices for a specific language.

        Args:
            language_code: Language code (e.g., 'en-US', 'es-ES')

        Returns:
            List of matching voices
        """
        all_voices = await self.get_available_voices()
        return [v for v in all_voices if v['Locale'].startswith(language_code)]

    def get_popular_voice(self, key: str) -> str:
        """
        Get a popular voice by key.

        Args:
            key: Voice key (e.g., 'en-US-female', 'en-GB-male')

        Returns:
            Voice ID or default voice if not found
        """
        return self.POPULAR_VOICES.get(key, self.default_voice)

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> bytes:
        """
        Convert text to speech.

        Args:
            text: Text to convert
            voice: Voice to use (default voice if None)
            rate: Speech rate (-50% to +100%)
            pitch: Speech pitch (-50Hz to +50Hz)
            volume: Speech volume (-50% to +50%)

        Returns:
            Audio bytes (MP3 format)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        voice = voice or self.default_voice

        logger.info(f"Synthesizing speech: {len(text)} chars with voice '{voice}'")

        try:
            # Create communicate object
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            # Collect audio chunks
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])

            # Combine chunks
            audio_bytes = b''.join(audio_chunks)

            logger.info(f"Speech synthesized: {len(audio_bytes)} bytes")
            return audio_bytes

        except Exception as e:
            logger.error(f"Speech synthesis failed: {str(e)}")
            raise

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",  # Fixed: must be in Hz format, not %
        volume: str = "+0%"
    ) -> str:
        """
        Convert text to speech and save to file.

        Args:
            text: Text to convert
            output_path: Path to save audio file
            voice: Voice to use (default if None)
            rate: Speech rate
            pitch: Speech pitch (in Hz format, e.g., "+0Hz", "+10Hz")
            volume: Speech volume

        Returns:
            Path to saved audio file
        """
        voice = voice or self.default_voice

        logger.info(f"Synthesizing to file: {output_path}")

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            await communicate.save(output_path)

            logger.info(f"Audio saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            raise

    def synthesize_sync(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0%",
        volume: str = "+0%"
    ) -> bytes:
        """
        Synchronous version of synthesize.

        Args:
            text: Text to convert
            voice: Voice to use
            rate: Speech rate
            pitch: Speech pitch
            volume: Speech volume

        Returns:
            Audio bytes
        """
        return asyncio.run(self.synthesize(text, voice, rate, pitch, volume))

    def synthesize_to_file_sync(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",  # Fixed: must be in Hz format
        volume: str = "+0%"
    ) -> str:
        """
        Synchronous version of synthesize_to_file.

        Args:
            text: Text to convert
            output_path: Output file path
            voice: Voice to use
            rate: Speech rate
            pitch: Speech pitch (in Hz format)
            volume: Speech volume

        Returns:
            Path to saved file
        """
        return asyncio.run(
            self.synthesize_to_file(text, output_path, voice, rate, pitch, volume)
        )

    async def synthesize_chunks(
        self,
        text: str,
        max_chunk_length: int = 500,
        voice: Optional[str] = None
    ) -> bytes:
        """
        Synthesize long text by splitting into chunks.

        Args:
            text: Long text to convert
            max_chunk_length: Maximum characters per chunk
            voice: Voice to use

        Returns:
            Combined audio bytes
        """
        # Split text into sentences
        sentences = text.replace('\n', ' ').split('. ')

        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            if current_length + sentence_length > max_chunk_length and current_chunk:
                # Save current chunk and start new one
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add remaining chunk
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')

        logger.info(f"Synthesizing {len(chunks)} chunks")

        # Synthesize each chunk
        audio_parts = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Synthesizing chunk {i+1}/{len(chunks)}")
            audio_bytes = await self.synthesize(chunk, voice=voice)
            audio_parts.append(audio_bytes)

        # Combine audio (simple concatenation for MP3)
        combined_audio = b''.join(audio_parts)

        logger.info(f"Combined audio: {len(combined_audio)} bytes")
        return combined_audio


# Singleton instance
_tts_service = None


def get_tts_service(default_voice: str = "en-US-AriaNeural") -> TextToSpeechService:
    """
    Get or create the TTS service instance (singleton).

    Args:
        default_voice: Default voice to use

    Returns:
        TextToSpeechService instance
    """
    global _tts_service

    if _tts_service is None:
        _tts_service = TextToSpeechService(default_voice=default_voice)

    return _tts_service
