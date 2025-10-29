"""
Voice API Routes - Speech-to-Text and Text-to-Speech endpoints.

This module provides voice interaction endpoints:
- /api/transcribe: Convert audio to text (STT)
- /api/speak: Convert text to audio (TTS)
- /api/voice-chat: Complete voice interaction (audio in, audio out)
"""
from app.models import Conversation
from app.models import Conversation
import logging
import base64
import tempfile
import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation
from app.services.speech_to_text import get_stt_service
from app.services.text_to_speech import get_tts_service
from app.agents.voice_agent import get_agent

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["voice"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TranscribeResponse(BaseModel):
    """Response model for transcription."""
    text: str = Field(description="Transcribed text")
    language: str = Field(description="Detected language code")
    language_probability: float = Field(description="Language detection confidence")
    confidence: float = Field(description="Overall transcription confidence")
    duration: float = Field(description="Audio duration in seconds")
    num_segments: int = Field(description="Number of segments")


class SpeakRequest(BaseModel):
    """Request model for speech synthesis."""
    text: str = Field(description="Text to convert to speech")
    voice: Optional[str] = Field(
        default="en-US-AriaNeural",
        description="Voice ID to use"
    )
    rate: Optional[str] = Field(default="+0%", description="Speech rate (-50% to +100%)")
    pitch: Optional[str] = Field(default="+0Hz", description="Speech pitch (-50Hz to +50Hz)")
    volume: Optional[str] = Field(default="+0%", description="Speech volume (-50% to +50%)")


class VoiceChatResponse(BaseModel):
    """Response model for voice chat."""
    transcript: str = Field(description="User's transcribed speech")
    response_text: str = Field(description="Agent's text response")
    response_audio_base64: str = Field(description="Agent's audio response (base64)")
    tools_used: list = Field(description="Tools used by agent")
    session_id: str = Field(description="Conversation session ID")
    language: str = Field(description="Detected language")
    confidence: float = Field(description="Transcription confidence")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Language code (auto-detect if None)")
):
    """
    Convert audio to text (Speech-to-Text).

    **Supported formats:** MP3, WAV, M4A, OGG, FLAC, WEBM
    **Max file size:** 10 MB
    **Max duration:** 60 seconds

    Returns the transcribed text with confidence scores and metadata.
    """
    logger.info(f"Transcription request: {audio_file.filename}")

    # Validate file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1])
        content = await audio_file.read()
        temp_file.write(content)
        temp_file.close()

        # Get STT service
        stt = get_stt_service(model_size="base")  # Use base model for balance

        # Transcribe (disable preprocessing if ffmpeg not available)
        result = stt.transcribe(temp_file.name, language=language, preprocess=False)

        logger.info(f"Transcription complete: {len(result['text'])} chars")

        # Cleanup - check if file still exists before deleting
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        return TranscribeResponse(
            text=result['text'],
            language=result['language'],
            language_probability=result['language_probability'],
            confidence=result['confidence'],
            duration=result['duration'],
            num_segments=result['num_segments']
        )

    except Exception as e:
        # Cleanup on error - check if file exists first
        try:
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup failed: {str(cleanup_error)}")

        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/speak")
async def synthesize_speech(request: SpeakRequest):
    """
    Convert text to speech (Text-to-Speech).

    **Voices:** 550+ voices available across multiple languages
    **Output:** MP3 audio file
    **Popular voices:**
    - en-US-AriaNeural (female, American)
    - en-US-GuyNeural (male, American)
    - en-GB-SoniaNeural (female, British)

    Returns audio file as downloadable MP3.
    """
    logger.info(f"TTS request: {len(request.text)} chars with voice '{request.voice}'")

    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        # Get TTS service
        tts = get_tts_service()

        # Synthesize speech (use async version since endpoint is async)
        audio_bytes = await tts.synthesize(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch,
            volume=request.volume
        )

        logger.info(f"TTS complete: {len(audio_bytes)} bytes")

        # Return audio file
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'attachment; filename="speech.mp3"'
            }
        )

    except Exception as e:
        logger.error(f"TTS failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


@router.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio_file: UploadFile = File(..., description="Audio file with user's query"),
    session_id: str = Form("default", description="Conversation session ID"),
    voice: Optional[str] = Form("en-US-AriaNeural", description="Voice for response"),
    db: Session = Depends(get_db)
):
    """
    Complete voice interaction: Audio input → Agent processing → Audio output.

    **Flow:**
    1. Transcribe user's audio (STT)
    2. Process query with AI agent (uses all 11 tools)
    3. Synthesize response to audio (TTS)

    **Supported formats:** MP3, WAV, M4A, OGG, FLAC, WEBM

    Returns both text and audio response with conversation metadata.
    """
    logger.info(f"Voice chat request: {audio_file.filename}, session: {session_id}")

    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    temp_file = None

    try:
        # Step 1: Save uploaded audio
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(audio_file.filename)[1]
        )
        content = await audio_file.read()
        temp_file.write(content)
        temp_file.close()

        # Step 2: Transcribe audio (STT)
        logger.info("Step 1/3: Transcribing audio...")
        stt = get_stt_service(model_size="base")
        transcription = stt.transcribe(temp_file.name, preprocess=False)

        transcript_text = transcription['text']
        logger.info(f"Transcribed: '{transcript_text}'")

        # Step 3: Get conversation history
        logger.info("Step 2/3: Processing with agent...")

        # Load system messages + last 5 messages (same as text chat)
        system_messages = db.query(Conversation)\
            .filter(Conversation.session_id == session_id, Conversation.role == 'system')\
            .order_by(Conversation.created_at.asc())\
            .all()

        recent_messages = db.query(Conversation)\
            .filter(Conversation.session_id == session_id, Conversation.role != 'system')\
            .order_by(Conversation.created_at.desc())\
            .limit(5)\
            .all()

        # Build conversation history
        conversation_history = []
        for msg in system_messages:
            conversation_history.append({"role": msg.role, "message": msg.message})
        for msg in reversed(recent_messages):
            conversation_history.append({"role": msg.role, "message": msg.message})

        # Save user message
        user_msg = Conversation(
            session_id=session_id,
            role="user",
            message=transcript_text
        )
        db.add(user_msg)
        db.commit()

        # Process with agent
        agent = get_agent()
        agent_response = agent.chat(
            message=transcript_text,
            session_id=session_id,
            conversation_history=conversation_history
        )

        response_text = agent_response['response']
        tools_used = agent_response['tools_used']

        logger.info(f"Agent response: {len(response_text)} chars, tools: {tools_used}")

        # Save agent response
        assistant_msg = Conversation(
            session_id=session_id,
            role="assistant",
            message=response_text
        )
        db.add(assistant_msg)
        db.commit()

        # Step 4: Synthesize response to audio (TTS)
        logger.info("Step 3/3: Synthesizing speech...")
        tts = get_tts_service()
        audio_bytes = await tts.synthesize(text=response_text, voice=voice)

        # Encode audio as base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        logger.info(f"Voice chat complete: {len(audio_bytes)} bytes audio")

        return VoiceChatResponse(
            transcript=transcript_text,
            response_text=response_text,
            response_audio_base64=audio_base64,
            tools_used=tools_used,
            session_id=session_id,
            language=transcription['language'],
            confidence=transcription['confidence']
        )

    except Exception as e:
        logger.error(f"Voice chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {str(e)}")

    finally:
        # Cleanup temp file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/voices")
async def list_voices(language: Optional[str] = None):
    """
    Get list of available TTS voices.

    Optionally filter by language code (e.g., 'en-US', 'es-ES').

    Returns list of voices with metadata (name, gender, language, locale).
    """
    try:
        tts = get_tts_service()

        if language:
            import asyncio
            voices = await tts.get_voices_by_language(language)
            logger.info(f"Found {len(voices)} voices for language: {language}")
        else:
            import asyncio
            voices = await tts.get_available_voices()
            logger.info(f"Returning all {len(voices)} voices")

        # Simplify response
        simplified_voices = [
            {
                "id": v['ShortName'],
                "name": v['FriendlyName'],
                "gender": v['Gender'],
                "locale": v['Locale']
            }
            for v in voices
        ]

        return {
            "total": len(simplified_voices),
            "voices": simplified_voices
        }

    except Exception as e:
        logger.error(f"Failed to list voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")
