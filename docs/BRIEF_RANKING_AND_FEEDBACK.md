# Brief Ranking and Feedback

**Current policy:** 2026-07-16

Freja's daily brief is a rule-constrained recommendation pipeline followed by an LLM editorial pass. The model never receives the full unfiltered feed and does not choose sources on its own.

```text
enabled sources
  -> collection and source snapshots
  -> provenance deduplication
  -> recency tiers
  -> explainable preference score
  -> source diversity and five-item cap
  -> LLM deduplication and Chinese editing
  -> per-item feedback for the next run
```

## 1. Candidate scope

Only enabled source subscriptions are collected. The current implemented sources are:

- Reddit through an authenticated OpenCLI Chrome session.
- OpenAI Blog, Anthropic Blog, Google DeepMind Blog, and Cursor Changelog through RSS.
- Claude Code and Codex through GitHub Releases Atom feeds.
- GitHub Trending through its public daily page.

Twitter / X and LinkedIn remain planned and hidden. Rednote / Xiaohongshu is not part of the current product source registry.

Each collector returns at most `COLLECTOR_LIMIT` items per run, currently 12. Items are deduplicated by `(source, source_id)` and persisted as Assets. Successful source results are cached by local date and connector configuration; `force_refresh=true` bypasses that cache.

## 2. Recency policy

Candidates are split before recommendation scoring:

1. **Fresh tier:** published within `BRIEF_FRESH_HOURS`, currently 72 hours.
2. **Fallback tier:** older than 72 hours but no older than `BRIEF_MAX_AGE_DAYS`, currently 7 days.
3. **Expired:** older than 7 days and always excluded.

The fresh tier is ranked first. The fallback tier is considered only when fewer than `BRIEF_MAX_ITEMS` fresh items survive ranking. Ordinary undated news is excluded. GitHub Trending is treated as a same-day signal and may use its collection timestamp because the page itself represents a daily ranking.

The brief may contain fewer than five items. Old or weak content is never inserted only to fill the quota.

## 3. Explainable ranking score

Within each recency tier, every candidate receives:

```text
score = engagement
      + source credibility
      + freshness
      + learned topic preference
      + learned source preference
      + learned term preference
      + learned quality adjustment
```

- **Engagement:** `log1p(points + score + likes + comments * 0.5) * 4`. Missing metrics contribute zero.
- **Credibility:** implemented official sources receive `+7`; other sources receive `+2`. When only official sources are enabled, this is a shared baseline and does not determine their relative order.
- **Freshness:** starts at 12 and declines by 1.5 per day, never below zero.
- **Topic preference:** learned topic weights are multiplied by 4.
- **Source preference:** learned source weights are multiplied by 3.
- **Term preference:** learned keyword weights are multiplied by 1.5 and clamped to `[-24, 18]`.
- **Quality adjustment:** prior `too_marketing` and `too_basic` feedback penalizes matching content patterns.

Previously disliked Asset IDs are excluded. At most three items from one source may enter the selected set. The deterministic recommender sends no more than `BRIEF_MAX_ITEMS`, currently 5, to the LLM.

## 4. LLM editorial contract

The LLM may remove or merge selected candidates, so the rendered brief can contain fewer than five entries. It must:

- produce concise Chinese Markdown;
- merge semantic duplicates, including adjacent release versions;
- retain original links and explicit publication dates when provided;
- explain what happened and why it matters;
- add an action only when the evidence supports one;
- distinguish source-platform metrics from original-site metrics;
- avoid invented dates, authors, popularity, evaluations, and facts;
- avoid presenting 3–7 day fallback items as newly published;
- prefer omission over padding.

## 5. Feedback learning

Each rendered item exposes `interested` and `not_interested`. Negative feedback can include:

- `not_relevant`
- `too_basic`
- `too_marketing`
- `repetitive`
- `source_not_useful`
- `other`

Positive feedback adds `+1.0`; negative feedback adds `-1.5`, so explicit rejection has greater influence. Reasons apply focused multipliers:

- `not_relevant` doubles the topic adjustment.
- `source_not_useful` doubles the source adjustment.
- `repetitive` multiplies term adjustment by 1.75.
- `too_marketing` and `too_basic` activate quality-pattern penalties.

The preference profile is rebuilt from persisted item feedback on every generation. This is an explainable online preference model, not model fine-tuning.

The 1–5 whole-brief satisfaction score is persisted and exposed in the preference profile for longitudinal evaluation. It does not currently change item ranking directly.

## 6. Traceability

Every Brief Asset stores:

- selected `item_ids`;
- total collected candidate count;
- fresh, fallback, eligible, and fallback-selected counts;
- the active recency policy;
- source snapshot usage;
- the preference profile summary used for that run.

This metadata makes a recommendation auditable without relying on the generated prose.
