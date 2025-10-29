# Testing RAG - Quick Guide

## Step 1: Install New Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `chromadb` - Vector database
- `sentence-transformers` - Embeddings
- `pypdf` - PDF processing

**Expected time**: 2-3 minutes (downloading models)

---

## Step 2: Start the Server

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Initializing Vector Store Service...
INFO:     Vector store initialized
INFO:     Agent initialized with 2 tools
```

---

## Step 3: Test via API Docs

Open: **http://localhost:8000/docs**

### 3.1 Upload a Document

1. Find **POST /api/upload-document**
2. Click **"Try it out"**
3. Click **"Choose File"** and select a PDF or TXT file
4. Click **"Execute"**

**Expected Response:**
```json
{
  "message": "Document processed and added to knowledge base (X chunks created)",
  "filename": "your_document.pdf",
  "status": "processed",
  "document_id": 1
}
```

**What's happening:**
- File is saved to `data/documents/`
- Document is chunked using recursive splitter
- Chunks are embedded and stored in ChromaDB
- Database tracks the document

### 3.2 Ask Questions About the Document

1. Find **POST /api/chat**
2. Click **"Try it out"**
3. Enter:
```json
{
  "message": "What is the main topic of the document?",
  "session_id": "test"
}
```
4. Click **"Execute"**

**Expected Response:**
```json
{
  "response": "Based on the document, the main topic is...",
  "session_id": "test",
  "tools_used": ["rag_search"]
}
```

**Key Check**: `tools_used` should include `"rag_search"`!

---

## Step 4: Test Tool Selection

The agent should automatically choose the right tool:

### Test RAG Search:
```json
{
  "message": "Summarize the uploaded document",
  "session_id": "test"
}
```
→ Should use: `rag_search`

### Test Web Search:
```json
{
  "message": "What's the latest news about AI?",
  "session_id": "test"
}
```
→ Should use: `web_search`

### Test General Conversation:
```json
{
  "message": "Hello! How are you?",
  "session_id": "test"
}
```
→ Should use: `[]` (no tools)

---

## Step 5: Check Logs

In your terminal, you'll see detailed logs:

```
INFO: Performing RAG search for: What is the main topic...
INFO: Found 15 relevant chunks from vector search
INFO: Applying re-ranking...
INFO: Re-ranked to top 3 results
INFO: Agent calling tools: ['rag_search']
```

This shows:
- Vector search retrieved 15 candidates
- Re-ranker narrowed to top 3
- Agent used the RAG tool

---

## Troubleshooting

### Error: "No module named 'chromadb'"
```bash
pip install chromadb sentence-transformers pypdf
```

### Error: "Collection is empty"
Make sure you uploaded a document first!

### Agent not using RAG tool?
- Check if document was uploaded successfully
- Try being more specific: "Based on the document, tell me about..."

### Slow first query?
- Models are loading (embeddings, re-ranker)
- Subsequent queries will be faster

---

## Sample Test Document

Don't have a PDF? Create a simple text file:

`test_doc.txt`:
```
Machine Learning Basics

Machine learning is a subset of artificial intelligence that enables
systems to learn from data without being explicitly programmed.

There are three main types:
1. Supervised Learning - trained on labeled data
2. Unsupervised Learning - finds patterns in unlabeled data
3. Reinforcement Learning - learns through trial and error

Common applications include image recognition, natural language
processing, and recommendation systems.
```

Upload this and ask:
- "What are the three types of machine learning?"
- "What is machine learning?"
- "What applications are mentioned?"

---

## Next Steps

Once RAG is working:

1. **Add Note-Taking Tool** - Let agent save notes to database
2. **Add Command Execution** - Execute simple system commands
3. **Test Different Documents** - Try various PDFs
4. **Experiment with Chunking** - Change `CHUNK_SIZE` in config

---

**Expected Result**: Agent intelligently chooses between RAG and web search based on context! 🎉
