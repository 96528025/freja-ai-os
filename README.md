# Freja Personal AI OS

Freja is an asset-first personal AI operating system. Its current product focus is one dependable workflow: select trusted sources, generate a Chinese AI brief, read the summary, and open the original items. Broader personal knowledge capabilities are documented but intentionally deferred; see [`docs/CURRENT_FOCUS.md`](docs/CURRENT_FOCUS.md).

Sprint 1 is recorded in [`docs/SPRINT_1.md`](docs/SPRINT_1.md), including the product pipeline, source contracts, daily snapshots, automation, verification baseline, and deferred backlog.

## Architecture Principle

**Everything is an Asset.** Ideas, news, briefs, repositories, research, notes, documents, and tasks share one durable domain model. Type-specific fields live in validated metadata; common lifecycle, provenance, search, and relationships stay consistent.

## Quick Start

### Docker Compose

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Open the dashboard at `http://localhost:3000` and API documentation at `http://localhost:8000/docs`.

### Local Development

Backend (Python 3.11+):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend (Node 20+):

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

`OPENAI_API_KEY` is optional. Without it, Freja still captures ideas, applies deterministic tags, stores local feature-hash embeddings in Chroma, collects sources, creates a link-based brief, and uses lexical search. With it, Freja adds semantic classification, Chinese synthesis, deduplication, and OpenAI embeddings stored through ChromaDB.

## Main API

- `POST /api/v1/assets/ideas` captures and enriches an idea.
- `GET /api/v1/assets?query=...&type=idea` searches assets.
- `GET /api/v1/dashboard` returns dashboard projections.
- `POST /api/v1/briefs/generate` starts collection and brief generation.
- `GET /api/v1/briefs/today` returns today's brief.

## Operations

- The scheduler runs every day at `BRIEF_HOUR:BRIEF_MINUTE` in `TIMEZONE`.
- SQLite and Chroma files live under `backend/data` locally and in the `freja_data` volume under Docker.
- Every collector is isolated. One unavailable source is logged and skipped without failing the whole brief.
- Source choices are persisted in SQLite and managed from the Dashboard's **Sources** panel. Available connectors include granular official blogs, GitHub Trending, Claude Code and Codex release feeds; community connectors expose their authentication state.
- FastAPI exposes OpenAPI at `/docs` and `/openapi.json`.

## Verification

```bash
cd backend && pytest
cd frontend && npm run build
```

Product and engineering specifications are in [`docs/`](./docs).
