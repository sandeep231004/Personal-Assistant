# Testing All Tools - Complete Guide

## 🎯 Overview

Your agent now has **6 intelligent tools**:

1. **web_search** - Search the web (DuckDuckGo)
2. **rag_search** - Search uploaded documents
3. **save_note** - Save notes to database
4. **retrieve_note** - Retrieve saved notes
5. **execute_command** - Execute safe system commands
6. **get_system_info** - Get system information

The agent automatically selects the right tool based on context!

---

## 🚀 Setup

```bash
# Make sure you're in the backend directory
cd backend

# Start the server
uvicorn app.main:app --reload
```

Open: **http://localhost:8000/docs**

---

## 🧪 Test Each Tool

### 1. Web Search Tool

**Test Query:**
```json
{
  "message": "What's the latest news about artificial intelligence?",
  "session_id": "test"
}
```

**Expected:**
- `tools_used: ["web_search"]`
- Recent web results about AI

**Other test queries:**
- "Search the web for Python 3.13 features"
- "What's the weather like today?"
- "Latest news about SpaceX"

---

### 2. RAG Search Tool

**First, upload a document:**
1. Go to **POST /api/upload-document**
2. Upload a PDF or create a text file with content
3. Wait for "processed" status

**Test Query:**
```json
{
  "message": "What does my document say about [topic]?",
  "session_id": "test"
}
```

**Expected:**
- `tools_used: ["rag_search"]`
- Relevant content from your document

**Other test queries:**
- "Summarize the uploaded document"
- "Search my knowledge base for information about X"
- "What are the key points in the document?"

---
z
### 3. Save Note Tool

**Test Query:**
```json
{
  "message": "Save a note titled 'Meeting Notes' with content: Discussed Q4 goals, budget planning, and team expansion",
  "session_id": "test"
}
```

**Expected:**
- `tools_used: ["save_note"]`
- Confirmation with note ID
- Note saved in database

**Other test queries:**
- "Remember that my favorite color is blue"
- "Take a note: Buy milk and eggs"
- "Save this: Meeting tomorrow at 3 PM"

**Natural variations the agent understands:**
- "Save a note that says..."
- "Remember this information..."
- "Write this down..."
- "Take a note about..."

---

### 4. Retrieve Note Tool

**Test Query:**
```json
{
  "message": "Show me my meeting notes",
  "session_id": "test"
}
```

**Expected:**
- `tools_used: ["retrieve_note"]`
- The note you saved earlier

**Other test queries:**
- "Find notes about meetings"
- "What did I save about budget?"
- "Show all my notes"
- "Read my note about [topic]"

---

### 5. Command Execution Tool

**Test Query:**
```json
{
  "message": "What time is it?",
  "session_id": "test"
}
```

**Expected:**
- `tools_used: ["execute_command"]`
- Current date/time

**Safe Commands Available:**
```json
{
  "message": "List files in current directory",
  "session_id": "test"
}
```

```json
{
  "message": "What's my username?",
  "session_id": "test"
}
```

```json
{
  "message": "Show disk space",
  "session_id": "test"
}
```

**Other test queries:**
- "What's the current directory?"
- "Show me the files here"
- "What's the hostname?"
- "Check my Python version"

**Security:** Only whitelisted commands are allowed. Try asking for something unsafe:
```json
{
  "message": "Delete all files",
  "session_id": "test"
}
```
Expected: Error message listing allowed commands

---

### 6. System Info Tool

**Test Query:**
```json
{
  "message": "What operating system am I using?",
  "session_id": "test"
}
```

**Expected:**
- `tools_used: ["get_system_info"]`
- OS details, Python version, etc.

**Other test queries:**
- "Show system information"
- "What's my Python version?"
- "Where am I? (current directory)"

---

## 🎭 Test Multi-Tool Conversations

The agent can use multiple tools in a conversation!

### Example 1: Search & Save
```json
{
  "message": "Search the web for the latest Python features and save them as a note",
  "session_id": "test"
}
```

**Expected:**
- First uses `web_search` to find info
- Then uses `save_note` to save it

### Example 2: Document Q&A & Note
```json
{
  "message": "What does my document say about X? Save the answer as a note",
  "session_id": "test"
}
```

**Expected:**
- `rag_search` to find answer
- `save_note` to save it

### Example 3: System Check & Note
```json
{
  "message": "Check the current time and save it as a note",
  "session_id": "test"
}
```

**Expected:**
- `execute_command` to get time
- `save_note` to save it

---

## 🧠 Testing Agent Intelligence

The agent should automatically choose the right tool. Test these ambiguous queries:

### 1. Context-Based Selection
```json
{
  "message": "What is machine learning?",
  "session_id": "test"
}
```

**If you have a document about ML:**
- Should use `rag_search` (prefers knowledge base)

**If no relevant document:**
- Should use `web_search`

### 2. Implicit Commands
```json
{
  "message": "Remember that I live in New York",
  "session_id": "test"
}
```
- Should use `save_note` (understands "remember" = save)

### 3. Natural Language
```json
{
  "message": "What's my computer's name?",
  "session_id": "test"
}
```
- Should use `execute_command` with "hostname"

---

## 📊 Verification Checklist

After testing, verify:

- [ ] **Web Search** - Gets current information from internet
- [ ] **RAG Search** - Retrieves info from uploaded documents
- [ ] **Save Note** - Creates notes in database
- [ ] **Retrieve Note** - Finds and displays saved notes
- [ ] **Execute Command** - Runs safe system commands only
- [ ] **System Info** - Returns OS/Python information

**Check the `tools_used` field in each response!**

---

## 🔍 Check Database

View saved notes via API:

**GET /api/notes** - List all notes

**GET /api/notes/{note_id}** - Get specific note

**DELETE /api/notes/{note_id}** - Delete a note

---

## 🎯 Advanced Tests

### Test 1: Tool Chain
Ask the agent to:
1. Search for Python tutorials
2. Save the best result as a note
3. Retrieve the note
4. Check what time it was saved

### Test 2: Mixed Context
Upload a document about Python, then ask:
- "What are the latest Python features?" (should use web for "latest")
- "What does my document say about Python?" (should use RAG)

### Test 3: Error Handling
- Try to save a note with very long title (>200 chars)
- Try to execute an unsafe command
- Search for a note that doesn't exist

---

## 🐛 Troubleshooting

### Agent using wrong tool?
- Check the tool descriptions in code
- Try being more explicit: "Search the web for..." or "In my documents, find..."

### Command execution not working?
- Only whitelisted commands allowed
- Check `ALLOWED_COMMANDS` in `command_execution.py`

### Notes not saving?
- Check database connection
- Look for errors in terminal logs

### RAG not finding anything?
- Make sure you uploaded a document first
- Check if document was processed (status="processed")

---

## 📝 Example Test Session

Here's a complete test flow:

```bash
# 1. Upload a document about Python
POST /api/upload-document
→ Upload python_tutorial.pdf

# 2. Test all tools in order:

# Web search
POST /api/chat
{"message": "Latest Python 3.13 news"}
→ tools_used: ["web_search"]

# RAG search
POST /api/chat
{"message": "What does my document say about functions?"}
→ tools_used: ["rag_search"]

# Save note
POST /api/chat
{"message": "Save a note: Remember to review Python tutorial"}
→ tools_used: ["save_note"]

# Retrieve note
POST /api/chat
{"message": "Show my notes about Python"}
→ tools_used: ["retrieve_note"]

# Command execution
POST /api/chat
{"message": "What time is it?"}
→ tools_used: ["execute_command"]

# System info
POST /api/chat
{"message": "What OS am I on?"}
→ tools_used: ["get_system_info"]
```

---

## ✅ Success Criteria

Your agent is working correctly if:

1. ✅ Each tool is called when appropriate
2. ✅ Agent chooses correct tool based on context
3. ✅ Multi-tool workflows work (search → save, etc.)
4. ✅ Safe commands execute, unsafe ones are rejected
5. ✅ Notes are saved and retrievable
6. ✅ RAG finds relevant info from documents
7. ✅ Web search returns current information

---

## 🎉 Next Steps

Once all tools work:

1. **Add Voice Integration** - STT + TTS
2. **Build Frontend** - React chat interface
3. **Add Authentication** - User management
4. **Deploy** - Host on cloud platform

**Your agent is now a full-featured AI assistant!** 🚀
