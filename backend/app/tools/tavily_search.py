"""
Tavily Search Tool - Real web search designed for AI agents.

Tavily provides real-time web search optimized for LLM consumption.
Free tier: 1,000 searches/month
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import httpx
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TavilySearchInput(BaseModel):
    """Input schema for Tavily search tool."""
    query: str = Field(description="The search query to look up on the web")


class TavilySearchTool(BaseTool):
    """
    Real web search tool using Tavily API.

    Tavily is designed specifically for AI agents and provides:
    - Real-time web search
    - Synthesized, relevant results
    - Optimized for LLM consumption
    - Source citations

    Free tier: 1,000 searches/month

    Use this when:
    - User needs current, real-time information
    - User asks about news, recent events
    - User wants factual, up-to-date data
    """

    name: str = "realtime_web_search"
    description: str = (
        "Search the web for CURRENT, REAL-TIME, and LIVE information using Tavily API. "
        "ONLY use this for: current time/date in ANY location, today's news, recent events (last days/weeks), "
        "live data (stock prices, sports scores), current weather conditions, breaking news. "
        "This tool performs ACTUAL web searches and returns UP-TO-DATE information. "
        "DO NOT use for: general knowledge, historical facts, definitions, explanations, "
        "questions about uploaded PDF/TXT documents, local file operations, or saved notes. "
        "If user mentions 'the document' or 'the file', use rag_search instead."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    def _run(self, query: str) -> str:
        """
        Execute real-time web search using Tavily.

        Args:
            query: Search query

        Returns:
            Synthesized search results with sources
        """
        try:
            logger.info(f"Performing Tavily web search for: {query}")

            # Tavily API endpoint
            url = "https://api.tavily.com/search"

            # Request payload
            payload = {
                "api_key": settings.TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",  # or "advanced" for more thorough search
                "include_answer": True,   # Get AI-generated answer
                "include_raw_content": False,
                "max_results": 5
            }

            # Make request
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            # Extract results
            if "answer" in data and data["answer"]:
                # Tavily provides a synthesized answer
                result = data["answer"]

                # Add sources if available
                if "results" in data and data["results"]:
                    sources = []
                    for idx, item in enumerate(data["results"][:3], 1):
                        title = item.get("title", "Unknown")
                        url = item.get("url", "")
                        sources.append(f"{idx}. {title}\n   {url}")

                    if sources:
                        result += "\n\n📚 Sources:\n" + "\n".join(sources)

            elif "results" in data and data["results"]:
                # Fallback: format raw results
                result = f"Web search results for: {query}\n\n"
                for idx, item in enumerate(data["results"], 1):
                    title = item.get("title", "No title")
                    content = item.get("content", "No description")
                    url = item.get("url", "")
                    result += f"{idx}. {title}\n{content}\n{url}\n\n"
            else:
                result = f"No search results found for: {query}"

            logger.info(f"Successfully retrieved Tavily search results for: {query}")
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                error_msg = "Tavily API key is invalid or missing. Please check TAVILY_API_KEY in .env file."
            elif e.response.status_code == 429:
                error_msg = "Tavily API rate limit exceeded. Free tier: 1,000 searches/month."
            else:
                error_msg = f"Tavily API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            return f"❌ {error_msg}"

        except httpx.TimeoutException:
            error_msg = "Tavily search timed out. Please try again."
            logger.error(error_msg)
            return f"❌ {error_msg}"

        except Exception as e:
            error_msg = f"Error performing Tavily search: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"

    async def _arun(self, query: str) -> str:
        """Async version (falls back to sync)."""
        return self._run(query)


def get_tavily_search_tool() -> TavilySearchTool:
    """Factory function to create Tavily search tool instance."""
    return TavilySearchTool()
