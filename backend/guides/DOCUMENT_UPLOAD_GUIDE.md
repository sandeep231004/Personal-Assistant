# Document Upload & Query Guide

## How to Upload Documents and Ask Questions in the Same Session

### Overview
To maintain document context throughout a session, you must provide a `session_id` when uploading documents. This allows the agent to be aware of uploaded documents when you ask questions later.

---

## Step-by-Step Workflow

### 1. **Upload a Document with Session ID**

**Endpoint**: `POST /api/upload-document`

**Parameters**:
- `file`: The document file (PDF or TXT)
- `session_id`: (Optional but recommended) Session identifier

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/api/upload-document?session_id=my_session_123" \
  -F "file=@research_paper.pdf"
```

**Example using Python**:
```python
import requests

session_id = "my_session_123"

with open("research_paper.pdf", "rb") as f:
    files = {"file": f}
    params = {"session_id": session_id}
    response = requests.post(
        "http://localhost:8000/api/upload-document",
        files=files,
        params=params
    )
    print(response.json())
```

**Response**:
```json
{
  "message": "Document processed and added to knowledge base (45 chunks created)",
  "filename": "research_paper.pdf",
  "status": "processed",
  "document_id": 1,
  "session_id": "my_session_123",
  "details": {
    "status": "success",
    "chunks": 45,
    "filename": "research_paper.pdf"
  }
}
```

### 2. **Ask Questions in the Same Session**

**Endpoint**: `POST /api/chat`

**Request Body**:
```json
{
  "message": "What does the research paper say about climate change?",
  "session_id": "my_session_123"
}
```

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does the research paper say about climate change?",
    "session_id": "my_session_123"
  }'
```

**Example using Python**:
```python
import requests

session_id = "my_session_123"

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "What does the research paper say about climate change?",
        "session_id": session_id
    }
)
print(response.json())
```

**Response**:
```json
{
  "response": "According to the uploaded research paper, climate change is primarily driven by...",
  "session_id": "my_session_123",
  "tools_used": ["rag_search"]
}
```

---

## How It Works

### Behind the Scenes:

1. **Document Upload**:
   - File is saved to `data/documents/`
   - Document is processed and split into chunks
   - Chunks are embedded and stored in ChromaDB
   - **System message is added to conversation history**:
     ```
     [SYSTEM] Document uploaded: 'research_paper.pdf' (45 chunks).
     User can now ask questions about this document.
     ```

2. **Chat Query**:
   - System loads last 5 messages from conversation history (including system messages)
   - Agent sees: "Document uploaded: research_paper.pdf"
   - Agent knows documents are available
   - Agent uses `rag_search` tool to find relevant information
   - Agent returns answer with sources

3. **Session Persistence**:
   - All messages (user, assistant, system) are stored with `session_id`
   - New session = fresh start
   - Same session = maintains full context

---

## Important Notes

### ✅ **Best Practices**:
- Always use the **same session_id** for uploads and queries
- Use descriptive session IDs (e.g., `user123_research_2024`)
- Upload documents **before** asking questions about them
- One session per conversation/topic

### ⚠️ **Common Mistakes**:
- Uploading without `session_id` → Agent won't know about the upload in chat
- Using different session IDs → Conversation context is lost
- Asking questions immediately after upload without waiting → File might still be processing

### 📊 **Checking Available Documents**:
You can ask the agent: "What documents do I have?" and it will use the `check_available_documents` tool to show all uploaded files.

---

## Example: Complete Workflow

```python
import requests

BASE_URL = "http://localhost:8000"
session_id = "demo_session_001"

# Step 1: Upload a document
print("Step 1: Uploading document...")
with open("ml_textbook.pdf", "rb") as f:
    upload_response = requests.post(
        f"{BASE_URL}/api/upload-document",
        files={"file": f},
        params={"session_id": session_id}
    )
print(upload_response.json())

# Step 2: Ask about the document
print("\nStep 2: Asking question...")
chat_response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "What is the definition of supervised learning in the textbook?",
        "session_id": session_id
    }
)
print(chat_response.json())

# Step 3: Follow-up question (maintains context)
print("\nStep 3: Follow-up question...")
followup_response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "Can you give me an example from the book?",
        "session_id": session_id
    }
)
print(followup_response.json())

# Step 4: Check what documents are available
print("\nStep 4: Checking available documents...")
check_response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "What documents do I have uploaded?",
        "session_id": session_id
    }
)
print(check_response.json())
```

---

## Troubleshooting

### Problem: "Knowledge base is empty"
**Solution**: Make sure you uploaded the document with the same `session_id` you're using for chat.

### Problem: Agent says "Please upload documents"
**Causes**:
1. Document upload failed (check upload response status)
2. Different session_id used for upload vs chat
3. Document is still processing (wait a few seconds)

### Problem: Agent doesn't mention the uploaded document
**Solution**: The system message was added in the last update. Make sure you're using the latest code and uploading with `session_id` parameter.

---

## API Reference

### Upload Document
```
POST /api/upload-document?session_id={session_id}
Content-Type: multipart/form-data

Parameters:
  - file (required): Document file (PDF/TXT)
  - session_id (optional): Session identifier for context tracking
```

### Chat
```
POST /api/chat
Content-Type: application/json

Body:
{
  "message": "Your question",
  "session_id": "your_session_id"  // Optional, defaults to "default"
}
```

### Get Conversation History
```
GET /api/conversations/{session_id}?limit=50
```
