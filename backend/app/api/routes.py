"""
API routes for Voice Assistant.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.database import get_db
from app.models import Note, Conversation, Document
from app.agents.voice_agent import get_agent
from app.services.vector_store import get_vector_store
from app.config import get_settings
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str
    tools_used: Optional[List[str]] = []


class NoteCreate(BaseModel):
    """Request model for creating notes."""
    filename: str
    title: Optional[str] = None
    content: str


class NoteResponse(BaseModel):
    """Response model for notes."""
    id: int
    filename: str
    title: Optional[str]
    content: str
    created_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Chat Endpoints
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint - sends message to the agent.

    The agent will automatically:
    - Understand user intent
    - Select appropriate tools (RAG, web search, notes, commands)
    - Execute actions
    - Return response
    """
    try:
        logger.info(f"Received message: {request.message}")

        # Load conversation history: ALL system messages + last 5 user/assistant messages
        # System messages (document uploads, note creation) should ALWAYS be included
        system_messages = db.query(Conversation)\
            .filter(Conversation.session_id == request.session_id, Conversation.role == 'system')\
            .order_by(Conversation.created_at.asc())\
            .all()

        # Get last 5 non-system messages (user/assistant)
        recent_messages = db.query(Conversation)\
            .filter(Conversation.session_id == request.session_id, Conversation.role != 'system')\
            .order_by(Conversation.created_at.desc())\
            .limit(5)\
            .all()

        # Combine: system messages first, then recent messages in chronological order
        conversation_history = []

        # Add all system messages first (chronological order)
        for msg in system_messages:
            conversation_history.append({"role": msg.role, "message": msg.message})

        # Add recent user/assistant messages (chronological order)
        for msg in reversed(recent_messages):
            conversation_history.append({"role": msg.role, "message": msg.message})

        # Save user message to conversation history
        user_msg = Conversation(
            session_id=request.session_id,
            role="user",
            message=request.message
        )
        db.add(user_msg)
        db.commit()  # Commit immediately so it's available for next query
        logger.info(f"💾 Saved user message to database (session: {request.session_id})")

        # Get agent and process message with conversation history
        agent = get_agent()
        agent_response = agent.chat(
            message=request.message,
            session_id=request.session_id,
            conversation_history=conversation_history
        )

        response_text = agent_response["response"]
        tools_used = agent_response["tools_used"]

        # Save assistant message
        assistant_msg = Conversation(
            session_id=request.session_id,
            role="assistant",
            message=response_text
        )
        db.add(assistant_msg)
        db.commit()

        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            tools_used=tools_used
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Notes Endpoints
# ============================================================================

@router.post("/notes", response_model=NoteResponse)
async def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note."""
    try:
        db_note = Note(
            filename=note.filename,
            title=note.title or note.filename,
            content=note.content
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)

        logger.info(f"Created note: {note.filename}")

        return NoteResponse(
            id=db_note.id,
            filename=db_note.filename,
            title=db_note.title,
            content=db_note.content,
            created_at=str(db_note.created_at)
        )
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes", response_model=List[NoteResponse])
async def get_notes(db: Session = Depends(get_db)):
    """Get all notes."""
    try:
        notes = db.query(Note).order_by(Note.created_at.desc()).all()
        return [
            NoteResponse(
                id=note.id,
                filename=note.filename,
                title=note.title,
                content=note.content,
                created_at=str(note.created_at)
            )
            for note in notes
        ]
    except Exception as e:
        logger.error(f"Error fetching notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific note by ID."""
    try:
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        return NoteResponse(
            id=note.id,
            filename=note.filename,
            title=note.title,
            content=note.content,
            created_at=str(note.created_at)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    try:
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        db.delete(note)
        db.commit()

        logger.info(f"Deleted note: {note.filename}")
        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Document Upload Endpoint (for RAG)
# ============================================================================

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload a document for RAG processing.
    Supports: PDF, TXT files.

    Process:
    1. Validate file type
    2. Save file to documents folder
    3. Ingest into ChromaDB vector store
    4. Track in database
    5. Add system message to conversation history (if session_id provided)

    Args:
        file: Document file to upload
        session_id: Optional session ID to track upload in conversation history
    """
    try:
        # Validate file type
        allowed_types = [".pdf", ".txt"]
        file_ext = "." + file.filename.split(".")[-1].lower()

        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {allowed_types}"
            )

        # Create documents directory if it doesn't exist
        docs_dir = Path(settings.DOCUMENTS_DIR)
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = docs_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved file to: {file_path}")

        # Track in database (mark as processing)
        db_doc = Document(
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_ext.replace(".", ""),
            status="processing"
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        # Ingest into vector store with session metadata
        vector_store = get_vector_store()
        ingestion_result = vector_store.ingest_document(
            file_path=str(file_path),
            file_type=file_ext.replace(".", ""),
            metadata={"session_id": session_id} if session_id else {}
        )

        # Update document status
        if ingestion_result["status"] == "success":
            db_doc.status = "processed"
            logger.info(f"Successfully ingested document: {file.filename}")
            message = f"Document processed and added to knowledge base ({ingestion_result['chunks']} chunks created)"
        else:
            db_doc.status = "failed"
            logger.error(f"Failed to ingest document: {ingestion_result['message']}")
            message = f"Document uploaded but processing failed: {ingestion_result['message']}"

        db.commit()

        # Add system message to conversation history if session_id provided
        if session_id and ingestion_result["status"] == "success":
            system_msg = Conversation(
                session_id=session_id,
                role="system",
                message=f"[SYSTEM] Document uploaded: '{file.filename}' ({ingestion_result['chunks']} chunks). User can now ask questions about this document."
            )
            db.add(system_msg)
            db.commit()
            logger.info(f"Added document upload notification to session: {session_id}")

        return {
            "message": message,
            "filename": file.filename,
            "status": db_doc.status,
            "document_id": db_doc.id,
            "details": ingestion_result,
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        # Update status if doc was created
        try:
            if 'db_doc' in locals():
                db_doc.status = "failed"
                db.commit()
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Conversation History
# ============================================================================

@router.get("/conversations/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get conversation history for a session."""
    try:
        messages = db.query(Conversation)\
            .filter(Conversation.session_id == session_id)\
            .order_by(Conversation.created_at.desc())\
            .limit(limit)\
            .all()

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg.role,
                    "message": msg.message,
                    "timestamp": str(msg.created_at)
                }
                for msg in reversed(messages)  # Reverse to get chronological order
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
