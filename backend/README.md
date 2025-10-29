# Voice Assistant Backend

A modern AI-powered voice assistant with RAG capabilities, built with LangChain, LangGraph, and Gemini API.

## Features

- 🤖 **Intelligent Agent**: LangGraph-powered agent with Gemini 2.0
- 📚 **RAG Search**: Document search using ChromaDB vector store
- 🔍 **Web Search**: Real-time web search via DuckDuckGo
- 📝 **Note Taking**: Store and retrieve notes with database persistence
- ⚡ **Command Execution**: Execute basic system commands
- 💬 **Conversation**: Natural language chat with memory

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Gemini API key
# Get key from: https://aistudio.google.com/apikey
```

### 4. Initialize Database

```bash
python -m app.database
```

### 5. Run Server

```bash
uvicorn app.main:app --reload
```

Visit: http://localhost:8000/docs for API documentation

## Project Structure

```
backend/
├── app/
│   ├── agents/          # LangGraph agents
│   ├── tools/           # LangChain tools
│   ├── api/             # FastAPI routes
│   ├── config.py        # Settings
│   ├── database.py      # SQLAlchemy setup
│   ├── models.py        # Database models
│   └── main.py          # FastAPI app
├── data/                # Data storage
│   ├── documents/       # PDFs for RAG
│   ├── chroma_db/       # Vector database
│   └── user_notes/      # Saved notes
├── requirements.txt
└── .env
```

## API Endpoints

- `POST /chat` - Send message to agent
- `POST /upload-document` - Upload document for RAG
- `GET /notes` - List all notes
- `POST /notes` - Create new note

## Technologies

- **FastAPI** - Modern web framework
- **LangChain** - LLM application framework
- **LangGraph** - Agent orchestration
- **Gemini 2.0** - Google's LLM
- **ChromaDB** - Vector database
- **SQLAlchemy** - ORM for SQLite
- **sentence-transformers** - Embeddings

## Development

This is Phase 1 focusing on core agent logic. Future phases will add:
- Frontend (React/Next.js)
- Authentication (JWT)
- Multi-user support
- Voice integration
- Cloud deployment
