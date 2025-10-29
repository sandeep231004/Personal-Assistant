# Voice Assistant - Setup Guide

Welcome! Let's get your AI voice assistant up and running. 🚀

## Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the API key

## Step 2: Set Up Python Environment

Open your terminal in the `backend` folder and run:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

# You should see (venv) in your terminal now
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This might take a few minutes. ☕

## Step 4: Configure Environment Variables

```bash
# Copy the example file
copy .env.example .env

# Now open .env file and add your Gemini API key:
# GEMINI_API_KEY=your_actual_api_key_here
```

## Step 5: Initialize Database

```bash
python -c "from app.database import init_db; init_db()"
```

You should see: ✅ Database initialized successfully!

## Step 6: Run the Server

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete!
```

## Step 7: Test It!

Open your browser and go to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Quick Test via API Docs

1. Go to http://localhost:8000/docs
2. Click on **POST /api/chat**
3. Click **"Try it out"**
4. Enter a message like:
   ```json
   {
     "message": "Search the web for latest AI news",
     "session_id": "test"
   }
   ```
5. Click **Execute**
6. See the response! 🎉

## Troubleshooting

### Error: "No module named 'app'"
- Make sure you're in the `backend` folder
- Make sure virtual environment is activated (you see `(venv)`)

### Error: "GEMINI_API_KEY not set"
- Check your `.env` file exists
- Make sure the API key is correct (no extra spaces)

### Error: "Address already in use"
- Another app is using port 8000
- Run with different port: `uvicorn app.main:app --reload --port 8001`

## What's Working Right Now

✅ FastAPI server
✅ LangGraph agent with Gemini
✅ Web search tool (DuckDuckGo)
✅ SQLite database
✅ Notes API
✅ Conversation history

## What's Coming Next

🔜 RAG search (ChromaDB)
🔜 Note-taking tool
🔜 Command execution
🔜 Voice integration

## Need Help?

Check the logs in your terminal - they'll show you what's happening!
