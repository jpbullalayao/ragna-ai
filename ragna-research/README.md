# ragna-research

Eve project for **Ragna AI**, an agent that runs **daily research** on topics you define (via schedules or prompts) and **publishes notes** to external notes apps. Notion is the first destination; additional adapters plug in under `agent/lib/notes/destinations/`.

This directory is the **Vercel deploy root** for the agent (run `eve link` and `eve deploy` from here). The package/project name is `ragna-research`; the agent’s identity is **Ragna AI**.

## Prerequisites

- Node.js 24.x
- [Vercel CLI](https://vercel.com/docs/cli) for linking and deploy (`npm i -g vercel`)
- Notion Internal Integration: `NOTION_API_KEY`, `NOTION_PARENT_PAGE_ID` (parent page shared with the integration)
- AI Gateway: `AI_GATEWAY_API_KEY` or Vercel OIDC (`VERCEL_OIDC_TOKEN` via `vercel env pull`)

## Local development

```bash
cd ragna-research
cp .env.example .env.local
# Edit .env.local — Notion + gateway credentials
npm install
npm run dev
```

Inspect discovered capabilities:

```bash
npm exec -- eve info
```

Trigger the daily investment schedule once (dev only). Run **one** trigger at a time while the previous session finishes; overlapping runs can stall the local workflow queue.

```bash
curl -X POST http://localhost:2000/eve/v1/dev/schedules/daily_investment_research
```

Browser tools use Eve’s **default sandbox** (`defaultBackend()` — typically Docker when the daemon is running, otherwise microsandbox or just-bash). Run **one** schedule trigger at a time so the local workflow queue does not overlap runs.

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Local Eve dev server + TUI |
| `npm run build` | Production build |
| `npm run deploy` | Deploy to Vercel production via `eve deploy` |
| `npm run typecheck` | TypeScript check |

## Architecture

- **Schedules** — `agent/schedules/*` kick off runs; workflow lives in matching skills
- **Skill** — `agent/skills/daily_investment_research/` (Reddit stock pulse for casual investors)
- **Research** — `agent/extensions/browser.ts` (agent-browser)
- **Publish** — `agent/tools/publish_note.ts` → `agent/lib/notes/registry.ts` → destinations (Notion today)

To add another notes app: implement `NotesDestination` in `agent/lib/notes/destinations/`, register it in `registry.ts`.

## Repo context

The parent [ragna-ai](../) repository also ships personal agent **skills** for [skills.sh](https://skills.sh) under `skills/`. That tree is independent of this Eve runtime.
