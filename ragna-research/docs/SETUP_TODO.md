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

- [ ] `npm i -g vercel` (if needed)
- [ ] `eve link` — create or link a Vercel project (deploy root = this directory).
- [ ] Enable **AI Gateway** on the project (dashboard) so gateway model strings work with OIDC.
- [ ] `vercel env pull` — pulls `VERCEL_OIDC_TOKEN` and related vars for local dev.

Add production env vars in the Vercel dashboard (or `vercel env add`):

- [ ] `NOTION_API_KEY` (mark **Sensitive**)
- [ ] `NOTION_PARENT_PAGE_ID`

Optional: `AI_GATEWAY_API_KEY` instead of OIDC for non-Vercel hosts.

## 4. Deploy

- [ ] `npm run deploy` (or push to a Git-connected Vercel project with root directory `ragna-research`).
- [ ] `curl https://<your-deployment>/eve/v1/health` returns OK.
- [ ] Vercel **Settings → Cron Jobs** lists `daily_research` (`0 14 * * *` **UTC** ≈ 07:00 US Pacific during PDT).

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
