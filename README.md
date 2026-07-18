# Knovara

> Make engineers become engineers faster.

Knovara is an AI-powered technical ramp-up copilot that helps engineers understand a company's code, documentation, projects, decisions, and people so they can become productive faster.

## The Problem

New engineers spend weeks or months learning how a company works before they can contribute effectively.

Knowledge is scattered across repositories, documentation, tickets, conversations, and the minds of experienced employees.

## The Vision

Transform organizational knowledge into personalized technical mentorship.

Help every engineer understand what matters, who to learn from, and how to contribute from day one.

## Local Development

Run the backend:

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Environment

Copy `backend/.env.example` to `backend/.env`.

`OPENAI_API_KEY` is optional for the deterministic demo path. Without it:

* `/chat` uses demo fallback sources.
* `/mentor` still returns a useful deterministic briefing.
* `/ingest` returns a clear error because live embeddings require OpenAI.

With `OPENAI_API_KEY` configured:

* `POST /ingest` embeds local files into Chroma.
* `/chat` retrieves indexed chunks from the selected collection.
* `/chat` can generate an OpenAI-backed answer grounded in retrieved snippets.

Useful defaults:

```bash
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./.chroma
DEFAULT_COLLECTION=seets
CORS_ORIGINS=http://localhost:3000
```

## Demo Flow

1. Open the Index page at `/knowledge`.
2. Ingest `../example_data` into the `seets` collection.
3. Open Chat and select `seets`.
4. Ask about gateway retries, ownership, onboarding, or architecture decisions.
5. Open Mentor and generate a first-week ramp-up path.

The app shows whether answers came from demo fallback, indexed retrieval, or indexed retrieval plus OpenAI generation.
