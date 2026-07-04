# Knovara

Knovara is an AI-powered technical ramp-up copilot for engineering onboarding. It helps new engineers understand a team's systems, decisions, documents, and people by turning scattered knowledge into focused briefings and cited answers.

The current version is a local portfolio demo: it runs without private company data or an API key, while keeping the backend contracts ready for retrieval and LLM integration.

## What It Demonstrates

- Full-stack product flow with a Next.js frontend and FastAPI backend
- Role-aware onboarding briefings for new engineers
- Grounded Q&A responses with source citations and follow-up questions
- Typed API contracts for mentor and chat workflows
- A retrieval abstraction that can be connected to indexed documents or repositories
- Local-first development with Docker-compatible service boundaries

## Product Flow

1. A user describes their role, team, background, and onboarding goal.
2. Knovara builds a first-week briefing with concrete learning tasks, recommended sources, and people to meet.
3. The user asks engineering questions in the chat surface.
4. The backend returns a concise answer with citations so the user can verify the source context.

## Architecture

```text
frontend/
  app/              Next.js app router pages
  lib/api.ts        Typed client for backend calls

backend/
  main.py           FastAPI app and routes
  mentor.py         Personalized onboarding briefing logic
  chat.py           Grounded Q&A response logic
  retrieval.py      Source search abstraction
  ingest.py         Document loading and chunking utilities
  models.py         Shared ingestion models
```

## Run Locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The demo works without `OPENAI_API_KEY`. Adding a key prepares the environment for replacing the deterministic demo responses with live LLM calls.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## API Endpoints

- `GET /health` checks backend status and whether the backend is in demo or LLM-ready mode.
- `GET /sources` returns representative source chunks.
- `POST /mentor` builds a personalized onboarding briefing.
- `POST /chat` answers an engineering question with citations.

## Validation

```bash
cd frontend
npm run build
```

```bash
cd backend
python -m compileall .
```

## Next Steps

- Connect `retrieval.py` to Chroma-backed document search.
- Replace deterministic demo generation with OpenAI chat completions.
- Add ingestion status endpoints and a reviewer-friendly seed dataset.
- Add backend tests for the mentor, chat, and retrieval contracts.
