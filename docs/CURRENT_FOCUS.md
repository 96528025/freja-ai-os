# Current Product Focus

## Decision

As of 2026-07-16, Freja has one active product feature:

> Generate a trustworthy, concise, adaptive Chinese AI brief from user-selected sources, with direct access to every original item.

The active product loop is deliberately limited to:

1. Select sources.
2. Generate the brief.
3. Read the Chinese summary.
4. Open the original source.
5. Rate individual items and the overall edition.

This document overrides the broader Sprint 1 user interface described in earlier planning documents. The Asset architecture remains intact, but capabilities outside this loop are not part of the current product surface.

## In Scope

### Source control

- Show implemented sources grouped as community, official, and code sources.
- Allow independent selection, select all, and clear all.
- Select all includes only connectors that are currently usable.
- Hide planned connectors until they have a verified collection path.
- Persist selection and show connector health without fabricating availability.

### Brief generation

- Collect only enabled sources.
- Isolate collector failures so one source cannot cancel the entire brief.
- Deduplicate source items and persist provenance.
- Apply a hard recency policy: prioritize the latest 72 hours, use 3–7 day items only as fallback, and reject older items.
- Rank signals using freshness, source credibility, recorded engagement, and learned user preferences.
- Send at most five candidates to the editorial model and allow a shorter final brief.
- Limit one source to at most three selected candidates.
- Generate a Chinese Markdown brief with the configured OpenAI model.
- Support both manual regeneration and the existing local schedule.
- Never invent engagement metrics. Missing values remain missing.
- Reddit items must be no older than 72 hours. An older thread may return only when a future collector can prove recent activity from comment timestamps or count deltas.
- A large lifetime comment total is not evidence of current activity.
- Reuse successful per-source snapshots within the same local date and configuration.
- When a source is enabled later that day, collect only that source and rerank the combined evidence.
- Run a missing daily edition at 07:00 PT or during backend startup catch-up.

The normative ranking and feedback behavior is documented in [BRIEF_RANKING_AND_FEEDBACK.md](BRIEF_RANKING_AND_FEEDBACK.md).

### Brief reading

- Make the current brief the primary reading surface.
- Display generation time and contributing item count when available.
- Open original links in a new browser tab.
- Preserve source URLs and contributing Asset IDs for auditability.
- Provide clear loading, empty, offline, and generation error states.
- Place item-level feedback beside the item it affects.
- Persist 1–5 whole-brief satisfaction for longitudinal quality evaluation.

## Current Source Scope

| Source | Acquisition | Current status |
|---|---|---|
| Reddit | OpenCLI using an authenticated Chrome session | Active |
| OpenAI Blog | RSS | Active |
| Anthropic Blog | RSS | Active |
| Google DeepMind Blog | RSS | Active |
| Cursor Changelog | RSS | Active |
| Claude Code | GitHub Releases Atom | Active, user-selectable |
| Codex | GitHub Releases Atom | Active, user-selectable |
| GitHub Trending | Public HTML | Active |
| Twitter / X | No verified connector | Deferred and hidden |
| LinkedIn | No verified connector | Deferred and hidden |

Hacker News is not part of the current source registry.

## Deferred Product Surface

The following capabilities are intentionally removed from the current dashboard. Existing backend code or stored data may remain so that no user data is destroyed.

| Capability | Current treatment | Re-entry requirement |
|---|---|---|
| Idea Inbox | Hidden | Brief workflow is stable and idea capture has a validated daily use case |
| Latest Ideas | Hidden | Idea Inbox returns with a complete browse-and-retrieve workflow |
| Knowledge statistics | Hidden | Counts support a concrete decision rather than decoration |
| Library | Hidden | Search, filters, detail view, and source navigation are complete |
| Semantic search / Chroma UI | Backend retained, UI deferred | Retrieval quality can be evaluated against a real corpus |
| Research Agent | Deferred | Source quality and provenance pass brief evaluations first |
| Archive | Hidden | Brief history navigation and retention behavior are implemented |
| Tasks and calendar | Hidden | There is a permissioned write path and an actual task workflow |
| Knowledge graph | Deferred | Relations have evidence and a user-facing retrieval use case |
| Global search | Hidden | Search results lead to complete Asset detail pages |
| Multi-agent system | Deferred | Single brief pipeline has observability, evaluations, and reliability targets |

## Quality Bar

The focused feature is ready for regular use only when:

- Source selection is persistent and batch controls are reliable.
- Every visible metric comes from collector data.
- Every summarized item has a working original URL.
- Reddit authentication failures are visible and recoverable.
- Every selected news item is no older than seven days, and fallback use is auditable.
- The brief contains no more than five candidate-backed entries and may be shorter after editorial deduplication.
- Item feedback changes later ranking in an explainable way.
- A failed connector is reported without blocking successful connectors.
- Manual generation exposes an unambiguous in-progress state and completion result.
- Desktop and mobile layouts have no clipped controls or horizontal overflow.
- Unit, type, and browser tests cover the core loop.

## Architecture Boundary

“Everything is an Asset” remains the long-term architecture rule. In the current focus, it is an implementation boundary rather than a collection of visible features:

- Collected items are Assets.
- Generated briefs are Assets.
- Provenance and source metadata stay attached to Assets.
- Idea, research, task, document, and relationship workflows remain dormant until deliberately resumed.

No deferred Asset data should be deleted as part of interface simplification.
