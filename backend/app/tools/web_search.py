"""
Web Search Tool using DuckDuckGo.
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: str = Field(description="The search query to look up on the web")
    max_results: Optional[int] = Field(
        default=5,
        description="Maximum number of search results to return"
    )


class WebSearchTool(BaseTool):
    """
    Tool for searching the web using DuckDuckGo.

    This tool is useful when you need to:
    - Find current information not in the knowledge base
    - Look up recent events, news, or updates
    - Get real-time data or facts
    - Search for information online
    """

    name: str = "web_search"
    description: str = (
        "Search the web for current information, news, or any topic not in the knowledge base. "
        "Use this when you need up-to-date information or facts from the internet. "
        "Input should be a clear search query."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """
        Execute web search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            Formatted string with search results
        """
        try:
            logger.info(f"Performing web search for: {query}")

            # Initialize DuckDuckGo search
            ddgs = DDGS()

            # Perform search
            results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return f"No search results found for: {query}"

            # Format results
            formatted_results = [f"Web Search Results for: '{query}'\n"]

            for idx, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                snippet = result.get('body', 'No description')
                url = result.get('href', 'No URL')

                formatted_results.append(
                    f"{idx}. {title}\n"
                    f"   {snippet}\n"
                    f"   URL: {url}\n"
                )

            final_result = "\n".join(formatted_results)
            logger.info(f"Found {len(results)} results for query: {query}")

            return final_result

        except Exception as e:
            error_msg = f"Error performing web search: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _arun(self, query: str, max_results: int = 5) -> str:
        """Async version of _run (not implemented, falls back to sync)."""
        return self._run(query, max_results)


def get_web_search_tool() -> WebSearchTool:
    """Factory function to create web search tool instance."""
    return WebSearchTool()
