# API Design and UI Wireframes

## 1. API Design

Base path: `/api/v1`. FastAPI generates the normative OpenAPI contract at `/openapi.json`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/assets` | Create a normalized Asset from a trusted client |
| `POST` | `/assets/ideas` | Capture and enrich free-form idea text |
| `GET` | `/assets` | Search/filter/paginate assets |
| `GET` | `/assets/{id}` | Read one asset |
| `GET` | `/briefs/today` | Read today's Brief Asset |
| `POST` | `/briefs/generate` | Queue one cached collection and synthesis run; `force_refresh=true` bypasses daily snapshots |
| `GET` | `/briefs/{brief_id}/feedback` | Read item feedback and whole-brief satisfaction |
| `PUT` | `/briefs/{brief_id}/items/{asset_id}/feedback` | Set or clear interested/not-interested item feedback |
| `PUT` | `/briefs/{brief_id}/feedback` | Record a 1–5 satisfaction score and optional note |
| `GET` | `/briefs/preferences/profile` | Read learned preference and satisfaction summary |
| `GET` | `/sources` | List connector configuration, availability, and health |
| `PATCH` | `/sources` | Select or clear all currently usable sources |
| `PATCH` | `/sources/{id}` | Enable or disable one source |
| `GET` | `/dashboard` | Load the local dashboard projection |
| `GET` | `/health` | Process health check |

### Examples

```json
POST /api/v1/assets/ideas
{"content":"我有一个想法：做一个针对论文阅读的个人研究 Agent"}
```

```json
{
  "id": "asset-uuid",
  "type": "idea",
  "status": "active",
  "title": "做一个针对论文阅读的个人研究 Agent",
  "content": "我有一个想法：做一个针对论文阅读的个人研究 Agent",
  "tags": ["ai", "product"],
  "metadata": {"category": "ai", "captured_via": "inbox"},
  "created_at": "2026-07-14T15:00:00Z"
}
```

Errors use `{"detail":"..."}` and standard HTTP status codes. Pagination uses `limit` and `offset`; a cursor should replace offsets after the local library reaches sustained high write volume.

## 2. Focused Brief Workspace

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Personal AI                                             local date   │
├──────────────────────────────────────────────────────────────────────┤
│ YOUR AI DAILY BRIEF                                                  │
│ Select sources → collect and rank → read summary → open original     │
│                                                                      │
│ ┌─ SELECT SOURCES ───────────────────── [all] [none] ──────────────┐ │
│ │ Community       □ Reddit                                         │ │
│ │ Official        □ OpenAI              □ Anthropic                │ │
│ │                 □ DeepMind            □ Cursor                   │ │
│ │                 □ Claude Code         □ Codex                    │ │
│ │ Code            □ GitHub Trending                               │ │
│ │                                            [Generate brief]       │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ TODAY'S BRIEF                                  generated time · count │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Chinese Markdown summary                                         │ │
│ │ linked item title ↗                                              │ │
│ │ source · verified metrics                                        │ │
│ │ why it matters · publication date · original link                │ │
│ │ [interested] [not interested: reason]                            │ │
│ └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Responsive behavior

- Desktop uses one centered work surface with two-column source rows and a constrained reading measure.
- Mobile stacks source rows and makes the generate command full width.
- The workflow has no drawer, inactive navigation, statistics, or secondary product modules.
- Controls retain stable touch targets and the document has no horizontal overflow.

### States

- Loading: localized spinner without replacing the full shell.
- Empty: source selection and one direct generate action.
- Offline: persistent, non-blocking connection notice.
- Generating: persistent progress state while collection, ranking, and synthesis run.
- Complete: scroll to the new brief and render every original link in a new tab.
- Feedback: item controls render directly under the matching linked item; whole-brief satisfaction follows the edition.
- Error: keep the selected sources and show a retryable inline message.
- Reduced motion: transitions and animations are disabled through media query.
