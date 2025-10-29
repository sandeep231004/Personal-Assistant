"""
Simple test script to verify the agent is working.

Run this after setup to test the agent without starting the server.
"""
import os
from dotenv import load_dotenv
from app.agents.voice_agent import get_agent
from app.config import create_directories
from app.database import init_db

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("GEMINI_API_KEY"):
    print("❌ GEMINI_API_KEY not found in .env file!")
    print("Please add your API key to the .env file.")
    exit(1)

print("🚀 Initializing Voice Assistant...\n")

# Create directories and database
create_directories()
init_db()

# Get agent instance
agent = get_agent()

print("✅ Agent initialized successfully!\n")
print("=" * 60)
print("Testing Web Search Tool")
print("=" * 60)

# Test 1: Web search
test_message = "What's the latest news about OpenAI?"
print(f"\n👤 User: {test_message}\n")

response = agent.chat(test_message, session_id="test")

print(f"🤖 Assistant: {response['response']}\n")
print(f"🔧 Tools used: {response['tools_used']}\n")

print("=" * 60)
print("Testing General Conversation")
print("=" * 60)

# Test 2: General conversation (no tools)
test_message_2 = "Hello! How are you?"
print(f"\n👤 User: {test_message_2}\n")

response_2 = agent.chat(test_message_2, session_id="test")

print(f"🤖 Assistant: {response_2['response']}\n")
print(f"🔧 Tools used: {response_2['tools_used']}\n")

print("=" * 60)
print("✅ All tests completed!")
print("=" * 60)
print("\nNext steps:")
print("1. Run the server: uvicorn app.main:app --reload")
print("2. Visit http://localhost:8000/docs to test via API")
print("3. Try different queries to see the agent in action!")
