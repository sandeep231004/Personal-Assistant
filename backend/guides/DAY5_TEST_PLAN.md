# Voice Integration - Day 5 Test Plan

**Date:** 2025-10-21
**Phase:** Voice Integration Testing & Optimization
**Status:** Ready to Begin

---

## 🎯 **Testing Objectives**

1. **Functional Testing** - Verify all voice endpoints work correctly
2. **Integration Testing** - Test complete voice chat flow with all 11 tools
3. **Performance Testing** - Measure latency and optimize bottlenecks
4. **Error Handling** - Test edge cases and error scenarios
5. **Session Management** - Verify conversation history works with voice

---

## 📋 **Test Categories**

### **1. STT Endpoint Testing** (`/api/transcribe`)

#### Test Cases:
- [x] Test with MP3 audio file
- [x] Test with WAV audio file
- [ ] Test with M4A audio file
- [ ] Test with OGG audio file
- [ ] Test language detection (English audio)
- [ ] Test language detection (non-English audio)
- [X] Test with noisy audio
- [X] Test with very short audio (<1 second)
- [ ] Test with long audio (30+ seconds)
- [ ] Test with silence
- [ ] Test error: No file provided
- [ ] Test error: Invalid file format
- [ ] Test error: File too large (>10 MB)

#### Expected Results:
- Accurate transcription with confidence scores
- Correct language detection
- Appropriate error messages for invalid inputs

---

### **2. TTS Endpoint Testing** (`/api/speak`)

#### Test Cases:
- [x] Test with default voice (en-US-AriaNeural)
- [ ] Test with different voices (male, female, accents)
- [ ] Test with different languages
- [ ] Test with very short text (1 word)
- [ ] Test with medium text (1 paragraph)
- [ ] Test with long text (500+ words)
- [ ] Test with special characters and punctuation
- [ ] Test with numbers and dates
- [ ] Test voice customization (rate, pitch, volume)
- [ ] Test error: Empty text
- [ ] Test error: Invalid voice ID

#### Expected Results:
- Natural-sounding audio output
- Correct MP3 format
- Proper handling of text variations

---

### **3. Voice Chat Endpoint Testing** (`/api/voice-chat`)

#### Test Cases - Basic Flow:
- [X] Test complete flow: audio → transcription → agent → synthesis
- [X] Test with new session (no history)
- [X] Test with existing session (with conversation history)
- [X] Test response includes all required fields
- [ ] Test audio response is valid base64-encoded MP3

#### Test Cases - Agent Tool Integration:
Test voice commands that trigger each of the 11 tools:

1. **Web Search Tool**
   - [X] "Search the web for latest AI news"
   - [X] "What's the weather in New York?"

2. **Calculator Tool** (No Calculator tool)
   - [X] "Calculate 25 multiplied by 47"
   - [X] "What's 15% of 200?"

3. **RAG Search Tool**
   - [X] Upload document first, then: "Search the document for [topic]"
   - [X] "What does the paper say about [subject]?"

4. **Date/Time Tool**
   - [X] "What time is it?"
   - [X] "What's today's date?"

5. **Note Creation Tool**
   - [X] "Create a note: Remember to buy groceries"
   - [X] "Save this: Meeting at 3 PM"

6. **Note Retrieval Tool**
   - [X] "Show me my notes"
   - [X] "What notes do I have?"

7. **System Info Tool**
   - [X] "What's my system information?"
   - [X] "Show me my operating system details"

8. **Command Execution Tool**
   - [X] "List files in current directory"
   - [X] "Show me the directory tree"

9. **Conversation History Tool**
   - [X] "What did we talk about earlier?"
   - [X] "Show me our conversation history"

10. **Recall Tool**
    - [] "Remember: My favorite color is blue"
    - [ ] "What's my favorite color?"

11. **Knowledge Retrieval Tool**
    - [] "Retrieve knowledge about Python programming"
    - [ ] "What do you know about machine learning?"

#### Expected Results:
- Correct tool selection based on voice query
- Accurate tool execution
- Natural voice response
- Proper session management

---

### **4. Voices Endpoint Testing** (`/api/voices`)

#### Test Cases:
- [ ] Get all available voices (should return 550+)
- [ ] Filter by language: en-US
- [ ] Filter by language: es-ES
- [ ] Filter by language: fr-FR
- [ ] Test invalid language code
- [ ] Verify voice metadata (name, gender, locale)

#### Expected Results:
- Complete list of voices with metadata
- Correct filtering by language
- Fast response time (<1 second)

---

## ⚡ **Performance Benchmarks**

### Target Latencies:
| Component | Target | Notes |
|-----------|--------|-------|
| STT (10s audio) | <2s | Time to transcribe average query |
| Agent Processing | <2s | Existing agent + tools |
| TTS (50 words) | <1s | Time to generate speech |
| **Total Voice Chat** | **<5s** | End-to-end response time |

### Performance Tests:
- [ ] Measure STT latency with 5-second audio
- [ ] Measure STT latency with 10-second audio
- [ ] Measure STT latency with 30-second audio
- [ ] Measure TTS latency with 10 words
- [ ] Measure TTS latency with 50 words
- [ ] Measure TTS latency with 200 words
- [ ] Measure complete voice chat latency (end-to-end)
- [ ] Test concurrent requests (5 simultaneous voice chats)
- [ ] Monitor memory usage during operation
- [ ] Monitor CPU usage during operation

### Optimization Targets:
- [ ] If STT >3s: Consider using "tiny" model for faster inference
- [ ] If TTS >2s: Optimize chunking strategy
- [ ] If total >7s: Investigate parallel processing opportunities

---

## 🔍 **Error Handling Tests**

### STT Errors:
- [ ] Missing audio file
- [ ] Corrupted audio file
- [ ] Unsupported format
- [ ] File too large
- [ ] Empty audio file
- [ ] Network timeout (if applicable)

### TTS Errors:
- [ ] Empty text input
- [ ] Invalid voice ID
- [ ] Text too long (>5000 chars)
- [ ] Invalid parameters (rate, pitch, volume)

### Voice Chat Errors:
- [ ] Missing session_id
- [ ] Invalid session_id format
- [ ] Database connection failure
- [ ] Agent processing timeout
- [ ] Whisper model not loaded
- [ ] Edge-TTS connection failure

### Expected Results:
- Clear error messages
- Appropriate HTTP status codes
- No server crashes
- Graceful degradation

---

## 🔄 **Session Management Tests**

### Test Scenarios:
- [ ] Create new session with voice chat
- [ ] Continue conversation in same session
- [ ] Load conversation history (5+ exchanges)
- [ ] Verify system messages are preserved
- [ ] Test RAG search with session-uploaded documents
- [ ] Verify cross-session isolation (no data leakage)
- [ ] Test long conversation (20+ exchanges)
- [ ] Test multiple simultaneous sessions

---

## 📊 **Audio Quality Tests**

### STT Quality:
- [ ] Test with clear audio (professional recording)
- [ ] Test with ambient noise (office, street)
- [ ] Test with different accents (US, UK, AU, IN)
- [ ] Test with fast speech
- [ ] Test with slow speech
- [ ] Test with whispered speech
- [ ] Test with multiple speakers (if applicable)

### TTS Quality:
- [ ] Verify natural prosody (rhythm and intonation)
- [ ] Test pronunciation of technical terms
- [ ] Test pronunciation of names and places
- [ ] Test handling of acronyms (NASA, FBI, etc.)
- [ ] Test handling of numbers (dates, phone numbers, currencies)
- [ ] Verify audio clarity (no distortion, artifacts)

---

## 🛠️ **Integration Tests**

### End-to-End Workflows:
1. **Document Q&A Workflow**
   - [ ] Upload document via `/api/upload-document`
   - [ ] Ask question via voice chat: "What's in the document?"
   - [ ] Verify RAG search is used
   - [ ] Verify correct document content in response

2. **Note-Taking Workflow**
   - [ ] Create note via voice: "Create a note: Buy milk"
   - [ ] Retrieve notes via voice: "What are my notes?"
   - [ ] Verify note appears in response

3. **Multi-Turn Conversation**
   - [ ] Voice query 1: "Search for Python tutorials"
   - [ ] Voice query 2: "What did you just tell me?" (should recall)
   - [ ] Voice query 3: "Create a note about it"
   - [ ] Verify contextual understanding across turns

4. **Tool Chaining**
   - [ ] Voice query: "Search the web for weather in Paris, then create a note about it"
   - [ ] Verify multiple tools are used in sequence

---

## 📝 **Test Execution Checklist**

### Prerequisites:
- [x] Voice services created and tested individually
- [x] Voice routes integrated into main.py
- [x] Server starts without errors
- [x] All endpoints accessible
- [ ] Test audio files prepared (MP3, WAV, M4A, OGG)
- [ ] Test documents prepared for RAG testing

### Test Execution:
- [ ] Run all STT endpoint tests
- [ ] Run all TTS endpoint tests
- [ ] Run all voice chat endpoint tests
- [ ] Run all voices endpoint tests
- [ ] Run performance benchmarks
- [ ] Run error handling tests
- [ ] Run session management tests
- [ ] Run audio quality tests
- [ ] Run integration tests

### Post-Testing:
- [ ] Document all issues found
- [ ] Optimize bottlenecks
- [ ] Fix critical bugs
- [ ] Update documentation
- [ ] Create usage examples

---

## 🐛 **Known Issues**

### Warnings to Address:
1. **FFmpeg Not Found** - `pydub` warning about missing ffmpeg
   - Impact: Audio conversion may fail for some formats
   - Solution: Install ffmpeg or use direct WAV files
   - Priority: Medium

2. **pkg_resources Deprecation** - Warning from ctranslate2
   - Impact: None (just a warning)
   - Solution: Will be fixed in future library updates
   - Priority: Low

---

## 📈 **Success Criteria**

Day 5 is complete when:
- [ ] All critical test cases pass (green checkmarks)
- [ ] Performance targets are met (<5s total latency)
- [ ] All 11 tools work via voice commands
- [ ] Error handling is robust
- [ ] Session management works correctly
- [ ] No server crashes or critical bugs
- [ ] Audio quality is acceptable
- [ ] Documentation is updated

---

## 📌 **Next Steps After Day 5**

**Day 6:** Documentation & Polish
- Create API usage guide
- Add code examples for each endpoint
- Create troubleshooting guide
- Record demo video

**Day 7:** Final Integration & Deployment
- Final end-to-end testing
- Performance optimization
- Deployment preparation
- Project completion summary

---

**Test Plan Created:** 2025-10-21
**Ready for Execution:** ✅
**Estimated Time:** 4-6 hours
