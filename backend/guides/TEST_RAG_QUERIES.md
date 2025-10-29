# RAG Search Tool - Test Queries

## These queries SHOULD trigger `rag_search`:

### Direct document references:
- ✅ "What does **the document** say about climate change?"
- ✅ "Search **the file** for information on neural networks"
- ✅ "According to **the paper**, what is the conclusion?"
- ✅ "Find information about X in **the PDF**"
- ✅ "What does **the uploaded file** contain?"
- ✅ "Tell me about **the research paper** I uploaded"

### After document upload (with system message):
- ✅ "What does it say about machine learning?" (after seeing system message: "Document uploaded")
- ✅ "Summarize the main points" (after upload)
- ✅ "What are the key findings?" (after upload)
- ✅ "Find information about deep learning" (after upload)

### Explicit document context:
- ✅ "Search my documents for quantum computing"
- ✅ "What information do I have about AI ethics?"
- ✅ "Find references to sustainability in my files"

---

## These queries should NOT trigger `rag_search`:

### General knowledge (should use `general_knowledge_search`):
- ❌ "What is machine learning?" (no document context)
- ❌ "How does photosynthesis work?"
- ❌ "Who invented the telephone?"
- ❌ "Explain quantum mechanics"

### Current/real-time data (should use `realtime_web_search`):
- ❌ "What time is it in Tokyo?"
- ❌ "What's the latest news?"
- ❌ "Current stock price of Apple"
- ❌ "Today's weather"

### System operations (should use `execute_command` or `get_system_info`):
- ❌ "List files in current directory"
- ❌ "What OS am I running?"

---

## Testing Workflow

### Example Test Session:

```python
import requests

BASE_URL = "http://localhost:8000"
session_id = "test_rag_session_001"

# Step 1: Upload document
print("=== STEP 1: Upload Document ===")
with open("ml_paper.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/upload-document",
        files={"file": f},
        params={"session_id": session_id}
    )
    print(response.json())

# Step 2: Query with explicit document reference
print("\n=== STEP 2: Query with 'the document' ===")
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "What does the document say about supervised learning?",
        "session_id": session_id
    }
)
result = response.json()
print(f"Response: {result['response']}")
print(f"Tools used: {result['tools_used']}")
assert "rag_search" in result['tools_used'], "❌ FAILED: Should use rag_search"
print("✅ PASSED: Used rag_search")

# Step 3: Query without explicit reference (context-based)
print("\n=== STEP 3: Query without explicit reference ===")
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "What are the main findings about neural networks?",
        "session_id": session_id
    }
)
result = response.json()
print(f"Response: {result['response']}")
print(f"Tools used: {result['tools_used']}")
assert "rag_search" in result['tools_used'], "❌ FAILED: Should use rag_search (has system message)"
print("✅ PASSED: Used rag_search based on context")

# Step 4: Query with "the file"
print("\n=== STEP 4: Query with 'the file' ===")
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "Summarize the file for me",
        "session_id": session_id
    }
)
result = response.json()
print(f"Response: {result['response']}")
print(f"Tools used: {result['tools_used']}")
assert "rag_search" in result['tools_used'], "❌ FAILED: Should use rag_search"
print("✅ PASSED: Used rag_search")

# Step 5: General knowledge query (should NOT use rag_search)
print("\n=== STEP 5: General knowledge query ===")
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "What is the capital of France?",
        "session_id": session_id
    }
)
result = response.json()
print(f"Response: {result['response']}")
print(f"Tools used: {result['tools_used']}")
assert "rag_search" not in result['tools_used'], "❌ FAILED: Should NOT use rag_search"
assert "general_knowledge_search" in result['tools_used'], "❌ FAILED: Should use general_knowledge_search"
print("✅ PASSED: Correctly used general_knowledge_search, not rag_search")

print("\n=== ALL TESTS PASSED ===")
```

---

## Debugging Tips

### If RAG search is NOT being used:

1. **Check conversation history**:
   ```bash
   curl "http://localhost:8000/api/conversations/{session_id}"
   ```
   Verify system message exists: `[SYSTEM] Document uploaded...`

2. **Check available documents**:
   ```bash
   curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "What documents do I have?", "session_id": "your_session"}'
   ```

3. **Check logs**:
   Look for: `Agent calling tools: ['rag_search']`

4. **Use explicit triggers**:
   Always include "the document", "the file", "the paper" in your query

---

## Expected Tool Selection Matrix

| Query | Expected Tool | Reason |
|-------|--------------|--------|
| "What does the document say about X?" | `rag_search` | Direct document reference |
| "Summarize the file" | `rag_search` | Direct file reference |
| "Find X in my uploaded paper" | `rag_search` | Explicit uploaded document |
| "What's in the PDF?" | `rag_search` | Direct PDF reference |
| "What is quantum physics?" | `general_knowledge_search` | General knowledge, no doc context |
| "What time is it in NYC?" | `realtime_web_search` | Real-time data |
| "What's today's news?" | `realtime_web_search` | Current events |
| "List my files" | `execute_command` | System operation |
| "What documents are available?" | `check_available_documents` | Document inventory |

---

## Common Issues

### Issue: Agent uses `general_knowledge_search` instead of `rag_search`
**Solution**: Use explicit triggers like "the document", "the file", "the paper"

### Issue: Agent says "no documents uploaded"
**Cause**: Upload wasn't linked to session
**Solution**: Include `session_id` parameter in upload request

### Issue: Agent uses wrong tool consistently
**Cause**: Tool descriptions might conflict
**Solution**: Restart the server to reload updated tool descriptions

---

## Quick Test Queries

Copy-paste these into your chat API:

```json
// Should use rag_search
{"message": "What does the document say about AI?", "session_id": "test"}
{"message": "Summarize the uploaded file", "session_id": "test"}
{"message": "Find information about X in the paper", "session_id": "test"}

// Should NOT use rag_search
{"message": "What is artificial intelligence?", "session_id": "test"}
{"message": "What time is it?", "session_id": "test"}
```
