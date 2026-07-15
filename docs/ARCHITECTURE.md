# System Architecture

## 1. Context

```text
                    +-----------------------+
Public Sources ---->| Collector Adapters    |
                    +-----------+-----------+
                                |
User / Scheduler -> FastAPI -> Application Services -> Asset Repository -> SQLite
                                |          |
                                |          +-> LLM Adapter -> OpenAI
                                +------------> Vector Adapter -> ChromaDB
                                             |
Next.js Dashboard <--------- Read Projections / Asset API
```

The application core owns the Asset lifecycle. Collectors, OpenAI, Chroma, SQLite, scheduling, and HTTP are replaceable boundary adapters.

Source connectors are registered independently in `SourceRegistry`. Operational subscription state, authentication readiness, health, and last errors live outside the Asset model; every item produced by a connector is normalized into an Asset with source-level provenance.

`SourceSnapshot` caches a successful connector result by source, local date, and configuration hash. Snapshot records reference canonical Asset IDs instead of copying source content. A same-day brief can therefore reuse existing sources, collect only newly enabled sources, and still rerank the combined evidence before synthesis.

## 2. Folder Structure

```text
freja-personal-ai-os/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # HTTP transport
│   │   ├── core/                # configuration and logging
│   │   ├── db/                  # engine and declarative base
│   │   ├── models/              # persistence entities
│   │   ├── repositories/        # database queries
│   │   ├── schemas/             # external contracts
│   │   └── services/            # use cases, LLM, vector, scheduler, collectors
│   └── tests/
├── frontend/
│   ├── app/                     # Next.js app router
│   ├── components/ui/           # shadcn-style primitives
│   ├── components/              # product surfaces
│   ├── lib/                     # API and utilities
│   └── public/                  # original product artwork
├── docs/
└── docker-compose.yml
```

## 3. Asset Model and Database Schema

```text
assets
  id                UUID string, primary key
  type              enum-like discriminator
  status            inbox | active | archived
  title             common display identity
  content           canonical body or Markdown
  summary           optional derived summary
  source/source_id  provenance and idempotency key (unique pair)
  url               canonical external location
  language          BCP-47-like short code
  tags              JSON list
  metadata          JSON object for type-specific fields
  parent_id         optional self-reference
  embedding_id      vector-store reference
  occurred_at       source event time
  created_at        ingestion time
  updated_at        last mutation time
```

Core indexes cover type/time, source identity, status, parent, and creation time. The next schema migration introduces `asset_relations(from_id, to_id, kind, weight, evidence, created_at)` once relationship discovery has a real consumer. Keeping that edge table out of Sprint 1 avoids a speculative graph abstraction.

### Metadata contracts

| Asset type | Example metadata |
|---|---|
| idea | `category`, `captured_via` |
| news | `publisher`, `score`, `comments`, `subreddit` |
| repository | `period`, later `stars`, `language`, `owner` |
| brief | `item_ids`, `collector_count`, later prompt/model provenance |
| task | `due_at`, `priority`, `completed_at` |

Metadata should be promoted to a real column only when it becomes cross-type, indexed, or part of a stable invariant.

## 4. Key Flows

### Idea capture

1. Validate free text.
2. Classify title/category/tags with OpenAI or deterministic fallback.
3. Persist Asset transactionally.
4. Generate embedding when configured and upsert into Chroma.
5. Return the canonical Asset; vector failure is logged but does not roll back knowledge.

### Daily brief

1. Scheduler or API starts the job.
2. Collectors execute concurrently and fail independently.
3. Normalize all results into `CollectedItem` values.
4. Deduplicate by `(source, source_id)` and persist source Assets.
5. Rank signals, ask the LLM for Chinese Markdown, and persist a Brief Asset referencing item IDs.

## 5. Architecture Decisions

- **Asset-first:** gives every future agent the same lifecycle, provenance, indexing, and relationship surface.
- **JSON metadata:** enables early type growth without dozens of sparse tables; schemas must become versioned as contracts mature.
- **SQLAlchemy:** keeps the repository portable to PostgreSQL while SQLite remains operationally simple.
- **Graceful AI degradation:** the OS must retain memory even when an external intelligence provider is unavailable.
- **Background task now, durable queue later:** FastAPI tasks and APScheduler are enough for one local process; a job table plus worker queue is required before multi-instance deployment.

## 6. Production Evolution

- Add Alembic before the first schema change.
- Add a durable `ingestion_runs` model, retry policy, per-source rate budgets, metrics, and OpenTelemetry.
- Add authentication and encrypted secret storage before remote access.
- Move SQLite to PostgreSQL when concurrent writers or remote deployment appear.
- Replace in-process jobs with a worker and outbox when work must survive process restarts.
