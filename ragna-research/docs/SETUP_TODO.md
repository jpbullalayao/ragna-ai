# Setup TODO — Ragna AI (ragna-research) → Notion

Use this checklist to go from the scaffolded agent (**Ragna AI**, project `ragna-research`) to **daily research notes landing in Notion** on Vercel.

## 1. Notion Internal Integration (recommended for cron)

Scheduled runs use **app-scoped** credentials. User OAuth via Vercel Connect does not attach a user principal to cron sessions.

- [ ] Open [Notion My integrations](https://www.notion.so/my-integrations) → **New integration**.
- [ ] Name it (e.g. `Ragna AI`), select the workspace, create.
- [ ] Copy the **Internal Integration Secret** → this is `NOTION_API_KEY`.
- [ ] In Notion, open the **parent page** where daily notes should appear → **⋯** → **Connect to** → select your integration.
- [ ] Copy the parent page ID from the URL (`https://notion.so/...<32-char-id>`) → `NOTION_PARENT_PAGE_ID` (UUID with hyphens).

## 2. Research topics (schedules)

Each topic is a schedule (or an ad-hoc session prompt) — no central topics list.

- [ ] Edit [`agent/schedules/daily_research.ts`](../agent/schedules/daily_research.ts) and replace the placeholder topic in the markdown prompt.
- [ ] Or add another file under `agent/schedules/` (e.g. `vercel_ai_sdk.ts` or `vercel_ai_sdk.md`) with its own `cron` and research prompt.
- [ ] Redeploy (or restart `eve dev`) so new schedules register as Vercel Cron jobs.

Markdown schedule example:

```md
---
cron: "0 14 * * *"
---

Conduct daily research on: **Vercel AI SDK**.
Load the `daily_research` skill and follow it end to end.
Publish exactly one consolidated note with `publish_note`.
```

## 3. Vercel project + Eve link

From `ragna-research/`:

- [x] `npm i -g vercel` (if needed)
- [x] Root Directory set to `ragna-research` (monorepo: repo `jpbullalayao/ragna-ai`, app lives in this folder)
- [ ] **Connect GitHub to Vercel** (required before `vercel git connect` works): [Account → Authentication → GitHub](https://vercel.com/account/settings/authentication) → connect GitHub as a login connection (not just CLI login).
- [ ] **Link the repo** (from repo root, after GitHub is connected):

  ```bash
  cd /path/to/ragna-ai
  vercel link --yes --project ragna-research --scope jpbullalayaos-projects
  vercel git connect
  ```

  Production deploys will track **`main`** (or your default branch). Push to `main` or merge PRs to trigger builds.

- [x] AI Gateway — team already has Gateway access; created key `ragna-research` and set `AI_GATEWAY_API_KEY` on Production/Preview/Development (OIDC also available on Vercel via `VERCEL_OIDC_TOKEN`)
- [x] OIDC / env pull — deploy flow wrote `VERCEL_OIDC_TOKEN` into `.env.local`

Production env vars (set via `vercel env add`):

- [x] `NOTION_API_KEY` (Sensitive on Production/Preview)
- [x] `NOTION_PARENT_PAGE_ID` (UUID form: `3b43e4e5-359a-8089-a629-face9c03fb14`)

Optional: `AI_GATEWAY_API_KEY` instead of OIDC for non-Vercel hosts.

## 4. Deploy

- [x] Production URL: https://ragna-research.vercel.app
- [x] `curl https://ragna-research.vercel.app/eve/v1/health` returns `{"ok":true,"status":"ready",...}`

**CLI deploy (monorepo):** run from the **repo root** (not `ragna-research/` alone), because the Vercel project Root Directory is `ragna-research`:

```bash
cd /path/to/ragna-ai
vercel deploy --prod
```

Or from `ragna-research/`: `npm run deploy` only works if project Root Directory is `.`; with Git monorepo settings, prefer repo-root `vercel deploy --prod` above.

- [x] Deploy includes cron route `eve/v1/cron/...` for `daily_research` (`0 14 * * *` **UTC** ≈ 07:00 US Pacific during PDT) — confirm under Vercel **Settings → Cron Jobs** if desired

Adjust cron in `agent/schedules/daily_research.ts` if you need a different UTC time.

## 5. Verify end-to-end

**Local (with credentials in `.env.local`):**

- [ ] `npm run dev`
- [ ] `curl -X POST http://localhost:2000/eve/v1/dev/schedules/daily_research`
- [ ] Confirm a new child page under your Notion parent page.

**Production:**

- [ ] Wait for cron or trigger a manual session via the Eve HTTP API if you add a secured manual route later.
- [ ] Check **Observability → Logs** and **Agent Runs** for failures.

## 6. Auth for HTTP channel (before public browser use)

Default `agent/channels/eve.ts` includes `placeholderAuth()` — replace before exposing the agent on the public internet. See [Eve auth and route protection](https://eve.dev/docs/guides/auth-and-route-protection).

## 7. Optional: Vercel Connect for Notion (interactive / per-user)

For **interactive** sessions where each user authorizes their own Notion workspace:

```bash
vercel connect create notion
```

Replace the Internal Integration path with `eve add connection/notion` and app-scoped Connect (`connect({ connector: "notion", principalType: "app" })`) if you prefer Connect token storage over `NOTION_API_KEY`.

**Do not** rely on user-scoped Connect for the daily cron job alone.

## 8. Adding another notes destination

- [ ] Create `agent/lib/notes/destinations/<app>.ts` implementing `NotesDestination` from `agent/lib/notes/types.ts`.
- [ ] Register the factory in `agent/lib/notes/registry.ts`.
- [ ] Document required env vars in this file.
- [ ] Extend `publish_note` tests / manual verification.

## Known follow-ups (not blocking first publish)

- [ ] Richer markdown → Notion blocks (lists, code, links as Notion link objects).
- [ ] Pagination when notes exceed 100 Notion blocks.
- [ ] Dedupe / idempotency key per day to avoid duplicate pages on retries.
- [ ] Evals under `evals/` for publish and research quality.
