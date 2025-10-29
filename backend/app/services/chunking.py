"""
Advanced chunking strategies for RAG.

This module provides different text splitting strategies:
1. RecursiveCharacterTextSplitter - Smart hierarchical splitting
2. Semantic Chunking - Split based on meaning/topics
3. Token-based chunking - Split by token count
"""
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    #SemanticTextSplitter,
    TokenTextSplitter,
)
from typing import List, Literal
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """
    Advanced chunking strategies for document processing.

    Why Chunking Matters:
    - LLMs have context limits (can't process entire books)
    - Smaller chunks = more precise retrieval
    - Overlaps preserve context between chunks
    - Different strategies work better for different content types
    """

    @staticmethod
    def recursive_character_split(
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Document]:
        """
        Recursive Character Text Splitter (RECOMMENDED)

        How it works:
        1. Tries to split on double newlines (paragraphs)
        2. If chunk still too big, splits on single newlines (sentences)
        3. If still too big, splits on periods, then spaces
        4. Preserves semantic structure as much as possible

        Why use this:
        - Keeps related content together
        - Respects document structure (paragraphs, sentences)
        - Works well for most document types
        - Good balance of precision and context

        Args:
            documents: List of LangChain documents
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks (preserves context)

        Returns:
            List of chunked documents
        """
        logger.info(f"Using Recursive Character Splitter (size={chunk_size}, overlap={chunk_overlap})")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            # Priority order for splitting
            separators=[
                "\n\n",  # Paragraph breaks (highest priority)
                "\n",    # Line breaks
                ". ",    # Sentences
                "! ",    # Exclamations
                "? ",    # Questions
                "; ",    # Semicolons
                ", ",    # Commas
                " ",     # Spaces
                "",      # Characters (last resort)
            ],
            # Don't split on these (keep together)
            is_separator_regex=False,
        )

        chunks = splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")

        return chunks

    @staticmethod
    def token_based_split(
        documents: List[Document],
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> List[Document]:
        """
        Token-based Text Splitter

        How it works:
        - Splits based on token count (not characters)
        - Tokens are what LLMs actually process
        - More accurate for context window management

        When to use:
        - When you need precise token counts
        - For specific LLM context windows
        - Technical/code documents

        Args:
            documents: List of LangChain documents
            chunk_size: Max tokens per chunk
            chunk_overlap: Overlap in tokens

        Returns:
            List of chunked documents
        """
        logger.info(f"Using Token-based Splitter (size={chunk_size} tokens, overlap={chunk_overlap})")

        splitter = TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        chunks = splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")

        return chunks

    @staticmethod
    def semantic_split(
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Document]:
        """
        Semantic Chunking (Advanced)

        How it works:
        1. Analyzes text semantically (meaning-based)
        2. Groups related sentences together
        3. Splits when topic changes
        4. Uses embeddings to detect topic shifts

        Why it's better:
        - Keeps related ideas together
        - Doesn't break mid-topic
        - Better retrieval accuracy
        - More contextually coherent chunks

        Note: Currently uses RecursiveCharacterTextSplitter as base
        (True semantic splitting requires additional libraries like langchain-experimental)

        Args:
            documents: List of LangChain documents
            chunk_size: Target chunk size
            chunk_overlap: Overlap size

        Returns:
            List of chunked documents
        """
        logger.info("Using Semantic Chunking strategy")

        # For now, use recursive splitter with semantic-friendly settings
        # In future: Can use SemanticChunker from langchain-experimental
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = splitter.split_documents(documents)

        # TODO: Add true semantic chunking using embeddings
        # from langchain_experimental.text_splitter import SemanticChunker
        # This would analyze sentence embeddings and group semantically similar content

        logger.info(f"Created {len(chunks)} semantic chunks")

        return chunks

    @staticmethod
    def get_chunker(
        strategy: Literal["recursive", "token", "semantic"] = "recursive",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Get a chunking function based on strategy.

        Args:
            strategy: Type of chunking ("recursive", "token", "semantic")
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks

        Returns:
            Chunking function
        """
        strategies = {
            "recursive": lambda docs: ChunkingStrategy.recursive_character_split(
                docs, chunk_size, chunk_overlap
            ),
            "token": lambda docs: ChunkingStrategy.token_based_split(
                docs, chunk_size, chunk_overlap
            ),
            "semantic": lambda docs: ChunkingStrategy.semantic_split(
                docs, chunk_size, chunk_overlap
            ),
        }

        return strategies.get(strategy, strategies["recursive"])


# Usage example and explanation
"""
CHUNKING STRATEGIES COMPARISON:

1. RECURSIVE CHARACTER SPLITTER (Default - Best for most cases)
   Pros:
   - Preserves document structure
   - Smart hierarchical splitting
   - Works with all content types
   - Good balance

   Cons:
   - Character-based (not token-aware)
   - May split mid-sentence if forced

   Best for:
   - General documents, PDFs, articles
   - Mixed content types
   - When in doubt, use this!

2. TOKEN-BASED SPLITTER
   Pros:
   - Precise token counting
   - LLM-aware chunking
   - Consistent chunk sizes

   Cons:
   - May break semantic meaning
   - Less natural splits

   Best for:
   - Code documentation
   - Technical content
   - Strict token budgets

3. SEMANTIC CHUNKING (Advanced)
   Pros:
   - Keeps topics together
   - Natural semantic boundaries
   - Best retrieval accuracy

   Cons:
   - More computational overhead
   - Variable chunk sizes
   - Requires embeddings

   Best for:
   - Long-form content
   - Books, research papers
   - When quality > speed

CHUNK SIZE GUIDELINES:

Small chunks (200-500):
- More precise retrieval
- Less context per chunk
- More chunks = slower search
- Good for: FAQs, definitions, facts

Medium chunks (500-1500):
- Balanced approach (RECOMMENDED)
- Good context + precision
- Good for: Most documents

Large chunks (1500-3000):
- More context
- Less precise retrieval
- Fewer chunks = faster search
- Good for: Long explanations, tutorials

OVERLAP IMPORTANCE:

Why overlap matters:
- Prevents losing context at chunk boundaries
- If key info spans chunk border, overlap captures it
- Typical: 10-20% of chunk size

Example with overlap=200, chunk_size=1000:
Chunk 1: [0-1000]
Chunk 2: [800-1800]  <- 200 chars overlap with Chunk 1
Chunk 3: [1600-2600] <- 200 chars overlap with Chunk 2
"""