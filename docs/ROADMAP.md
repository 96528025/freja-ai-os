# Development Roadmap and Future Vision

## Active Product Phase: Brief Quality

The active scope is defined in [CURRENT_FOCUS.md](CURRENT_FOCUS.md). Freja currently exposes one complete loop only: select sources, generate a Chinese AI brief, read the summary, and open the original items.

Before starting another product module, this phase prioritizes:

1. Connector reliability and authentication recovery for Reddit and Rednote.
2. Source-level observability, freshness, and accurate engagement metadata.
3. Brief ranking, deduplication, citation, and quality evaluations.
4. Generation progress, cancellation, history, and failure reporting.
5. Twitter / X and LinkedIn only after a compliant, verified acquisition path exists.

The original Sprint 2-10 roadmap below is retained as a deferred direction, not an active implementation queue. Idea Inbox, Library, Research, Career, Learning, Creative, Life OS, knowledge graph, and multi-agent work must not displace brief quality until the current loop is dependable in regular use.

## Roadmap Principles

1. Every agent reads and writes Assets through published services.
2. Provenance is mandatory; generated claims retain evidence asset IDs.
3. Human attention is the scarce resource. Proactivity must be relevant, bounded, and dismissible.
4. Autonomy increases only after evaluation, observability, permissions, and reversible execution exist.
5. Local-first ownership remains the default even when remote infrastructure is introduced.

## Deferred Sprint 2: Source Agents

Turn collectors into independently deployable Reddit, X/Twitter, GitHub, YouTube, RSS, paper, and podcast agents. Add ingestion runs, checkpoints, quotas, source health, transcripts, and agent-specific metadata schemas.

## Deferred Sprint 3: Long-term Memory

Add versioned embeddings, hybrid search, explicit and inferred `asset_relations`, relationship evidence, automatic tagging, entity resolution, personal timeline, and retention controls. Deliver explainable retrieval, not a black-box memory score.

## Deferred Sprint 4: Research Agent

Given an Idea Asset, plan queries; collect web, repository, paper, startup, and competitor Assets; compare evidence; and publish a cited Research Asset. Add source quality scoring, claim-level citations, evaluation fixtures, and review checkpoints.

## Deferred Sprint 5: Career Agent

Track job, internship, company, recruiter, resume, and interview Assets. Add deduped opportunity timelines, fit signals, application state, deadline tasks, and private document controls. LinkedIn access must use supported, consented integrations.

## Deferred Sprint 6: Learning Agent

Create study plans, learning paths, flashcards, quizzes, and progress Assets from knowledge gaps. Introduce spaced repetition, prerequisite relationships, assessment history, and learning outcome metrics.

## Deferred Sprint 7: Creative Agent

Generate project, hackathon, business, startup, and content Ideas grounded in the user's existing interests. Add novelty checks against prior Assets, feasibility dimensions, structured critique, and incubation states.

## Deferred Sprint 8: Life OS

Add permissioned connectors for calendar, reminders, travel, dance, tennis, finance, shopping, and fitness. Separate sensitive data classes, encrypt credentials, require confirmation for writes or purchases, and provide per-domain retention settings.

## Deferred Sprint 9: Multi-Agent System

Introduce Planner, Researcher, Writer, Reviewer, Critic, Memory, and Executor roles behind a durable orchestration protocol. Plans, tool calls, observations, reviews, and artifacts are all Assets. Add budgets, cancellation, idempotency, audit trails, sandboxed tools, and regression evaluations.

## Deferred Sprint 10: Personal AI Operating System

Deliver continuous planning, learning, research, and knowledge-graph maintenance with morning briefs, weekly reviews, monthly reviews, and quarterly reviews. Suggestions use an attention budget and expose why-now reasoning, evidence, confidence, expected value, and a dismiss/snooze mechanism.

## Future Vision

Freja becomes a durable personal context layer rather than another destination app. It remembers where an idea came from, how it changed, what evidence supports it, which projects it influenced, and when it becomes useful again. Agents operate on the same memory substrate and can collaborate without creating isolated silos.

The mature system has three planes:

- **Knowledge plane:** assets, versions, provenance, relationships, embeddings, policies.
- **Intelligence plane:** retrieval, ranking, research, synthesis, planning, evaluation.
- **Action plane:** permissioned connectors, tasks, schedules, confirmations, audit and rollback.

The product succeeds when it quietly improves decisions over years while preserving user control, inspectability, and ownership.
