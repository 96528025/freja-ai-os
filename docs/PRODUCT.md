# Freja Product Requirements and SRS

> **Current scope notice (2026-07-14):** The active product experience is limited to source selection, brief generation, summary reading, and opening original sources. See [CURRENT_FOCUS.md](CURRENT_FOCUS.md). The broader requirements below document retained architecture and deferred capabilities; they are not all active UI commitments.

## 1. Product Requirements Document

### Product statement

Freja is a long-lived personal AI operating system, not a chatbot and not a news reader. It continuously converts external signals and personal inputs into durable, searchable knowledge assets, then proactively surfaces the most relevant knowledge at the right time.

### Primary user

A technically fluent individual who follows AI, generates frequent project ideas, and needs one private workspace to preserve context over years.

### Jobs to be done

1. Understand the few AI developments that matter each morning without reading every source.
2. Capture an idea in seconds without manually filing it.
3. Find prior ideas, links, reports, and generated knowledge from one search surface.
4. See the current state of personal knowledge and pending work at a glance.

### Sprint 1 outcomes

- A morning brief can be scheduled or manually generated and is stored as an Asset.
- An idea can be captured, timestamped, tagged, categorized, embedded, and searched.
- All persisted records use the shared Asset model with provenance and metadata.
- The local dashboard exposes the brief, ideas, statistics, research, and tasks.
- The entire system starts with local tooling or Docker Compose.

The current focused release exposes only the morning brief outcome. Idea, library, research, task, statistics, archive, and knowledge graph surfaces are deferred while their underlying data is preserved.

### Non-goals

- Chat interface, autonomous browsing loops, write access to external services, multi-user tenancy, mobile apps, knowledge graph inference, and the Sprint 2-10 agents.

### Success measures

- Idea capture completes in under two seconds excluding optional LLM latency.
- Dashboard read p95 stays under 300 ms for 100,000 local assets.
- A failed collector does not prevent the daily brief from being created.
- Every generated output can be traced to its source asset IDs.
- The system remains useful when OpenAI is not configured, using deterministic local feature-hash embeddings.

## 2. Software Requirements Specification

### Functional requirements

| ID | Requirement | Acceptance |
|---|---|---|
| FR-01 | Persist every knowledge object as an Asset | No feature-specific root table is required for Sprint 1 data |
| FR-02 | Capture ideas from free text | API returns classified, timestamped Asset with tags and metadata |
| FR-03 | Collect AI signals from community, code, and first-party sources | A run records new source assets and skips known source IDs |
| FR-04 | Generate a Chinese Markdown brief | Brief Asset contains source links and contributing asset IDs |
| FR-05 | Schedule daily generation | Cron schedule uses configured local timezone |
| FR-06 | Search assets | Type-filtered lexical search works; semantic index is populated when available |
| FR-07 | Project dashboard state | One endpoint returns brief, ideas, research, tasks, and counts |
| FR-08 | Preserve provenance | External assets store source, source ID, URL, occurrence time, and raw metadata |

### Non-functional requirements

- **Maintainability:** strict service and repository boundaries; typed request/response schemas.
- **Reliability:** source isolation, idempotent source keys, explicit logs, graceful AI/vector fallback.
- **Portability:** SQLite in Sprint 1; SQLAlchemy models and JSON metadata remain PostgreSQL-compatible.
- **Privacy:** local persistence by default; only enrichment content is sent to configured AI providers.
- **Security:** secrets come from environment variables and are never written to Asset metadata.
- **Observability:** structured log context is the next production hardening step; health endpoint exists now.
- **Accessibility:** keyboard-operable actions, labeled icon buttons, semantic headings, reduced-motion support.

### Constraints and assumptions

- Public source endpoints can rate-limit or change markup.
- Reddit anonymous JSON access may be unavailable in some networks.
- Chroma's default local embedding behavior may download a model; OpenAI embeddings avoid that when configured.
- Sprint 1 is a trusted single-user local system and does not include authentication.

## 3. Sprint Plan

### Week 1: foundation

- Establish Asset schema, repositories, migrations strategy, config, logging, and test harness.
- Deliver idea capture with deterministic fallback enrichment.

### Week 2: knowledge ingestion

- Add collectors, normalization, source idempotency, ranking, LLM brief synthesis, Chroma adapter, and scheduler.
- Add contract tests and source fixtures before production hardening.

### Week 3: experience and operations

- Complete dashboard, empty/error/loading states, Docker, documentation, performance checks, and end-to-end QA.

### Definition of done

The repository starts from documented commands, tests pass, the dashboard captures an idea, a manual brief can be requested, persisted assets survive restart, OpenAPI is available, and every known limitation is documented.
