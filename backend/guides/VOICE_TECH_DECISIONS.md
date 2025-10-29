# Voice Integration - Technology Decisions

**Date:** 2025-10-09
**Phase:** Voice Integration (Phase 3)
**Status:** Day 1 Complete

---

## 🎯 **Technology Stack Selected**

### **Speech-to-Text (STT)**
- **Library:** `faster-whisper` v1.2.0
- **Model:** Whisper (by OpenAI, optimized by faster-whisper)
- **Device:** CPU (with potential GPU support)
- **Compute Type:** int8 (for speed)

**Why chosen:**
- ✅ **Local processing** - No API costs, unlimited usage
- ✅ **Fast** - Optimized implementation of Whisper
- ✅ **Accurate** - State-of-the-art speech recognition
- ✅ **Multi-language** - Supports 99+ languages
- ✅ **Offline capable** - Works without internet

**Model sizes available:**
| Model | Speed | Accuracy | RAM Usage | Use Case |
|-------|-------|----------|-----------|----------|
| tiny | Fastest | Basic | ~1 GB | Quick testing |
| base | Fast | Good | ~1 GB | Development |
| small | Medium | Better | ~2 GB | **Recommended for production** |
| medium | Slow | High | ~5 GB | High accuracy needed |
| large | Slowest | Best | ~10 GB | Maximum accuracy |

**Decision:** Use `small` model for production (best balance)

---

### **Text-to-Speech (TTS)**
- **Library:** `edge-tts` v7.2.3
- **Provider:** Microsoft Azure Cognitive Services (via edge-tts)
- **Default Voice:** `en-US-AriaNeural` (female, American)

**Why chosen:**
- ✅ **Free** - No API costs
- ✅ **Natural voices** - Neural TTS, very realistic
- ✅ **550+ voices** - Multiple languages, accents, genders
- ✅ **Fast** - Quick synthesis
- ✅ **High quality** - Professional-grade audio

**Popular English Voices:**
| Voice | Gender | Accent | Use Case |
|-------|--------|--------|----------|
| `en-US-AriaNeural` | Female | American | **Default** (professional, clear) |
| `en-US-GuyNeural` | Male | American | Alternative male voice |
| `en-GB-SoniaNeural` | Female | British | UK users |
| `en-GB-RyanNeural` | Male | British | UK users (male) |
| `en-AU-NatashaNeural` | Female | Australian | Australian users |

**Decision:** Use `en-US-AriaNeural` as default, allow user selection

---

### **Audio Processing**
- **Library:** `pydub` v0.25.1
- **Audio I/O:** `soundfile` v0.13.1

**Capabilities:**
- Format conversion (MP3 ↔ WAV ↔ M4A ↔ OGG)
- Audio normalization
- Noise reduction (future enhancement)
- Trimming silence
- Volume adjustment

---

## 📊 **Audio Standards Defined**

### **Input (User Audio)**
**Supported Formats:**
- MP3 (most common)
- WAV (uncompressed, high quality)
- M4A (Apple devices)
- OGG (open source)
- FLAC (lossless)

**Requirements:**
- Max file size: 10 MB
- Max duration: 60 seconds (for single query)
- Sample rate: Any (auto-converted)
- Channels: Mono or Stereo (converted to mono for STT)

### **Output (AI Audio Response)**
**Format:** MP3
**Settings:**
- Sample rate: 24 kHz (high quality)
- Bitrate: 64 kbps (good balance)
- Channels: Mono
- Encoding: Constant Bitrate (CBR)

**Why MP3:**
- ✅ Universal browser support
- ✅ Small file size
- ✅ Good quality at low bitrates
- ✅ Streaming friendly

---

## ⚡ **Performance Targets**

| Metric | Target | Notes |
|--------|--------|-------|
| **STT Latency** | <2s | Time to transcribe average query (10s audio) |
| **Agent Processing** | <2s | Existing agent + tools |
| **TTS Latency** | <1s | Time to generate speech |
| **Total Response Time** | <5s | End-to-end (audio in → audio out) |
| **Audio Quality** | High | Natural, clear, professional |

---

## 🔧 **Testing Results (Day 1)**

### **faster-whisper Test:**
```
[OK] Model loaded successfully!
Model size: tiny
Device: CPU
Compute type: int8
Status: Working correctly
```

### **edge-tts Test:**
```
[OK] Audio generated successfully!
File: test_output.mp3
Size: 47,664 bytes
Voice: en-US-AriaNeural
Total voices available: 550
Status: Working correctly
```

---

## 💰 **Cost Analysis**

### **Current Implementation (Free Tier):**
- STT: `faster-whisper` - **$0/month** (local processing)
- TTS: `edge-tts` - **$0/month** (free API access)
- **Total Cost: $0/month** ✅

### **Alternative (Paid Options):**
**If needed for scaling or premium quality:**

| Service | Provider | Cost | Notes |
|---------|----------|------|-------|
| STT | OpenAI Whisper API | $0.006/minute | Cloud-based, auto-scaling |
| STT | Google Speech-to-Text | $0.006-0.024/minute | Multiple models available |
| TTS | ElevenLabs | $5-99/month | Most natural voices |
| TTS | Google Text-to-Speech | $4/1M characters | WaveNet voices |

**Decision:** Start with free tier, upgrade if needed

---

## 🎤 **Voice Model Recommendations**

### **For Production:**
**STT Model:** `small`
- Best balance of speed/accuracy
- ~2 GB RAM
- Fast enough for real-time
- Accurate enough for production

**TTS Voice:** `en-US-AriaNeural`
- Professional, clear American English
- Gender-neutral tone
- Works well for all use cases

### **For Development/Testing:**
**STT Model:** `tiny` or `base`
- Fast downloads
- Quick testing
- Lower RAM usage

### **For Multi-language:**
**STT:** Whisper auto-detects language
**TTS:** Select voice based on user's language:
- Spanish: `es-US-AlonsoNeural`
- French: `fr-FR-DeniseNeural`
- German: `de-DE-KatjaNeural`
- (550+ voices available)

---

## 📁 **File Organization**

### **Test Scripts Created:**
- `backend/test_stt.py` - Test Speech-to-Text
- `backend/test_tts.py` - Test Text-to-Speech

### **To Be Created (Day 2+):**
- `backend/app/services/speech_to_text.py` - STT service
- `backend/app/services/text_to_speech.py` - TTS service
- `backend/app/services/audio_utils.py` - Audio processing utilities
- `backend/app/api/voice_routes.py` - Voice API endpoints

---

## ✅ **Days 1-4 Complete**

### **Day 1 - Environment Setup**
**Achievements:**
- ✅ Installed all voice dependencies
- ✅ Tested faster-whisper (STT) - Working
- ✅ Tested edge-tts (TTS) - Working
- ✅ Selected technology stack
- ✅ Defined audio standards
- ✅ Set performance targets

### **Day 2 - STT Service**
**Achievements:**
- ✅ Created `app/services/speech_to_text.py` (340+ lines)
- ✅ Multi-format audio support (MP3, WAV, M4A, OGG, FLAC, WEBM)
- ✅ Audio preprocessing (mono, normalize, silence trimming)
- ✅ Whisper model integration with confidence scoring
- ✅ Created `app/services/audio_utils.py` for audio utilities
- ✅ Created test script `test_stt_service.py` - All tests passed

### **Day 3 - TTS Service**
**Achievements:**
- ✅ Created `app/services/text_to_speech.py` (330+ lines)
- ✅ 550+ voice support via edge-tts
- ✅ Voice customization (rate, pitch, volume)
- ✅ Async and sync methods
- ✅ Long text chunking for extended responses
- ✅ Created test script `test_tts_service.py` - All tests passed
- ✅ Fixed pitch parameter bug (must use Hz format: "+0Hz")

### **Day 4 - Voice API Endpoints**
**Achievements:**
- ✅ Created `app/api/voice_routes.py` (350+ lines)
- ✅ POST `/api/transcribe` - Audio to text (STT only)
- ✅ POST `/api/speak` - Text to audio (TTS only)
- ✅ POST `/api/voice-chat` - Complete flow (audio → agent → audio)
- ✅ GET `/api/voices` - List available TTS voices
- ✅ Integrated voice router into `main.py`
- ✅ Updated health check endpoint with voice services
- ✅ Verified all endpoints accessible via FastAPI server

**Complete Voice Integration Pipeline:**
```
Audio Input → Transcribe (STT) → Agent Processing (11 tools) → Synthesize (TTS) → Audio Output
```

**Next:** Day 5 - Testing & Optimization

---

**Last Updated:** 2025-10-21
**Status:** ✅ Days 1-4 complete, ready for Day 5 testing
