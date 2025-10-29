"""
Test script to verify query preservation in web search.

This tests that the agent properly preserves:
1. Exact product names (conditioner vs shampoo)
2. Source requirements (brand site, official site)
3. All qualifiers (current, latest, MRP, etc.)
"""
import httpx
import json
import logging

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test queries that previously had issues
TEST_QUERIES = [
    {
        "query": "Go to True frog brand site and get the current MRP of True Frog Every day conditioner",
        "expected_keywords": ["True Frog", "conditioner", "brand site", "official", "MRP"],
        "should_not_contain": ["shampoo"]
    },
    {
        "query": "Go to Nike official site and get the price of Air Max 90",
        "expected_keywords": ["Nike", "official", "site", "Air Max 90", "price"],
        "should_not_contain": []
    }
]

BASE_URL = "http://localhost:8000"

def test_query_preservation():
    """Test that queries are properly preserved when calling web_search tool."""

    print("=" * 80)
    print("QUERY PRESERVATION TEST")
    print("=" * 80)
    print()

    for i, test_case in enumerate(TEST_QUERIES, 1):
        query = test_case["query"]
        expected = test_case["expected_keywords"]
        should_not = test_case["should_not_contain"]

        print(f"Test {i}: {query}")
        print("-" * 80)

        try:
            # Send request to chat endpoint
            response = httpx.post(
                f"{BASE_URL}/api/chat",
                json={"message": query},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            print(f"✅ Response received")
            print(f"Response: {data['response'][:200]}...")
            print()

            # Check tools used
            if "tools_used" in data:
                print(f"🔧 Tools used: {data['tools_used']}")

                if "web_search" in data['tools_used']:
                    print("✅ web_search tool was called")
                else:
                    print("⚠️  web_search tool was NOT called")

            print()
            print("📋 VERIFICATION CHECKLIST:")
            print("   Check the server logs to verify:")
            print(f"   1. Search query contains: {', '.join(expected)}")
            if should_not:
                print(f"   2. Search query does NOT contain: {', '.join(should_not)}")
            print()

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print()
        print("=" * 80)
        print()

def check_server():
    """Check if the server is running."""
    try:
        response = httpx.get(f"{BASE_URL}/", timeout=5.0)
        print(f"✅ Server is running at {BASE_URL}")
        return True
    except Exception as e:
        print(f"❌ Server is not reachable at {BASE_URL}")
        print(f"   Error: {str(e)}")
        print()
        print("Please start the server with:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")
        return False

if __name__ == "__main__":
    print()
    print("🔍 Checking server status...")
    print()

    if check_server():
        print()
        print("🚀 Starting query preservation tests...")
        print()
        test_query_preservation()

        print()
        print("=" * 80)
        print("IMPORTANT: Check the server logs above for the actual search queries!")
        print("Look for lines like:")
        print("   [GEMINI GROUNDED SEARCH] Query: <the actual search query>")
        print()
        print("The query should preserve ALL context from the user's original request.")
        print("=" * 80)
