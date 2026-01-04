"""
RAG Search Tool for querying the knowledge base.
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import logging

from app.services.vector_store import get_vector_store
from app.config import get_session_context

logger = logging.getLogger(__name__)


class RAGSearchInput(BaseModel):
    """Input schema for RAG search tool."""
    query: str = Field(description="The question or query to search in the knowledge base")
    k: Optional[int] = Field(
        default=3,
        description="Number of relevant documents to retrieve"
    )


class RAGSearchTool(BaseTool):
    """
    Tool for searching the knowledge base using RAG (Retrieval Augmented Generation).

    This tool searches through uploaded documents in the vector database
    and returns relevant information to answer user queries.

    Use this when:
    - User asks about information in uploaded documents
    - User wants to query the knowledge base
    - User asks questions that might be answered by stored documents
    """

    name: str = "rag_search"
    description: str = (
        "Search the knowledge base of uploaded documents (PDFs, TXTs) for specific information. "
        "Use this tool when: "
        "(1) System prompt indicates documents were uploaded in this session, "
        "(2) User asks questions about any topic that COULD be in uploaded documents, "
        "(3) User mentions 'the document', 'the file', 'the paper', 'the PDF', "
        "(4) User asks 'what is X?', 'explain Y', 'tell me about Z', 'summarize', 'key points', 'findings', "
        "(5) Any question that might be answered by document content. "
        "When documents are uploaded, check this FIRST before using web search or general knowledge. "
        "This searches actual uploaded files, NOT the internet. "
        "Skip only for: current time, weather, news, or topics completely unrelated to documents."
    )
    args_schema: Type[BaseModel] = RAGSearchInput

    def _run(self, query: str, k: int = 3) -> str:
        """
        Execute RAG search.

        Args:
            query: Search query/question
            k: Number of relevant chunks to retrieve

        Returns:
            Formatted string with relevant information from documents
        """
        try:
            logger.info(f"Performing RAG search for: {query}")

            # Get vector store instance
            vector_store = get_vector_store()

            # Check if there are any documents in the knowledge base
            stats = vector_store.get_collection_stats()
            total_docs = stats.get('total_documents', 0)

            if total_docs == 0:
                return (
                    "The knowledge base is currently empty. No documents have been uploaded yet. "
                    "Please upload documents using the /api/upload-document endpoint before querying."
                )

            logger.info(f"Knowledge base has {total_docs} document chunks available")

            # Get session context to filter documents from current session
            session_id = get_session_context()
            logger.info(f"[RAG DEBUG] Session context retrieved: {session_id if session_id else 'None (no filtering)'}")
            filter_metadata = {"session_id": session_id} if session_id else None

            if filter_metadata:
                logger.info(f"[RAG FILTER] Filtering search results to session: {session_id}")

            # Search for relevant documents with optional session filter
            results = vector_store.search(query, k=k, filter_metadata=filter_metadata)

            if not results:
                return (
                    f"I searched through {total_docs} document chunks in the knowledge base, "
                    f"but couldn't find information relevant to '{query}'. "
                    f"Try rephrasing your question or asking about different topics covered in the uploaded documents."
                )

            # Format results with source tracking
            formatted_results = [f"Found {len(results)} relevant results in the knowledge base:\n"]
            sources_found = set()  # Track which documents the results came from

            for idx, result in enumerate(results, 1):
                content = result['content']
                metadata = result['metadata']
                score = result['similarity_score']

                # Extract metadata
                source = metadata.get('source', 'Unknown')
                page = metadata.get('page', 'N/A')
                sources_found.add(source)

                formatted_results.append(
                    f"\n--- Result {idx} (Relevance: {score:.2f}) ---\n"
                    f"Source: {source} (Page {page})\n"
                    f"Content: {content}\n"
                )

            # Add summary of which documents were searched
            if sources_found:
                sources_list = "', '".join([s.split('/')[-1] if '/' in s else s for s in sources_found])
                formatted_results.insert(1, f"\nSearch results from document(s): '{sources_list}'\n")

            final_result = "\n".join(formatted_results)
            logger.info(f"Found {len(results)} relevant chunks from {len(sources_found)} document(s): {sources_found}")

            return final_result

        except Exception as e:
            error_msg = f"Error performing RAG search: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def _arun(self, query: str, k: int = 3) -> str:
        """Async version of _run (falls back to sync)."""
        return self._run(query, k)


def get_rag_search_tool() -> RAGSearchTool:
    """Factory function to create RAG search tool instance."""
    return RAGSearchTool()