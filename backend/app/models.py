"""
SQLAlchemy database models for the Voice Assistant.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Note(Base):
    """Model for storing user notes."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)  # For now, single user; multi-user later
    filename = Column(String(255), nullable=False, index=True)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Note(id={self.id}, filename='{self.filename}', title='{self.title}')>"


class Conversation(Base):
    """Model for storing conversation history."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    session_id = Column(String(100), index=True)  # Group messages by session
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Conversation(id={self.id}, role='{self.role}', session='{self.session_id}')>"


class Document(Base):
    """Model for tracking uploaded documents."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # 'pdf', 'txt', etc.
    status = Column(String(50), default="uploaded")  # 'uploaded', 'processed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"
