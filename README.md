# Freja Personal AI OS

Freja is an asset-first personal AI operating system. Its current product focus is one dependable, adaptive workflow: select trusted sources, generate a concise Chinese AI brief, read original items, and teach the next edition with explicit feedback. Broader personal knowledge capabilities are documented but intentionally deferred; see [`docs/CURRENT_FOCUS.md`](docs/CURRENT_FOCUS.md).

Sprint 1 is recorded in [`docs/SPRINT_1.md`](docs/SPRINT_1.md). The current ranking and learning contract is specified in [`docs/BRIEF_RANKING_AND_FEEDBACK.md`](docs/BRIEF_RANKING_AND_FEEDBACK.md).

## Current Brief Contract

- Only user-enabled sources enter the candidate pool.
- News from the last 72 hours is ranked first; 3–7 day items are fallback-only; older items are excluded.
- At most five candidates reach the editorial model, and the final brief may be shorter.
- At most three candidates may come from one source.
- Per-item interest feedback updates topic, source, keyword, and quality weights for later editions.
- Every brief preserves source links, contributing Asset IDs, recency counts, snapshot usage, and the preference profile used for ranking.
- Internal code and data retain the Freja name; the demo-facing UI displays **Personal AI**.

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
- `GET /api/v1/briefs/{brief_id}/feedback` returns item and satisfaction feedback state.
- `PUT /api/v1/briefs/{brief_id}/items/{asset_id}/feedback` records or clears item feedback.
- `PUT /api/v1/briefs/{brief_id}/feedback` records the 1–5 brief satisfaction score.
- `GET /api/v1/briefs/preferences/profile` returns the learned profile summary.

## Operations

- The scheduler runs every day at `BRIEF_HOUR:BRIEF_MINUTE` in `TIMEZONE`.
- SQLite and Chroma files live under `backend/data` locally and in the `freja_data` volume under Docker.
- Every collector is isolated. One unavailable source is logged and skipped without failing the whole brief.
- Source choices are persisted in SQLite and managed from the Dashboard's **Sources** panel. Available connectors include Reddit, granular official blogs, GitHub Trending, Claude Code, and Codex release feeds. Reddit exposes its OpenCLI Chrome authentication state. Rednote / Xiaohongshu is not in the current registry.
- FastAPI exposes OpenAPI at `/docs` and `/openapi.json`.

## Verification

```bash
cd backend && pytest
cd frontend && npx tsc --noEmit
```

Product and engineering specifications are in [`docs/`](./docs).
