"""
Gemini 2.5 Flash Web Search Tool with Google Search Grounding.

Uses Gemini 2.5 Flash model with Google Search grounding enabled
for real-time web search capabilities.
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any
import logging
from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: str = Field(description="The search query or question requiring current/real-time information from the web")


class GeminiWebSearchTool(BaseTool):
    """
    Universal web search tool using Gemini with Google Search grounding.

    This tool performs REAL web searches using Google Search grounding
    to answer ANY web-related queries with current, accurate information.

    Use this for ALL web searches including:
    - Current time and date (in any location)
    - Recent news and current events
    - Latest information and developments
    - Facts, definitions, and explanations
    - Research topics and general knowledge
    - Live data (weather, sports, stocks, etc.)
    """

    name: str = "web_search"
    description: str = (
        "Search the web for ANY information using Google Search grounding. "
        "This tool performs REAL web searches with Google and provides current, accurate, up-to-date information. "
        "\n\n**CRITICAL - QUERY FORMULATION RULES:**\n"
        "- PRESERVE ALL details from user's query - do NOT simplify, paraphrase, or drop context\n"
        "- MAINTAIN exact product names, versions, specifications, and requirements\n"
        "- INCLUDE source requirements: if user says 'official site', 'brand website', 'go to X site' - add that to search\n"
        "- KEEP all qualifiers: 'current', 'latest', 'today', specific locations, etc.\n"
        "- Examples of CORRECT query preservation:\n"
        "  ✓ User: 'Go to Nike official site for shoe price' → Search: 'Nike official website shoe price'\n"
        "  ✓ User: 'Find MRP of Product X conditioner on brand site' → Search: 'Product X official brand site conditioner MRP'\n"
        "  ✗ WRONG: User mentions 'conditioner' → You search 'shampoo' (NEVER change product names!)\n"
        "  ✗ WRONG: User says 'brand site' → You search generic price (NEVER drop source requirements!)\n"
        "\n**Use this for:** current time/date, weather conditions, news, facts, definitions, product prices, company info, "
        "official websites, specific site information, research topics, 'what is X', 'how does Y work', 'latest Z'.\n"
        "\n**DO NOT use for:** uploaded documents (use rag_search), local files, or saved notes."
    )
    args_schema: Type[BaseModel] = WebSearchInput
    client: Any = Field(default=None, exclude=True)  # Pydantic field for Gemini client
    model: str = Field(default="gemini-2.5-flash", exclude=True)  # Model name

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        """Initialize the Gemini client with Google Search grounding."""
        super().__init__(**kwargs)

        # Use separate API key if available, otherwise fall back to main key
        api_key = settings.GEMINI_SEARCH_API_KEY or settings.GEMINI_API_KEY

        # Initialize Gemini client with the new SDK
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"  # Model name as string

        logger.info("Initialized Gemini Web Search tool with Google Search grounding enabled")

    def _run(self, query: str) -> str:
        """
        Execute web search using Gemini with Google Search grounding.

        Args:
            query: Search query or question

        Returns:
            Response with current/real-time information from the web
        """
        try:
            logger.info(f"[GEMINI GROUNDED SEARCH] Query: {query}")

            # Generate response with Google Search grounding using official SDK format
            response = self.client.models.generate_content(
                model=self.model,
                contents=query,  # Use query directly as per official docs
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for factual accuracy
                    tools=[types.Tool(google_search=types.GoogleSearch())]  # Enable Google Search grounding
                )
            )

            result = response.text.strip()

            logger.info(f"[GEMINI GROUNDED SEARCH] Result: {result[:200]}...")

            # CRITICAL: Check if grounding actually happened (in candidates[0].grounding_metadata)
            metadata = None
            if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata

            if metadata:
                # Log web search queries executed
                if hasattr(metadata, 'web_search_queries') and metadata.web_search_queries:
                    logger.info(f"[GEMINI GROUNDED SEARCH] ✅ GROUNDING ACTIVE - Search queries: {metadata.web_search_queries}")

                # Log grounding chunks (sources)
                if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                    source_count = len(metadata.grounding_chunks)
                    logger.info(f"[GEMINI GROUNDED SEARCH] ✅ GROUNDING ACTIVE - Found {source_count} web sources")
                    # Log first few sources
                    for i, chunk in enumerate(metadata.grounding_chunks[:3]):
                        if hasattr(chunk, 'web') and chunk.web:
                            uri = chunk.web.uri if hasattr(chunk.web, 'uri') else 'unknown'
                            title = chunk.web.title if hasattr(chunk.web, 'title') else 'N/A'
                            logger.info(f"[GEMINI GROUNDED SEARCH]   Source {i+1}: {title} - {uri}")
            else:
                logger.warning(f"[GEMINI GROUNDED SEARCH] ⚠️ NO GROUNDING METADATA - Model may have used internal knowledge instead of web search!")

            return result

        except Exception as e:
            error_msg = f"Error performing grounded web search: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"I encountered an error while searching the web: {str(e)}"

    async def _arun(self, query: str) -> str:
        """Async version of _run (falls back to sync for now)."""
        return self._run(query)


def get_gemini_web_search_tool() -> GeminiWebSearchTool:
    """Factory function to create Gemini web search tool instance."""
    return GeminiWebSearchTool()
