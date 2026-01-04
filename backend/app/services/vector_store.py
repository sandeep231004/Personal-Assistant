"""
Vector Store Service for RAG with Advanced Chunking and Re-ranking.

This module handles:
- ChromaDB initialization
- Embeddings generation
- Advanced chunking strategies
- Re-ranking for better retrieval
- Document storage and retrieval
"""
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from typing import List, Optional, Literal
import logging
from pathlib import Path

from app.config import get_settings
from app.services.chunking import ChunkingStrategy
from app.services.reranking import get_reranker

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreService:
    """
    Service for managing the vector store (ChromaDB).

    Handles document ingestion, embedding generation, and similarity search
    with advanced chunking and re-ranking strategies.
    """

    def __init__(
        self,
        chunking_strategy: Literal["recursive", "token", "semantic"] = "recursive",
        enable_reranking: bool = True
    ):
        """
        Initialize vector store with embeddings and ChromaDB.

        Args:
            chunking_strategy: Type of chunking to use
            enable_reranking: Whether to use re-ranking
        """
        logger.info("Initializing Vector Store Service...")

        # Initialize embeddings model
        # This converts text into numerical vectors (embeddings)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU
            encode_kwargs={'normalize_embeddings': True}  # Normalize for cosine similarity
        )

        # Initialize chunking strategy
        self.chunking_strategy = chunking_strategy
        self.chunker = ChunkingStrategy.get_chunker(
            strategy=chunking_strategy,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        # Initialize re-ranker (optional)
        self.reranker = get_reranker(enable=enable_reranking) if enable_reranking else None

        # Initialize ChromaDB
        self.vectorstore = Chroma(
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=settings.CHROMA_DB_PATH
        )

        logger.info(f"Vector store initialized with collection: {settings.CHROMA_COLLECTION_NAME}")
        logger.info(f"Embeddings model: {settings.EMBEDDING_MODEL}")
        logger.info(f"Chunking strategy: {chunking_strategy}")
        logger.info(f"Re-ranking: {'Enabled' if self.reranker else 'Disabled'}")

    def ingest_document(self, file_path: str, file_type: str = "pdf", metadata: dict = None) -> dict:
        """
        Ingest a document into the vector store with optional metadata.

        Args:
            file_path: Path to the document file
            file_type: Type of file ('pdf' or 'txt')
            metadata: Optional dictionary with additional metadata (e.g., session_id)

        Returns:
            Dictionary with ingestion status and details
        """
        try:
            logger.info(f"Ingesting document: {file_path}")
            if metadata:
                logger.info(f"Adding metadata: {metadata}")

            # Load document based on type
            if file_type.lower() == "pdf":
                loader = PyPDFLoader(file_path)
            elif file_type.lower() == "txt":
                loader = TextLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Load the document
            documents = loader.load()

            if not documents:
                return {
                    "status": "error",
                    "message": "No content found in document"
                }

            # Split into chunks using selected strategy
            chunks = self.chunker(documents)

            # Add custom metadata to each chunk if provided
            if metadata:
                for chunk in chunks:
                    # Merge custom metadata with existing metadata
                    chunk.metadata.update(metadata)
                    logger.debug(f"Added metadata to chunk: {chunk.metadata}")

            logger.info(f"Split document into {len(chunks)} chunks using {self.chunking_strategy} strategy")

            # Add to vector store
            self.vectorstore.add_documents(chunks)

            logger.info(f"Successfully ingested document: {Path(file_path).name}")

            return {
                "status": "success",
                "message": f"Document ingested successfully",
                "chunks": len(chunks),
                "filename": Path(file_path).name
            }

        except Exception as e:
            error_msg = f"Error ingesting document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }

    def search(self, query: str, k: int = None, use_reranking: bool = True, filter_metadata: dict = None) -> List[dict]:
        """
        Search the vector store for relevant documents with optional re-ranking and filtering.

        Args:
            query: Search query
            k: Number of final results to return (default from settings)
            use_reranking: Whether to use re-ranking (default True)
            filter_metadata: Optional metadata filter (e.g., {"session_id": "abc123"})

        Returns:
            List of relevant document chunks with metadata
        """
        try:
            if k is None:
                k = settings.TOP_K_RESULTS

            # If re-ranking is enabled, retrieve more candidates first
            retrieval_k = k * 5 if (use_reranking and self.reranker) else k

            logger.info(f"Searching vector store for: {query[:50]}... (k={retrieval_k})")
            if filter_metadata:
                logger.info(f"Applying metadata filter: {filter_metadata}")

            # Perform similarity search with optional filtering
            if filter_metadata:
                results = self.vectorstore.similarity_search_with_score(
                    query,
                    k=retrieval_k,
                    filter=filter_metadata
                )
            else:
                results = self.vectorstore.similarity_search_with_score(query, k=retrieval_k)

            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })

            logger.info(f"Found {len(formatted_results)} relevant chunks from vector search")

            # Apply re-ranking if enabled
            if use_reranking and self.reranker and formatted_results:
                logger.info("Applying re-ranking...")
                formatted_results = self.reranker.rerank(query, formatted_results, top_k=k)
                logger.info(f"Re-ranked to top {len(formatted_results)} results")
            else:
                # Just return top k without re-ranking
                formatted_results = formatted_results[:k]

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}", exc_info=True)
            return []

    def get_retriever(self, k: int = None):
        """
        Get a LangChain retriever for the vector store.

        Args:
            k: Number of documents to retrieve

        Returns:
            LangChain retriever object
        """
        if k is None:
            k = settings.TOP_K_RESULTS

        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    def delete_collection(self):
        """Delete the entire collection (use with caution!)."""
        try:
            self.vectorstore.delete_collection()
            logger.info(f"Deleted collection: {settings.CHROMA_COLLECTION_NAME}")

            # Reinitialize
            self.__init__()

            return {"status": "success", "message": "Collection deleted and reinitialized"}
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_collection_stats(self) -> dict:
        """Get statistics about the vector store collection."""
        try:
            # Get collection
            collection = self.vectorstore._collection

            return {
                "collection_name": settings.CHROMA_COLLECTION_NAME,
                "total_documents": collection.count(),
                "embedding_model": settings.EMBEDDING_MODEL,
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> VectorStoreService:
    """
    Get or create the vector store service instance (singleton).

    Returns:
        VectorStoreService instance
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()

    return _vector_store_instance