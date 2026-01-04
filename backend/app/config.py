"""
Configuration settings for the Voice Assistant application.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Context-aware storage for session context (works with LangGraph and async execution)
from contextvars import ContextVar
_session_context: ContextVar[str] = ContextVar('session_context', default=None)


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # App Info
    APP_NAME: str = "Personal Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API Keys
    GEMINI_API_KEY: str = ""  # Main agent/chat API key (set via .env file)
    GEMINI_SEARCH_API_KEY: str = ""  # Separate API key for Gemini web search with Google Search grounding (optional, falls back to GEMINI_API_KEY)
    TAVILY_API_KEY: str = ""  # Tavily API key for real-time web search - 1,000 free searches/month (get from https://tavily.com)

    # Database (Neon PostgreSQL)
    # Must be set in .env file - no default fallback
    DATABASE_URL: str = ""  # Will be loaded from .env

    # ChromaDB (Vector Store)
    CHROMA_DB_PATH: str = str(BASE_DIR / "data" / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "documents"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # LLM Settings
    # Options: "gemini-2.0-flash-exp" (50 req/day) or "gemini-1.5-flash" (1500 req/day free tier)
    LLM_MODEL: str = "gemini-2.5-flash"  # Switched to 1.5 for higher quota
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1024

    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 3

    # Documents
    DOCUMENTS_DIR: str = str(BASE_DIR / "data" / "documents")

    # Voice Settings
    ASR_MODEL: str = "medium"  # Whisper model size
    TTS_MODEL: str = "tts_models/en/ljspeech/glow-tts"
    AUDIO_SAMPLE_RATE: int = 16000

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def set_session_context(session_id: str):
    """Set the current session ID in context-aware storage."""
    _session_context.set(session_id)


def get_session_context() -> str:
    """Get the current session ID from context-aware storage."""
    return _session_context.get()


# Create necessary directories
def create_directories():
    """Create required directories if they don't exist."""
    dirs = [
        BASE_DIR / "data",
        BASE_DIR / "data" / "documents",
        BASE_DIR / "data" / "chroma_db",
        BASE_DIR / "data" / "user_notes",
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
