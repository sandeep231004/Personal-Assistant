"""
Document Info Tool - Check available documents in the knowledge base.
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import logging
from sqlalchemy import desc

from app.database import SessionLocal
from app.models import Document
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class DocumentInfoInput(BaseModel):
    """Input schema for document info tool."""
    query: str = Field(
        default="list",
        description="Action to perform: 'list' to see all documents, or specific filename to get details"
    )


class DocumentInfoTool(BaseTool):
    """
    Tool for checking what documents are available in the knowledge base.

    This helps the agent understand what documents have been uploaded
    and can be searched using the RAG search tool.
    """

    name: str = "check_available_documents"
    description: str = (
        "Check what documents are currently available in the knowledge base. "
        "Use this when the user asks 'what documents do I have?', 'what files are uploaded?', "
        "'show me my documents', or before performing RAG search to verify documents exist. "
        "Returns list of uploaded documents with their status."
    )
    args_schema: Type[BaseModel] = DocumentInfoInput

    def _run(self, query: str = "list") -> str:
        """
        Get information about available documents.

        Args:
            query: Action or filename to query

        Returns:
            Information about available documents
        """
        try:
            logger.info(f"Checking available documents: {query}")

            # Get database session
            db = SessionLocal()

            try:
                # Get vector store stats
                vector_store = get_vector_store()
                stats = vector_store.get_collection_stats()
                total_chunks = stats.get('total_documents', 0)

                # Get all documents from database
                documents = db.query(Document).order_by(desc(Document.created_at)).all()

                if not documents:
                    return (
                        "No documents have been uploaded to the knowledge base yet. "
                        "You can upload PDF or TXT files to search through them later."
                    )

                # Format document list
                result_lines = [
                    f"Knowledge Base Status:",
                    f"- Total documents: {len(documents)}",
                    f"- Total searchable chunks: {total_chunks}",
                    f"\nUploaded Documents:\n"
                ]

                for idx, doc in enumerate(documents, 1):
                    status_icon = "✓" if doc.status == "processed" else "⏳" if doc.status == "processing" else "✗"
                    result_lines.append(
                        f"{idx}. {status_icon} {doc.filename}\n"
                        f"   Type: {doc.file_type.upper()}\n"
                        f"   Status: {doc.status}\n"
                        f"   Uploaded: {doc.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    )

                result = "\n".join(result_lines)

                # Add helpful message
                if any(doc.status == "processed" for doc in documents):
                    result += "\nYou can ask questions about these documents and I'll search through them for answers."

                logger.info(f"Found {len(documents)} documents in knowledge base")
                return result

            finally:
                db.close()

        except Exception as e:
            error_msg = f"Error checking documents: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def _arun(self, query: str = "list") -> str:
        """Async version (falls back to sync)."""
        return self._run(query)


def get_document_info_tool() -> DocumentInfoTool:
    """Factory function to create document info tool instance."""
    return DocumentInfoTool()
