# AI Persoanl Assistant with Voice Integration

An intelligent voice-powered assistant built with advanced AI technologies, featuring natural language understanding, document analysis, web search, and voice interaction capabilities.

## Overview

This project is a full-stack AI assistant that combines conversational AI with practical tools. Users can interact via text or voice to get real-time information, analyze documents, manage notes, and execute commands - all through natural conversation.

## Key Features

- **Voice Interaction**: Speech-to-text and text-to-speech capabilities for hands-free operation
- **Intelligent Web Search**: Real-time web search with Google Search grounding for accurate, sourced information
- **Document Analysis (RAG)**: Upload and query PDF/text documents using advanced retrieval techniques
- **Smart Note-Taking**: Create, retrieve, edit, and manage notes through conversational commands
- **Multi-Tool Integration**: rag, note taking, web search, system info, command execution, and more
- **Session Management**: Maintains conversation context across multiple interactions
- **Scalable Database**: PostgreSQL (Neon) for production-ready data storage

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML**: Google Gemini (2.5 Flash), LangChain, LangGraph
- **Database**: PostgreSQL (Neon serverless), ChromaDB (vector store)
- **Voice**: Faster Whisper (STT), Edge TTS (TTS)
- **Embeddings**: Sentence Transformers

### Key Libraries
- SQLAlchemy for ORM
- Pydantic for data validation
- uvicorn for ASGI server
- ChromaDB for semantic search
- Google Generative AI SDK

## Architecture

```
User Input (Voice/Text)
    ↓
FastAPI Endpoints
    ↓
Voice Agent (LangGraph)
    ↓
Tool Selection & Execution
    ├── Web Search (Google Grounding)
    ├── RAG Search (ChromaDB)
    ├── Note Management
    └── System Commands
    ↓
Response Generation (Gemini)
    ↓
Output (Voice/Text)
```

## Installation

### Prerequisites
- Python 3.10+
- PostgreSQL (or Neon account)
- Google Gemini API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sandeep231004/Personal-Assistant.git
   cd voice-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys and database URL
   ```

5. **Run the server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

## API Endpoints

### Core Endpoints
- `POST /api/chat` - Text-based chat interface
- `POST /api/voice-chat` - Voice-to-voice interaction
- `POST /api/transcribe` - Speech-to-text conversion
- `POST /api/speak` - Text-to-speech synthesis

### Document Management
- `POST /api/upload-document` - Upload PDF/text documents
- `GET /api/documents` - List uploaded documents

### Notes
- `POST /api/notes` - Create a new note
- `GET /api/notes` - Retrieve notes
- `PUT /api/notes/{note_id}` - Update a note
- `DELETE /api/notes/{note_id}` - Delete a note

### Utilities
- `GET /health` - Health check
- `GET /api/voices` - List available TTS voices

## Usage Examples

### Text Chat
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in New York?", "session_id": "session-1"}'
```

### Document Q&A
1. Upload a document via `/api/upload-document`
2. Ask questions: "What does the document say about machine learning?"

### Voice Interaction
Send an audio file to `/api/voice-chat` and receive a voice response with synthesized speech.

## Project Structure

```
voice-agent/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── agents/           # LangGraph agent logic
│   │   ├── tools/            # Agent tools (search, notes, etc.)
│   │   ├── services/         # Core services (STT, TTS, vector store)
│   │   ├── models.py         # Database models
│   │   ├── database.py       # Database configuration
│   │   └── main.py           # Application entry point
│   ├── data/                 # Data storage (documents, notes)
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment configuration
└── README.md
```

## Features in Detail

### 1. Web Search with Grounding
Performs real-time web searches using Google's Search Grounding API, providing accurate, up-to-date information with source citations.

### 2. RAG (Retrieval Augmented Generation)
- Upload documents (PDF, TXT)
- Automatic chunking and embedding
- Semantic search with re-ranking
- Session-based document isolation

### 3. Voice Capabilities
- **STT**: Faster Whisper model for accurate transcription
- **TTS**: Edge TTS for natural-sounding speech synthesis
- Supports multiple languages and voices

### 4. Agent System
Built with LangGraph for:
- Dynamic tool selection
- Multi-turn conversations
- Context management
- Error handling and recovery

## Database Schema

### Tables
- **conversations**: User/assistant message history
- **notes**: User-created notes with full-text search
- **documents**: Uploaded document metadata

### Vector Store (ChromaDB)
- Document embeddings for semantic search
- Metadata filtering by session
- Re-ranking for relevance

## Configuration

Key environment variables:
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key
GEMINI_SEARCH_API_KEY=your_search_api_key

# Database
DATABASE_URL=postgresql://user:pass@host/db

# Application
DEBUG=True
APP_NAME=Voice Assistant
```

## Performance

- **Chat Response**: < 2s (without web search)
- **Voice Processing**: 3-5s end-to-end
- **Document Upload**: Depends on size (typical PDF: 5-10s)
- **RAG Search**: < 1s for semantic retrieval

## Future Enhancements

- [ ] Frontend web interface (React/Vue)
- [ ] User authentication and multi-tenancy
- [ ] Migrate ChromaDB to PostgreSQL pgvector
- [ ] Real-time streaming responses
- [ ] Mobile app integration
- [ ] Advanced analytics dashboard

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini for conversational AI
- LangChain/LangGraph for agent framework
- Faster Whisper for speech recognition
- ChromaDB for vector storage
- Neon for serverless PostgreSQL

---

**Built with ❤️ for intelligent automation**

