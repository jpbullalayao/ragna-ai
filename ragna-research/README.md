# ragna-research

Eve agent that runs **daily research** on a configurable topic and **publishes notes** to external notes apps. Notion is the first destination; additional adapters plug in under `agent/lib/notes/destinations/`.

This directory is the **Vercel deploy root** for the agent (run `eve link` and `eve deploy` from here).

## Prerequisites

- Node.js 24.x
- [Vercel CLI](https://vercel.com/docs/cli) for linking and deploy (`npm i -g vercel`)
- Notion integration and Vercel project credentials — see [docs/SETUP_TODO.md](docs/SETUP_TODO.md)

## Local development

```bash
cd ragna-research
cp .env.example .env.local
# Edit .env.local — at minimum RESEARCH_TOPIC and Notion vars for publish tests
npm install
npm run dev
```

Inspect discovered capabilities:

```bash
npm exec -- eve info
```

Trigger the daily schedule once (dev only):

```bash
curl -X POST http://localhost:2000/eve/v1/dev/schedules/daily_research
```

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Local Eve dev server + TUI |
| `npm run build` | Production build |
| `npm run deploy` | Deploy to Vercel production via `eve deploy` |
| `npm run typecheck` | TypeScript check |

## Architecture

- **Schedule** — `agent/schedules/daily_research.ts` (Vercel Cron, UTC)
- **Skill** — `agent/skills/daily_research/` workflow
- **Research** — `agent/extensions/browser.ts` (agent-browser)
- **Publish** — `agent/tools/publish_note.ts` → `agent/lib/notes/registry.ts` → destinations (Notion today)

To add another notes app: implement `NotesDestination` in `agent/lib/notes/destinations/`, register it in `registry.ts`, document env vars in `docs/SETUP_TODO.md`.

## Repo context

The parent [ragna-ai](../) repository also ships personal agent **skills** for [skills.sh](https://skills.sh) under `skills/`. That tree is independent of this Eve runtime.
