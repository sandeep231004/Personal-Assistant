"""
Note-Taking Tool for saving user notes to the database and files.
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import logging
from datetime import datetime
from pathlib import Path

from app.database import SessionLocal
from app.models import Note, Conversation
from app.config import get_settings, get_session_context

logger = logging.getLogger(__name__)
settings = get_settings()


class NoteTakingInput(BaseModel):
    """Input schema for note-taking tool."""
    title: str = Field(description="Title or filename for the note")
    content: str = Field(description="The content of the note to save")


class NoteTakingTool(BaseTool):
    """
    Tool for saving notes to the database.

    This tool allows the agent to save information as notes when the user requests it.

    Use this when:
    - User asks to "save this", "remember this", "take a note"
    - User wants to store information for later
    - User explicitly asks to create or write a note
    """

    name: str = "save_note"
    description: str = (
        "Save a note to the database with a title and content. "
        "ONLY use when the user EXPLICITLY asks to 'save a note', 'remember this', "
        "'take a note', or 'write this down'. NOT for searching or retrieving notes. "
        "Input should include a title (filename) and the content to save."
    )
    args_schema: Type[BaseModel] = NoteTakingInput

    def _run(self, title: str, content: str) -> str:
        """
        Save a note to both database and file system.

        Args:
            title: Title/filename for the note
            content: Content of the note

        Returns:
            Confirmation message
        """
        try:
            # Get session context
            session_id = get_session_context()
            logger.info(f"Saving note: {title} (session: {session_id or 'none'})")

            # Create database session
            db = SessionLocal()

            try:
                # Clean filename
                filename = self._sanitize_filename(title)

                # Create user_notes directory if it doesn't exist
                from app.config import BASE_DIR
                notes_dir = Path(BASE_DIR) / "data" / "user_notes"
                notes_dir.mkdir(parents=True, exist_ok=True)

                # Save to file system
                file_path = notes_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {title}\n")
                    f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    if session_id:
                        f.write(f"Session: {session_id}\n")
                    f.write(f"\n{'-' * 50}\n\n")
                    f.write(content)

                logger.info(f"Note saved to file: {file_path}")

                # Create note in database
                note = Note(
                    user_id=1,  # Default user for now
                    filename=filename,
                    title=title,
                    content=content
                )

                db.add(note)
                db.commit()
                db.refresh(note)

                # Add system message to conversation history if session_id provided
                if session_id:
                    system_msg = Conversation(
                        session_id=session_id,
                        role="system",
                        message=f"[SYSTEM] Note saved: '{title}' (File: {filename}). User can retrieve this note anytime."
                    )
                    db.add(system_msg)
                    db.commit()
                    logger.info(f"Added note creation notification to session: {session_id}")

                logger.info(f"Successfully saved note: {filename} (ID: {note.id})")

                return (
                    f"Note saved successfully!\n"
                    f"Title: {title}\n"
                    f"Filename: {filename}\n"
                    f"Location: data/user_notes/{filename}\n"
                    f"Note ID: {note.id}\n"
                    f"You can retrieve this note anytime by asking for '{title}'."
                )

            finally:
                db.close()

        except Exception as e:
            error_msg = f"Error saving note: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"Failed to save note: {str(e)}"

    async def _arun(self, title: str, content: str) -> str:
        """Async version (falls back to sync)."""
        return self._run(title, content)

    def _sanitize_filename(self, title: str) -> str:
        """
        Sanitize title to create a valid filename.

        Args:
            title: Original title

        Returns:
            Sanitized filename
        """
        # Remove invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        filename = title

        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Truncate if too long
        if len(filename) > 100:
            filename = filename[:100]

        # Add timestamp if filename is too generic
        if len(filename) < 3:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"note_{timestamp}"

        # Ensure it has .txt extension
        if not filename.endswith('.txt'):
            filename = f"{filename}.txt"

        return filename


class NoteRetrievalInput(BaseModel):
    """Input schema for note retrieval tool."""
    search_term: str = Field(description="Title, filename, or keyword to search for in notes")


class NoteRetrievalTool(BaseTool):
    """
    Tool for retrieving notes from the database.

    Allows the agent to search and retrieve previously saved notes.
    """

    name: str = "retrieve_note"
    description: str = (
        "Retrieve a previously saved note by searching for its title, filename, or keywords in the content. "
        "ONLY use when the user asks to 'see', 'read', 'find', or 'retrieve' a SPECIFIC NOTE. "
        "NOT for general web searches or document searches. "
        "Use this when the user asks to see, read, or find a note."
    )
    args_schema: Type[BaseModel] = NoteRetrievalInput

    def _run(self, search_term: str) -> str:
        """
        Retrieve notes matching the search term.

        Args:
            search_term: Search query

        Returns:
            Formatted note(s) or error message
        """
        try:
            logger.info(f"Searching for notes: {search_term}")

            db = SessionLocal()

            try:
                # Search in title, filename, and content
                notes = db.query(Note).filter(
                    (Note.title.ilike(f"%{search_term}%")) |
                    (Note.filename.ilike(f"%{search_term}%")) |
                    (Note.content.ilike(f"%{search_term}%"))
                ).order_by(Note.created_at.desc()).all()

                if not notes:
                    return f"No notes found matching '{search_term}'. Try a different search term or ask me to list all notes."

                # Format results
                if len(notes) == 1:
                    note = notes[0]
                    return (
                        f"📝 Note Found:\n\n"
                        f"Title: {note.title}\n"
                        f"Filename: {note.filename}\n"
                        f"Created: {note.created_at}\n"
                        f"\nContent:\n{note.content}"
                    )
                else:
                    result = [f"Found {len(notes)} notes matching '{search_term}':\n"]
                    for idx, note in enumerate(notes[:5], 1):  # Limit to 5 results
                        preview = note.content[:100] + "..." if len(note.content) > 100 else note.content
                        result.append(
                            f"{idx}. {note.title}\n"
                            f"   ID: {note.id} | Created: {note.created_at}\n"
                            f"   Preview: {preview}\n"
                        )

                    if len(notes) > 5:
                        result.append(f"\n... and {len(notes) - 5} more. Try a more specific search.")

                    return "\n".join(result)

            finally:
                db.close()

        except Exception as e:
            error_msg = f"Error retrieving notes: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def _arun(self, search_term: str) -> str:
        """Async version (falls back to sync)."""
        return self._run(search_term)


class NoteEditInput(BaseModel):
    """Input schema for note editing tool."""
    search_term: str = Field(description="Title or filename of the note to edit")
    new_content: str = Field(description="New content to replace the old content, or content to append")
    mode: str = Field(
        default="replace",
        description="Edit mode: 'replace' to replace entire content, 'append' to add to end"
    )


class NoteEditTool(BaseTool):
    """
    Tool for editing existing notes.

    Allows the agent to update or append to previously saved notes.
    """

    name: str = "edit_note"
    description: str = (
        "Edit or update an existing note by searching for its title or filename. "
        "Use this when the user asks to 'edit', 'update', 'modify', 'append to', or 'add to' an existing note "
        "AND the user has provided the NEW content they want to add or replace. "
        "If user hasn't provided the new content yet, use 'retrieve_note' first to show them the current content, "
        "then ask what they want to add/change. "
        "Can either replace the entire content or append new content to existing content. "
        "NOT for creating new notes (use save_note for that)."
    )
    args_schema: Type[BaseModel] = NoteEditInput

    def _run(self, search_term: str, new_content: str, mode: str = "replace") -> str:
        """
        Edit an existing note.

        Args:
            search_term: Title or filename to search for
            new_content: New content
            mode: 'replace' or 'append'

        Returns:
            Confirmation message or error
        """
        try:
            logger.info(f"Editing note: {search_term} (mode: {mode})")

            # Get session context
            session_id = get_session_context()

            db = SessionLocal()

            try:
                # Search for the note
                notes = db.query(Note).filter(
                    (Note.title.ilike(f"%{search_term}%")) |
                    (Note.filename.ilike(f"%{search_term}%"))
                ).order_by(Note.created_at.desc()).all()

                if not notes:
                    return f"No note found matching '{search_term}'. Please check the title and try again."

                if len(notes) > 1:
                    # Multiple matches - list them
                    result = [f"Found {len(notes)} notes matching '{search_term}'. Please be more specific:\n"]
                    for idx, note in enumerate(notes[:5], 1):
                        result.append(f"{idx}. {note.title} (ID: {note.id})")
                    return "\n".join(result)

                # Edit the note
                note = notes[0]
                old_content = note.content

                if mode == "append":
                    note.content = old_content + "\n\n" + new_content
                    action = "appended to"
                else:  # replace
                    note.content = new_content
                    action = "replaced"

                note.updated_at = datetime.now()
                db.commit()

                # Update file system
                from app.config import BASE_DIR
                notes_dir = Path(BASE_DIR) / "data" / "user_notes"
                file_path = notes_dir / note.filename

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {note.title}\n")
                    f.write(f"Created: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Updated: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    if session_id:
                        f.write(f"Session: {session_id}\n")
                    f.write(f"\n{'-' * 50}\n\n")
                    f.write(note.content)

                logger.info(f"Successfully edited note: {note.filename} (ID: {note.id})")

                # Add system message to conversation history
                if session_id:
                    system_msg = Conversation(
                        session_id=session_id,
                        role="system",
                        message=f"[SYSTEM] Note edited: '{note.title}' (content {action})."
                    )
                    db.add(system_msg)
                    db.commit()

                return (
                    f"Note '{note.title}' updated successfully!\n"
                    f"Filename: {note.filename}\n"
                    f"Location: data/user_notes/{note.filename}\n"
                    f"Action: Content {action}\n"
                    f"Note ID: {note.id}"
                )

            finally:
                db.close()

        except Exception as e:
            error_msg = f"Error editing note: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def _arun(self, search_term: str, new_content: str, mode: str = "replace") -> str:
        """Async version (falls back to sync)."""
        return self._run(search_term, new_content, mode)


class NoteListInput(BaseModel):
    """Input schema for note listing tool."""
    query: str = Field(
        default="list",
        description="Optional query to filter notes, or 'list' to show all"
    )


class NoteListTool(BaseTool):
    """
    Tool for listing all available notes.

    Shows all notes with their titles and IDs for easy reference.
    """

    name: str = "list_notes"
    description: str = (
        "List all available notes in the database with their titles, IDs, and creation dates. "
        "Use this when: "
        "(1) User asks 'what notes do I have?', 'show my notes', 'list all notes', "
        "(2) User wants to edit a note but you need to see what notes exist first, "
        "(3) Before editing/appending to a note to verify which note to modify. "
        "This helps identify the correct note before retrieving or editing it."
    )
    args_schema: Type[BaseModel] = NoteListInput

    def _run(self, query: str = "list") -> str:
        """
        List all available notes.

        Args:
            query: Optional filter query

        Returns:
            Formatted list of notes
        """
        try:
            logger.info(f"Listing notes (query: {query})")

            db = SessionLocal()

            try:
                # Get all notes
                notes = db.query(Note).order_by(Note.created_at.desc()).all()

                if not notes:
                    return "No notes found in the database. You can create a new note by asking me to save one."

                # Format results
                result = [f"Available Notes ({len(notes)} total):\n"]

                for idx, note in enumerate(notes, 1):
                    preview = note.content[:60] + "..." if len(note.content) > 60 else note.content
                    result.append(
                        f"{idx}. Title: {note.title}\n"
                        f"   ID: {note.id} | Filename: {note.filename}\n"
                        f"   Created: {note.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                        f"   Preview: {preview}\n"
                    )

                result.append("\nTo view full content of any note, ask me to retrieve it by title or ID.")

                logger.info(f"Listed {len(notes)} notes")
                return "\n".join(result)

            finally:
                db.close()

        except Exception as e:
            error_msg = f"Error listing notes: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def _arun(self, query: str = "list") -> str:
        """Async version (falls back to sync)."""
        return self._run(query)


def get_note_taking_tool() -> NoteTakingTool:
    """Factory function to create note-taking tool instance."""
    return NoteTakingTool()


def get_note_retrieval_tool() -> NoteRetrievalTool:
    """Factory function to create note retrieval tool instance."""
    return NoteRetrievalTool()


def get_note_edit_tool() -> NoteEditTool:
    """Factory function to create note editing tool instance."""
    return NoteEditTool()


def get_note_list_tool() -> NoteListTool:
    """Factory function to create note listing tool instance."""
    return NoteListTool()
