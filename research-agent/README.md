# research-agent

Eve project for **Ragna AI**, a durable backend agent. This directory is the **Vercel deploy root** (run `eve link` and `eve deploy` from here). The package/project name is `research-agent`; the agent’s identity is **Ragna AI**.

Add skills under `agent/skills/`, schedules under `agent/schedules/`, tools under `agent/tools/`, connections under `agent/connections/`, and extensions under `agent/extensions/` as you expand capabilities.

## Prerequisites

- Node.js 24.x
- [Vercel CLI](https://vercel.com/docs/cli) logged in (`npm i -g vercel`, then `vercel login`)
- A Vercel project linked from **this** directory (`research-agent/`)
- AI Gateway: `AI_GATEWAY_API_KEY` or Vercel OIDC from `vercel env pull`
- [Browser Use](https://browser-use.com) API key (`BROWSER_USE_API_KEY`) for cloud browsing
- Notion workspace access (only if the agent should read or write Notion pages)

## Local development

```bash
cd research-agent
npm install
vercel link
vercel env pull .env.local
# Optional: set AI_GATEWAY_API_KEY in .env.local if OIDC alone is not enough
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

## Browser Use (cloud browser)

Live web browsing uses [`@browser_use/eve`](https://www.npmjs.com/package/@browser_use/eve). The scaffold is:

- `agent/sandbox/sandbox.ts` — installs `browser-harness-js` in the sandbox
- `agent/skills/browser-use.ts` — CDP workflow for the model
- `agent/tools/open_cloud_browser.ts` / `stop_cloud_browser.ts` — provision and tear down a cloud browser

Add your [Browser Use](https://browser-use.com) API key locally and to the linked Vercel project:

```bash
# .env.local (see .env.example)
BROWSER_USE_API_KEY=bu_...

vercel env add BROWSER_USE_API_KEY
```

The API key stays in the app runtime. The agent receives only a scoped WebSocket URL, drives the browser with CDP, and should call `stop_cloud_browser` when finished. Ask it to “open example.com and tell me the title” as a smoke test.

Sandbox browser automation via `@agent-browser/eve` remains mounted in `agent/extensions/browser.ts` with a Reddit allowlist.

## Notion connection

Notion access uses **Vercel Connect** with Notion’s MCP server (`https://mcp.notion.com/mcp`). The connection file is `agent/connections/notion.ts` and authenticates with:

```ts
auth: connect("notion/notion");
```

That string is the connector **UID** (`<service>/<name>`). Creating a connector with `--name notion` yields UID `notion/notion`. Use that UID in CLI commands and keep it in sync with `notion.ts`.

Authorization is **user-scoped**: each developer signs in to Notion once for their Vercel user. Run Connect and Eve commands from the linked `research-agent/` directory so the CLI can mint a Vercel user OIDC token for that session.

### 1. Create and attach the connector

```bash
cd research-agent
vercel link

vercel connect create notion --connection-method mcp --name notion
vercel connect attach notion/notion
vercel env pull .env.local
```

`create` may already attach the linked project; `attach` is safe to run either way. Confirm with:

```bash
vercel connect list
# Expect UID notion/notion on this project
```

### 2. Authorize Notion

```bash
vercel connect token notion/notion --yes
```

Complete the browser OAuth flow when prompted.

### 3. Share destination pages

OAuth alone does not grant page access. In Notion:

1. Open the parent page or database the agent should use.
2. **⋯ → Connections** → add the integration from this Connect setup.
3. Optional: set that page’s UUID in `.env.local` as `NOTION_PARENT_PAGE_ID`.

### 4. Smoke test

```bash
npm run dev
```

In the TUI:

```text
Using Notion connection tools, create a page under parent <PAGE_ID>
titled "Hello world" with body "Hello world". Reply with the page URL.
```

Or without the TUI:

```bash
npm exec -- eve invoke "Using Notion connection tools, create a page under parent <PAGE_ID> titled 'Hello world' with body 'Hello world'. Reply with the page URL."
```

Useful checks:

```bash
npm exec -- eve info          # connection notion / notion__* tools
vercel connect open notion/notion
```

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Local Eve dev server + TUI |
| `npm run build` | Production build |
| `npm run deploy` | Deploy to Vercel production via `eve deploy` |
| `npm run typecheck` | TypeScript check |

## Architecture

- **Connection** — `agent/connections/notion.ts` (Eve registry Notion MCP via Vercel Connect)
- **Schedules** — `agent/schedules/*` kick off runs; workflow lives in matching skills
- **Skill** — `agent/skills/daily_investment_research/` (Reddit stock pulse for casual investors)
- **Research** — Browser Use cloud browser (`open_cloud_browser` / `stop_cloud_browser`) plus `agent/extensions/browser.ts` (agent-browser, Reddit allowlist)

## Repo context

The parent [ragna-ai](../) repository also ships personal agent **skills** for [skills.sh](https://skills.sh) under `skills/`. That tree is independent of this Eve runtime.
