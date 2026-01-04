"""
Main FastAPI application for Voice Assistant.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings, create_directories
from app.database import init_db
from app.api import routes
from app.api.voice_routes import router as voice_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Voice Assistant Backend...")
    create_directories()
    init_db()
    logger.info("✅ Application startup complete!")

    yield

    # Shutdown
    logger.info("👋 Shutting down Voice Assistant Backend...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered voice assistant with RAG capabilities",
    lifespan=lifespan
)

# CORS middleware for frontend integration (later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(routes.router, prefix="/api")
app.include_router(voice_router)  # Voice routes already have /api prefix


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "message": "Voice Assistant API is running! Visit /docs for API documentation."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "services": ["agent", "rag", "web_search", "notes", "speech_to_text", "text_to_speech", "voice_chat"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
