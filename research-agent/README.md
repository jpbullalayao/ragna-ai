# research-agent

Eve project for **Ragna AI**, a durable backend agent. This directory is the **Vercel deploy root** (run `eve link` and `eve deploy` from here). The package/project name is `research-agent`; the agent’s identity is **Ragna AI**.

Add skills under `agent/skills/`, schedules under `agent/schedules/`, tools under `agent/tools/`, connections under `agent/connections/`, and extensions under `agent/extensions/` as you expand capabilities.

## Prerequisites

- Node.js 24.x
- [Vercel CLI](https://vercel.com/docs/cli) logged in (`npm i -g vercel`, then `vercel login`)
- A Vercel project linked from **this** directory (`research-agent/`)
- AI Gateway: `AI_GATEWAY_API_KEY` or Vercel OIDC from `vercel env pull`
- Notion workspace access (only if you need the agent to read/write pages)

## Local development

```bash
cd research-agent
npm install
vercel link          # link this folder to your Vercel project
vercel env pull .env.local
# Optional: set AI_GATEWAY_API_KEY in .env.local if OIDC is not enough
npm run dev
```

Inspect discovered capabilities:

```bash
npm exec -- eve info
```

## Notion connection

The agent talks to Notion through **Vercel Connect + Notion MCP** (`agent/connections/notion.ts`), not a custom Notion HTTP client. Auth is **user-scoped** (`connect("notion/notion")`): each developer authorizes their own Notion workspace. App tokens (`principalType: "app"`) are **not** supported for this MCP connector today, so cron/schedules that need Notion without a user session will fail until that changes or you switch to an API-key connector.

`agent/connections/notion.ts` is already in the repo. Do **not** re-run `eve add connection/notion` unless you intend to regenerate that file (the registry default uses a different connector id / auth mode).

### One-time Connect setup (from `research-agent/`)

```bash
cd research-agent
vercel link   # required; Connect commands use the linked project

# Skip create if the team already has UID notion/notion (see below)
vercel connect create notion --connection-method mcp --name notion

# Attach if create did not already link this project
vercel connect attach notion/notion

vercel env pull .env.local
```

**Same Vercel team / reinstalling on a new machine:** if `vercel connect list --all-projects` already shows `notion/notion`, skip `create`. Run `attach`, `token … --yes`, and `env pull` only. Use a new `--name` (and update `connect("…")` in `notion.ts`) only when you intentionally want a second connector.

Use the **UID** `notion/notion` (or the `scl_…` id from create), not the short name `notion`. `vercel connect attach notion` fails with “No connector found”.

Confirm:

```bash
vercel connect list
# Expect UID notion/notion linked to your project

# Authorize your Vercel user against Notion (opens browser)
vercel connect token notion/notion --yes
```

`vercel connect token notion/notion --subject app` failing with “Token subject is not accessible” is expected for this connector.

### Share pages in Notion

Connect only grants OAuth. The integration still cannot see pages until you share them:

1. Open the parent page (or database) in Notion.
2. **⋯ → Connections** → connect/share with the integration created by Vercel Connect.
3. Optional: put that page’s UUID in `.env.local` as `NOTION_PARENT_PAGE_ID`.

### Smoke test

```bash
npm run dev
```

In the TUI (stay in the linked `research-agent/` directory so the CLI can mint a Vercel user OIDC token for user-scoped Connect):

```text
Using Notion connection tools, create a page under parent <PAGE_ID>
titled "Hello world" with body "Hello world". Reply with the page URL.
```

Or:

```bash
npm exec -- eve invoke "Using Notion connection tools, create a page under parent <PAGE_ID> titled 'Hello world' with body 'Hello world'. Reply with the page URL."
```

If Eve says Notion is configured but not authorized, finish `vercel connect token notion/notion --yes`, restart `npm run dev`, and retry. If tools run but page create fails, the page is not shared with the integration.

Confirm tools with `npm exec -- eve info` (look for connection `notion` / `notion__*` tools). Dashboard for the connector: `vercel connect open notion/notion`.

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Local Eve dev server + TUI |
| `npm run build` | Production build |
| `npm run deploy` | Deploy to Vercel production via `eve deploy` |
| `npm run typecheck` | TypeScript check |

## Repo context

The parent [ragna-ai](../) repository also ships personal agent **skills** for [skills.sh](https://skills.sh) under `skills/`. That tree is independent of this Eve runtime.
