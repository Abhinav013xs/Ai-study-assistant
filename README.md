# AI-Powered Study Assistant Platform

A production-grade, commercializable monorepo containing a full-stack educational SaaS platform that allows students to upload study materials (PDFs, PPTs, DOCX files, handwritten notes, images) and interact with them using AI-powered RAG chat, dynamic quiz generation, flashcard reviews (spaced repetition via SM-2), custom notes generation, and study planner calendars.

---

## Technical Stack & Architecture

- **Frontend**: Next.js App Router, TypeScript, Tailwind CSS, Framer Motion animations.
- **Backend**: FastAPI (Python), SQLAlchemy ORM, SQLite (local development) and PostgreSQL (production).
- **Vector Ingestion**: ChromaDB vector database with custom metadata scopes.
- **AI Integrations**: Gemini API (default multimodal driver for OCR, Embeddings, Chat, Quiz Generation) and fallback drivers for OpenAI/Claude.
- **DevOps**: Docker, Docker Compose orchestration, PostgreSQL and Redis service containers.

---

## Folder Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # Route versioning and dependency injections
│   │   ├── core/         # Settings, Security (Direct bcrypt/JWT), Config
│   │   ├── db/           # Session management
│   │   ├── models/       # Declarative SQLAlchemy database schemas
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # RAG, OCR, SM-2 Flashcards, Quiz Grader, Adaptive Planner
│   │   └── main.py       # FastAPI Entrypoint
│   ├── tests/            # pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js pages (Unified SaaS SPA page.tsx)
│   ├── lib/              # API clients
│   ├── Dockerfile
│   └── tsconfig.json
├── docker-compose.yml    # Database, Redis, and multi-service orchestrator
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python (3.11+)
- Docker & Docker Compose (optional, for deployment)

### 1. Backend Configuration
Navigate to `/backend`:
```bash
cd backend
python -m venv venv
source venv/Scripts/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `/backend` directory:
```env
DATABASE_URL=sqlite:///./study_assistant.db
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=generate_a_random_jwt_secret_key_here
```

Start the backend locally:
```bash
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation will be live at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Configuration
Navigate to `/frontend`:
```bash
cd ../frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the SaaS dashboard.

---

## Verification & Testing

To run the automated Python backend tests verifying the spaced repetition algorithms:
```bash
cd backend
pytest tests/
```

---

## Production Deployment via Docker Compose

To containerize and run the entire stack (Postgres database, Redis cache, FastAPI app, and Next.js frontend):
1. Configure environment keys inside `docker-compose.yml` or set them on host variables.
2. Build and launch:
```bash
docker compose up --build
```
This maps:
- Frontend Client: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Postgres Database: `http://localhost:5432`
