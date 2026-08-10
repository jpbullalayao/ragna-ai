# research-agent

Eve project for **Ragna AI**, a durable backend agent. This directory is the **Vercel deploy root** (run `eve link` and `eve deploy` from here). The package/project name is `research-agent`; the agent’s identity is **Ragna AI**.

Add skills under `agent/skills/`, schedules under `agent/schedules/`, tools under `agent/tools/`, connections under `agent/connections/`, and extensions under `agent/extensions/` as you expand capabilities.

## Prerequisites

- Node.js 24.x
- [Vercel CLI](https://vercel.com/docs/cli) logged in (`npm i -g vercel`, then `vercel login`)
- A Vercel project linked from **this** directory (`research-agent/`)
- AI Gateway: `AI_GATEWAY_API_KEY` or Vercel OIDC from `vercel env pull`
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

## Repo context

The parent [ragna-ai](../) repository also ships personal agent **skills** for [skills.sh](https://skills.sh) under `skills/`. That tree is independent of this Eve runtime.
