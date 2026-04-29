# Phase 1: Foundation & Core Infrastructure

> **Scope:** WhatsApp API Integration + Event-Driven Architecture + ASR Pipeline  
> **Duration:** ~3–4 weeks  
> **Goal:** Establish the foundational backbone — a working WhatsApp bot that receives text/voice messages, queues them through an event-driven pipeline, transcribes voice messages via ASR, and sends replies back.

---

## 1.1 Objectives

| # | Objective | Success Metric |
|---|-----------|---------------|
| 1 | WhatsApp Business API connected via Twilio (or Meta Cloud API) | Webhook receives inbound messages and logs them |
| 2 | Event-driven message queue operational | Messages flow through queue → parser → handler |
| 3 | Basic text echo-bot functional | Send a WhatsApp text, receive a canned reply within 2s |
| 4 | ASR pipeline for voice messages | Voice note in Hindi/English/Tamil → accurate transcript logged (≥80% WER) |
| 5 | Project scaffolding & database | Postgres DB with core tables, S3/MinIO for file storage |

---

## 1.2 Tech Stack Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Runtime** | Python 3.11+ (FastAPI) | Best ecosystem for AI/ML libs (Whisper, LangChain, HuggingFace) |
| **WhatsApp API** | Twilio WhatsApp API (sandbox for dev) | Simplifies messaging + calling; well-documented; free sandbox |
| **Message Queue** | Redis + BullMQ (or AWS SQS if cloud) | Lightweight, fast, supports job routing by message type |
| **ASR Engine** | OpenAI Whisper v2 (via HuggingFace `transformers`) | Supports Hindi, Tamil, Malayalam; easy local/cloud deployment |
| **Database** | PostgreSQL 16 | Robust, free, handles structured data well |
| **Object Storage** | MinIO (local dev) / AWS S3 (prod) | Store voice files, images, documents |
| **Containerization** | Docker + Docker Compose | Consistent dev/prod environments |

---

## 1.3 Architecture (Phase 1 Scope)

```mermaid
flowchart LR
  subgraph External
    U["User (WhatsApp)"] --> TW["Twilio WhatsApp API"]
  end

  subgraph Backend ["Backend (FastAPI)"]
    TW -->|Webhook POST| WH["Webhook Handler"]
    WH --> Q["Message Queue (Redis)"]
    Q --> P["Message Parser"]
    P -->|text| TH["Text Handler"]
    P -->|voice| VH["Voice Handler"]
    VH --> ASR["Whisper ASR"]
    ASR --> TH
    TH --> RB["Response Builder"]
    RB --> TW
  end

  subgraph Storage
    VH -->|store audio| S3["MinIO / S3"]
    TH -->|log| DB["PostgreSQL"]
  end
```

---

## 1.4 Detailed Deliverables

### 1.4.1 Project Scaffolding

```
tradesbot/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                  # FastAPI app entry
│   ├── config.py                # Environment config loader
│   ├── api/
│   │   ├── webhooks.py          # Twilio webhook routes
│   │   └── health.py            # Health check endpoint
│   ├── services/
│   │   ├── whatsapp.py          # Send messages via Twilio
│   │   ├── queue.py             # Redis queue producer/consumer
│   │   ├── parser.py            # Message type detection & routing
│   │   ├── asr.py               # Whisper ASR service
│   │   └── media.py             # Fetch media from WhatsApp API
│   ├── models/
│   │   ├── database.py          # SQLAlchemy/asyncpg setup
│   │   └── schemas.py           # Pydantic models
│   ├── db/
│   │   └── migrations/          # Alembic migrations
│   └── utils/
│       ├── audio.py             # OGG→WAV conversion (ffmpeg)
│       └── logger.py            # Structured logging
├── tests/
│   ├── test_webhook.py
│   ├── test_asr.py
│   └── test_queue.py
└── scripts/
    └── setup_twilio.py          # Helper to configure Twilio sandbox
```

### 1.4.2 Database Schema (Initial Tables)

```sql
-- Users table (tradespeople)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    trade_type VARCHAR(50),           -- plumber, electrician, carpenter, etc.
    language_preference VARCHAR(10) DEFAULT 'en',  -- en, hi, ta, ml
    gstin VARCHAR(20),
    hourly_rate DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    phone_number VARCHAR(15) NOT NULL,
    name VARCHAR(100),
    address TEXT,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table (message log)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    customer_id UUID REFERENCES customers(id),
    direction VARCHAR(10) NOT NULL,    -- 'inbound' or 'outbound'
    message_type VARCHAR(20) NOT NULL, -- 'text', 'voice', 'image', 'document'
    content TEXT,                       -- text content or transcript
    media_url TEXT,                     -- S3/MinIO URL for media
    metadata JSONB,                     -- extra data (ASR confidence, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table (placeholder for Phase 2)
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    customer_id UUID REFERENCES customers(id),
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, scheduled, in_progress, completed
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.4.3 WhatsApp Webhook Handler

**Endpoint:** `POST /api/webhooks/twilio`

**Incoming payload fields (Twilio):**
- `From` – sender's WhatsApp number (`whatsapp:+91XXXXXXXXXX`)
- `Body` – text content (empty for media-only)
- `NumMedia` – count of media attachments
- `MediaUrl0`, `MediaContentType0` – media URL and MIME type
- `MessageSid` – unique message ID

**Logic:**
1. Validate Twilio signature (security).
2. Parse message type: `text` if Body present, `voice` if MediaContentType is audio/*, `image` if image/*, `document` otherwise.
3. Enqueue to Redis with `{message_sid, from, type, body, media_url, timestamp}`.
4. Return `200 OK` with empty TwiML (acknowledge receipt).

### 1.4.4 Message Queue & Parser

**Queue Design:**
- **Queue name:** `inbound_messages`
- **Consumer workers:** 2–4 (configurable)
- **Job schema:**
  ```json
  {
    "message_sid": "SM...",
    "from": "whatsapp:+919876543210",
    "type": "voice",
    "body": "",
    "media_url": "https://api.twilio.com/...",
    "timestamp": "2026-04-24T18:30:00Z"
  }
  ```

**Parser routing:**
- `type == "text"` → Text Handler (Phase 1: echo reply; Phase 2+: LLM agent)
- `type == "voice"` → Voice Handler → ASR → Text Handler
- `type == "image"` → (Phase 6: OCR) — for now, reply "Image received, noted."
- `type == "document"` → Store in S3, reply "Document saved."

### 1.4.5 ASR Pipeline (Voice → Text)

**Flow:**
1. **Fetch audio:** Download voice file from Twilio Media API using `MediaUrl0` + auth.
2. **Convert format:** Use `ffmpeg` to convert OGG/Opus → WAV (16kHz mono PCM).
3. **Transcribe:** Load Whisper model (`openai/whisper-medium` or `openai/whisper-large-v2`) via HuggingFace `transformers`.
4. **Output:** Return transcript text + detected language + confidence.
5. **Store:** Save audio file to MinIO/S3, log transcript in `conversations` table.

**Whisper Configuration:**
```python
from transformers import pipeline

asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-medium",
    device="cuda:0",  # or "cpu" for dev
    chunk_length_s=30,
    return_timestamps=True,
)

result = asr_pipeline(
    "audio.wav",
    generate_kwargs={
        "language": "hindi",   # or auto-detect
        "task": "transcribe",
    }
)
# result["text"] → transcribed text
```

**Language Detection:**
- Whisper auto-detects language from first 30s.
- Override with user's `language_preference` from DB if known.
- Log detected language in `conversations.metadata`.

### 1.4.6 Response Builder & WhatsApp Reply

**Phase 1 behavior (echo/canned):**
- For text messages: reply with `"✅ Received: {body}. Our AI assistant is being set up!"`
- For voice messages: reply with `"🎤 I heard: '{transcript}'. Our AI assistant will be ready soon!"`
- For images/docs: reply with acknowledgment.

**Twilio send function:**
```python
from twilio.rest import Client

def send_whatsapp_message(to: str, body: str, media_url: str = None):
    client = Client(TWILIO_SID, TWILIO_AUTH)
    msg = client.messages.create(
        from_=f"whatsapp:{TWILIO_NUMBER}",
        to=to,
        body=body,
        media_url=[media_url] if media_url else None,
    )
    return msg.sid
```

---

## 1.5 Environment Variables

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886   # sandbox number

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tradesbot

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO / S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=tradesbot-media

# ASR
WHISPER_MODEL=openai/whisper-medium
WHISPER_DEVICE=cpu   # or cuda:0

# App
APP_ENV=development
LOG_LEVEL=INFO
```

---

## 1.6 Docker Compose (Dev Environment)

```yaml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - redis
      - minio
    volumes:
      - ./app:/app/app

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: tradesbot
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

volumes:
  pgdata:
  minio_data:
```

---

## 1.7 Acceptance Criteria

| # | Criterion | How to Verify |
|---|-----------|---------------|
| 1 | Twilio webhook receives messages | Send WhatsApp text to sandbox → server logs show parsed payload |
| 2 | Messages are queued in Redis | Check Redis queue length after sending message |
| 3 | Text messages get echo reply | Send "Hello" → receive "✅ Received: Hello..." within 3s |
| 4 | Voice messages are transcribed | Send Hindi voice note → reply contains transcript |
| 5 | ASR accuracy ≥ 80% | Test with 10 sample voice notes → measure WER |
| 6 | Media files stored in MinIO | After voice/image message → file visible in MinIO console |
| 7 | Conversations logged in DB | Query `conversations` table → entries match sent messages |
| 8 | Docker Compose boots cleanly | `docker compose up` → all services healthy |

---

## 1.8 Testing Strategy

### Unit Tests
- `test_parser.py` — Verify message type detection (text/voice/image/doc)
- `test_audio_convert.py` — OGG → WAV conversion produces valid audio
- `test_asr.py` — Whisper transcribes sample audio files correctly

### Integration Tests
- `test_webhook_flow.py` — Simulate Twilio POST → verify queue entry + DB log + reply
- `test_voice_flow.py` — POST voice message → verify ASR + transcript in reply

### Manual Tests
- Use Twilio WhatsApp Sandbox to send real messages from a phone
- Test with voice notes in: English, Hindi, Tamil, Malayalam
- Verify latency (< 5s for text, < 10s for voice including ASR)

---

## 1.9 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Twilio sandbox limits (1 msg/sec, template-only outbound) | Slow dev testing | Use webhook replay tools; upgrade to paid early |
| Whisper accuracy on accented Indic speech | Poor transcripts | Benchmark Whisper vs IndicWav2Vec; fallback to larger model |
| GPU unavailable locally | Can't run Whisper | Use `whisper-small` on CPU for dev; cloud GPU for prod |
| Redis message loss | Lost messages | Enable Redis persistence (AOF); add dead-letter queue |

---

## 1.10 Phase 1 Exit Criteria

Before moving to Phase 2, ALL of the following must be true:

- [ ] WhatsApp webhook is operational and validated
- [ ] Message queue reliably routes text and voice messages
- [ ] ASR pipeline produces usable transcripts in at least 2 Indic languages
- [ ] All messages are logged in PostgreSQL with correct metadata
- [ ] Media files are stored in object storage
- [ ] Docker Compose environment is reproducible
- [ ] At least 15 unit/integration tests pass
- [ ] README with setup instructions is complete
