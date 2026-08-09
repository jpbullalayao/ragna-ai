# research-agent

Eve project for **Ragna AI**, a durable backend agent. This directory is the **Vercel deploy root** (run `eve link` and `eve deploy` from here). The package/project name is `research-agent`; the agent’s identity is **Ragna AI**.

Add skills under `agent/skills/`, schedules under `agent/schedules/`, tools under `agent/tools/`, connections under `agent/connections/`, and extensions under `agent/extensions/` as you expand capabilities.

## Prerequisites

- Node.js 24.x
- [Vercel CLI](https://vercel.com/docs/cli) for linking and deploy (`npm i -g vercel`)
- AI Gateway: `AI_GATEWAY_API_KEY` or Vercel OIDC (`VERCEL_OIDC_TOKEN` via `vercel env pull`)
- **Notion** (optional until you need publish): Vercel Connect Notion client for `agent/connections/notion.ts`

## Notion connection

This agent uses Eve’s registry Notion connection (MCP), not a hand-rolled Notion HTTP client:

```bash
cd research-agent
# Install/configure Connect for the Notion MCP (interactive):
npm exec -- eve add connection/notion --skip-install
# Or: vercel connect create notion
```

`agent/connections/notion.ts` is **app-scoped** (`principalType: "app"`) so schedules and cron can call Notion without an interactive user session. Share the destination Notion pages/databases with the connected integration.

Confirm discovery with `npm exec -- eve info` (look for the `notion` connection and its tools).

## Local development

```bash
cd research-agent
cp .env.example .env.local
# Edit .env.local — gateway credentials
npm install
npm run dev
```

Inspect discovered capabilities:

```bash
npm exec -- eve info
```

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Local Eve dev server + TUI |
| `npm run build` | Production build |
| `npm run deploy` | Deploy to Vercel production via `eve deploy` |
| `npm run typecheck` | TypeScript check |

## Repo context

The parent [ragna-ai](../) repository also ships personal agent **skills** for [skills.sh](https://skills.sh) under `skills/`. That tree is independent of this Eve runtime.
