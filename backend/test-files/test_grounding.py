"""
Test Google Search Grounding with Gemini API.
This script verifies that grounding is actually working.
"""
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_grounding():
    """Test Google Search grounding with a time-sensitive query."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file")
        return

    print("=" * 60)
    print("Testing Gemini Google Search Grounding")
    print("=" * 60)

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Test query - should require web search for current info
    query = "Go to True frog brand site and get the current MRP of True Frog Deep Conditioning Mask and Everyday conditioner"

    print(f"\n📝 Query: {query}")
    print("\n⏳ Sending request with Google Search grounding enabled...")

    try:
        # Generate response with Google Search grounding
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        # DEBUG: Print entire response object structure
        print("\n" + "=" * 60)
        print("DEBUG - RESPONSE OBJECT INSPECTION:")
        print("=" * 60)
        print(f"Response type: {type(response)}")
        print(f"Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        print()

        # Try to access different attributes
        print("Checking various attributes:")
        for attr in ['grounding_metadata', 'candidates', 'metadata', 'usage_metadata', 'prompt_feedback']:
            if hasattr(response, attr):
                val = getattr(response, attr)
                print(f"  ✓ {attr}: {type(val)} = {val}")
            else:
                print(f"  ✗ {attr}: NOT FOUND")
        print()

        # Print response
        print("\n" + "=" * 60)
        print("RESPONSE TEXT:")
        print("=" * 60)
        print(response.text)
        print("=" * 60)

        # Check for grounding metadata
        print("\n" + "=" * 60)
        print("GROUNDING VERIFICATION:")
        print("=" * 60)

        # CORRECT: Check candidates[0].grounding_metadata (not response.grounding_metadata)
        metadata = None
        if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata

        if metadata:
            print(f"✅ GROUNDING IS WORKING!")
            print(f"   Found grounding metadata in candidates[0]")
            print()

            # Web search queries
            if hasattr(metadata, 'web_search_queries') and metadata.web_search_queries:
                print(f"🔍 Search Queries Executed: {metadata.web_search_queries}")
                print()

            # Grounding chunks (sources)
            if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                print(f"📚 Number of Web Sources: {len(metadata.grounding_chunks)}")
                print("\n📖 Sources:")
                for i, chunk in enumerate(metadata.grounding_chunks[:5], 1):
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri if hasattr(chunk.web, 'uri') else 'N/A'
                        title = chunk.web.title if hasattr(chunk.web, 'title') else 'N/A'
                        print(f"  {i}. {title}")
                        print(f"     {uri}")
                print()

            # Search entry point (optional UI widget)
            if hasattr(metadata, 'search_entry_point') and metadata.search_entry_point:
                print("🔗 Search Entry Point: Available (for UI rendering)")
                print()

            # Full metadata
            print("🔬 Full Grounding Metadata:")
            print(metadata)

        else:
            print("⚠️ WARNING: NO GROUNDING METADATA FOUND!")
            print("The model may have answered from internal knowledge without searching the web.")
            print()
            print("Possible reasons:")
            print("  1. Grounding is not enabled properly")
            print("  2. Model decided web search wasn't needed for this query")
            print("  3. API configuration issue")

        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_grounding()
