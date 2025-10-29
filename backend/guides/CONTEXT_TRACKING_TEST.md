# Context Tracking Test Guide

## Overview
This document contains test scenarios to verify that the agent maintains context about files, directories, documents, and notes mentioned throughout a conversation session.

---

## 🎯 What Was Improved

### **Enhanced System Prompt with:**
1. **Explicit Contextual Reference Tracking** - Agent now actively looks back at conversation history
2. **Concrete Examples** - Shows agent exactly how to handle pronouns and vague references
3. **System Message Awareness** - Agent checks system messages for uploads, note creation, file operations
4. **Clarification Instructions** - Agent will ask for clarification instead of guessing

### **Key Features:**
- Tracks "it", "that", "this", "those" references
- Remembers last mentioned documents, notes, files, folders
- Cross-references system messages in conversation history
- Maintains context across multi-turn conversations

---

## 🧪 Test Scenarios

### **Scenario 1: Document Upload Context**

**Test Flow:**
```
1. User: "Upload this AI research paper"
   → Upload document: "AI_Research_2025.pdf"
   → System adds message: "[SYSTEM] Document uploaded: 'AI_Research_2025.pdf'"

2. User: "What does it say about transformers?"
   → Expected: Agent recognizes "it" = "AI_Research_2025.pdf"
   → Agent uses rag_search on that specific document
   → Response: Information about transformers from the paper

3. User: "Summarize that document"
   → Expected: Agent recognizes "that document" = "AI_Research_2025.pdf"
   → Agent provides summary of the same document
```

**What to Verify:**
- ✅ Agent doesn't ask "which document?"
- ✅ Agent correctly identifies the referenced document
- ✅ Agent uses rag_search tool (not web search)

---

### **Scenario 2: Note Context Tracking**

**Test Flow:**
```
1. User: "Save a note titled 'Meeting Notes' with content: Discussed Q1 goals"
   → System saves note
   → System adds message: "[SYSTEM] Note saved: 'Meeting Notes'"

2. User: "What's in it?"
   → Expected: Agent recognizes "it" = "Meeting Notes"
   → Agent uses retrieve_note for "Meeting Notes"
   → Response: Shows the content

3. User: "Add 'Review budget' to that note"
   → Expected: Agent recognizes "that note" = "Meeting Notes"
   → Agent uses edit_note with mode='append'
   → Response: Confirms addition to Meeting Notes
```

**What to Verify:**
- ✅ Agent maintains awareness of which note was just created
- ✅ Agent doesn't ask "which note?"
- ✅ Agent correctly appends to the right note

---

### **Scenario 3: Multiple Files - Disambiguation**

**Test Flow:**
```
1. User: "I uploaded two files: ML_Guide.pdf and Python_Tutorial.pdf"
   → Upload both documents
   → System adds messages for both uploads

2. User: "What does it say about neural networks?"
   → Expected: Agent asks for clarification OR searches both documents
   → Better response: "I see you uploaded two files. Which one should I search?"

3. User: "The ML guide"
   → Expected: Agent now searches ML_Guide.pdf specifically
   → Response: Information from ML_Guide.pdf only
```

**What to Verify:**
- ✅ Agent recognizes ambiguity when multiple files exist
- ✅ Agent asks for clarification instead of guessing
- ✅ After clarification, agent remembers the specific file

---

### **Scenario 4: Cross-Reference System Messages**

**Test Flow:**
```
1. User: "Save a note called 'Project Ideas'"
   → System message: "[SYSTEM] Note saved: 'Project Ideas'"

2. [Several unrelated queries about weather, time, etc.]

3. User: "Update the note I created earlier"
   → Expected: Agent checks system messages in history
   → Agent finds "[SYSTEM] Note saved: 'Project Ideas'"
   → Agent uses list_notes → retrieve_note → asks what to add
   → Response: Shows current content and asks for new content
```

**What to Verify:**
- ✅ Agent looks back through entire conversation history
- ✅ Agent identifies notes from system messages
- ✅ Agent maintains context despite intervening queries

---

### **Scenario 5: File Operation Context**

**Test Flow:**
```
1. User: "List files in the documents folder"
   → Agent uses execute_command or appropriate tool
   → Shows: file1.txt, file2.txt, file3.txt

2. User: "What's in that folder?"
   → Expected: Agent recognizes "that folder" = "documents folder"
   → Agent lists the same folder again (or confirms previous answer)

3. User: "Check the second file"
   → Expected: Agent recognizes "second file" = "file2.txt" from previous listing
   → Agent attempts to read file2.txt
```

**What to Verify:**
- ✅ Agent remembers which folder was just listed
- ✅ Agent tracks file positions from previous responses
- ✅ Agent correctly identifies numbered references

---

### **Scenario 6: Pronoun Chaining**

**Test Flow:**
```
1. User: "I saved a note about AI automation"
   → System saves note

2. User: "Can you read it back to me?"
   → Expected: Agent retrieves the note about "AI automation"

3. User: "Thanks. Now add 'Use Python' to it"
   → Expected: Agent appends to the SAME note (maintains chain)

4. User: "Perfect. Show me that note again"
   → Expected: Agent shows the SAME note with the addition
```

**What to Verify:**
- ✅ Agent maintains reference across multiple turns
- ✅ Pronouns chain correctly (it → it → that note all reference same object)
- ✅ Context persists throughout conversation

---

### **Scenario 7: Contextual Switching**

**Test Flow:**
```
1. User: "Upload resume.pdf"
   → Document uploaded

2. User: "What's the weather?"
   → Agent provides weather (unrelated query)

3. User: "What does my resume say about experience?"
   → Expected: Agent remembers "resume.pdf" despite intervening query
   → Agent searches resume.pdf using rag_search
```

**What to Verify:**
- ✅ Agent maintains document context despite topic changes
- ✅ Agent returns to correct context when user references it again
- ✅ Unrelated queries don't erase previous context

---

## 📊 Success Metrics

### **Pass Criteria:**
✅ Agent correctly identifies references 90%+ of the time
✅ Agent asks for clarification when ambiguous
✅ Agent maintains context across 5+ conversation turns
✅ Agent checks system messages for context clues
✅ No false positives (agent doesn't apply old context to new queries)

### **Failure Indicators:**
❌ Agent asks "which file?" when only one file exists
❌ Agent applies wrong context (references wrong file/note)
❌ Agent ignores previous context and performs web search instead of RAG
❌ Agent loses context after 2-3 turns
❌ Agent applies old context to unrelated new queries

---

## 🔧 How to Test

### **Option 1: API Testing (FastAPI /docs)**
```bash
# Start server
cd backend
uvicorn app.main:app --reload

# Visit http://localhost:8000/docs
# Use /api/chat endpoint with same session_id for all messages
```

**Example Request:**
```json
{
  "message": "Upload complete. What does the document say?",
  "session_id": "test_session_123"
}
```

### **Option 2: Python Test Script**
```python
import requests

API_URL = "http://localhost:8000/api/chat"
SESSION_ID = "context_test_001"

def send_message(message):
    response = requests.post(API_URL, json={
        "message": message,
        "session_id": SESSION_ID
    })
    return response.json()

# Test Scenario 1
print(send_message("I just saved a note called 'Ideas'"))
print(send_message("What's in it?"))  # Should recognize "it" = "Ideas" note
print(send_message("Add 'Build mobile app' to that note"))  # Should edit Ideas note
```

---

## 🐛 Debugging Context Issues

### **If Agent Loses Context:**

1. **Check Conversation History:**
   ```
   GET /api/conversations/{session_id}
   ```
   Verify system messages are being saved

2. **Check Logs:**
   ```bash
   # Look for:
   "[Session: {id}] Loaded {N} previous messages"
   ```

3. **Verify System Messages:**
   - Document uploads should create system messages
   - Note creation should create system messages
   - Check database: `SELECT * FROM conversations WHERE role='system'`

4. **Test Conversation History Loading:**
   - Ensure last 5 messages are loaded correctly
   - Check message order (chronological)

---

## 📝 Implementation Details

### **What Changed:**
**File:** `backend/app/agents/voice_agent.py` (lines 219-268)

**Added:**
- Explicit "CONTEXTUAL REFERENCE TRACKING" section in system prompt
- Concrete examples of pronoun → object mapping
- Instructions to check system messages
- Clarification instructions for ambiguity

**Key Instructions to Agent:**
```
- ALWAYS maintain awareness of files, folders, documents, and notes mentioned
- When user uses pronouns, LOOK BACK at the conversation
- Track what was discussed: 'the document' = last mentioned document
- Check system messages in history for uploads, note creation
- If unclear, ask for clarification instead of guessing
```

---

## 🎯 Expected Behavior After Enhancement

### **Before:**
```
User: "I uploaded a research paper"
[uploads paper.pdf]
User: "What does it say?"
Agent: "I'm not sure which document you're referring to. Could you upload it?"
❌ Agent lost context
```

### **After:**
```
User: "I uploaded a research paper"
[uploads paper.pdf → System message added]
User: "What does it say?"
Agent: [Checks history, sees system message about paper.pdf]
Agent: [Uses rag_search on paper.pdf]
Agent: "Based on the research paper you just uploaded, it discusses..."
✅ Agent maintained context
```

---

## 🚀 Next Steps

1. **Run all test scenarios** above
2. **Document any failures** and edge cases
3. **Consider adding:**
   - More specific system messages (e.g., file paths, note IDs)
   - Entity tracking in agent state
   - Explicit reference resolution step before tool calling
4. **Monitor** conversation logs for context loss patterns

---

**Status:** ✅ **Enhanced - Ready for Testing**
**Last Updated:** 2025-10-09
