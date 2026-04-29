# TradesBot 🛠️🤖

An AI-powered AI assistant and CRM platform designed specifically for tradespeople (plumbers, electricians, carpenters, etc.). TradesBot integrates directly with WhatsApp to handle customer inquiries, quoting, and scheduling via text and voice notes.

## 🌟 Key Features

*   **WhatsApp Business Integration**: Direct communication with customers where they already are.
*   **Voice-to-Text Pipeline (ASR)**: Uses OpenAI's Whisper model to transcribe incoming voice notes in multiple languages (English, Hindi, Tamil, Malayalam).
*   **Event-Driven Architecture**: Scalable message processing using Redis and robust task queuing.
*   **Intelligent Routing & AI**: Leverages LangChain and Groq to understand customer intent, draft quotes, and schedule appointments.
*   **Cross-Platform Mobile App**: Includes a Flutter-based mobile application for tradespeople to manage their business on the go.

## 🏗️ Architecture & Tech Stack

### Backend (`/tradesbot`)
*   **Framework**: FastAPI (Python 3.11+)
*   **Database**: PostgreSQL 16 (with asyncpg & SQLAlchemy)
*   **Message Queue**: Redis 
*   **Storage**: MinIO / AWS S3 for media storage
*   **AI & ML**: LangChain, Groq, ChromaDB, HuggingFace (Whisper)
*   **Containerization**: Docker & Docker Compose

### Mobile App (`/tradesbot_mobile`)
*   **Framework**: Flutter (Dart)
*   **Platforms**: Android, iOS, Web, Windows, macOS, Linux

## 📂 Project Structure

```
.
├── tradesbot/                  # FastAPI Backend Services
│   ├── app/                    # Core application logic
│   ├── db/                     # Database migrations
│   ├── k8s/                    # Kubernetes manifests
│   ├── tests/                  # Backend tests
│   ├── docker-compose.yml      # Local dev environment
│   └── requirements.txt        # Python dependencies
├── tradesbot_mobile/           # Flutter Mobile Application
│   ├── lib/                    # Dart source code
│   ├── android/                # Android platform code
│   ├── ios/                    # iOS platform code
│   └── pubspec.yaml            # Flutter dependencies
├── phase-*.md                  # Project Planning & Architecture Docs
└── deep-research-report.md     # In-depth technical research & strategy
```

## 🚀 Getting Started

### Prerequisites
*   Docker & Docker Compose
*   Python 3.11+
*   Flutter SDK

### Running the Backend (Local Dev)
1. Navigate to the backend directory: `cd tradesbot`
2. Copy the environment template: `cp .env.example .env` (and fill in your Twilio/Groq keys)
3. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. The API will be available at `http://localhost:8000`

### Running the Mobile App
1. Navigate to the mobile app directory: `cd tradesbot_mobile`
2. Install dependencies:
   ```bash
   flutter pub get
   ```
3. Run the app on your preferred device:
   ```bash
   flutter run
   ```

## 📝 Roadmap
- [x] **Phase 1**: Foundation & Core Infrastructure (WhatsApp Webhook, ASR Pipeline, Postgres+Redis setup)
- [ ] **Phase 2**: AI Agents, Quoting, and Scheduling (LangChain Integration, PDF Generation)
- [ ] **Phase 3**: Follow-ups, Voice Outbound, and Marketing
- [ ] **Phase 4**: Localization & Multi-language Support
- [ ] **Phase 5**: Testing, Scaling, and Rollout

---
*Built to empower local trades businesses with cutting-edge AI.*
