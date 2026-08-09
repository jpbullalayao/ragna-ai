---
description: Daily deep dive on general stock-investing subreddits so a casual investor knows which tickers are being discussed and why.
---

Use this skill for scheduled or on-demand **daily investment pulse** runs. Goal: by end of run, a casual investor can answer *“What stocks did Reddit care about today, and why?”* without reading hundreds of posts.

## Subreddits to cover (in order)

Visit each via browser. Prefer **today’s** (or last ~24h) hot/top/discussion threads; read enough posts and comments to infer themes, not just headlines.

| Subreddit | Role | How to read it |
| --- | --- | --- |
| **r/stocks** | Core — individual names, news, earnings reactions | Daily discussion threads, high-upvote tickers, “why is X moving” posts |
| **r/investing** | Core — broader market, portfolios, fundamentals | Daily thread, advice threads with ticker mentions |
| **r/StockMarket** | Market-wide news and index/sector mood | Front page + daily discussion |
| **r/wallstreetbets** | Sentiment & momentum (noisy) | What’s trending; **always** label hype vs substance |
| **r/ValueInvesting** | Fundamental theses | Top DD posts mentioning tickers |
| **r/dividends** | Income / yield names | What dividend investors are buying or worried about |
| **r/SecurityAnalysis** | Higher-quality DD (optional if time) | 1–2 top posts only — extract tickers and thesis summary |

Skip or lightly skim: r/pennystocks, r/Superstonk, meme-only threads unless they spill into the core subs above.

## Research steps

1. Note **today’s date** (UTC or US Pacific — be consistent in the note).
2. For each subreddit above, open `https://www.reddit.com/r/{name}/` (or `.json` / old.reddit if easier). Capture **thread title, URL, upvote/comment signal if visible**, and the **investment reason** people give (catalyst, earnings, macro, meme, short squeeze narrative, etc.).
3. **Merge by ticker**: one entry per symbol that appeared in multiple places; dedupe spam.
4. **Score substance** (1–5): 1 = pure hype/meme; 5 = cites filings, numbers, or concrete catalysts. Call out WSB-heavy names explicitly.
5. Do **not** invent tickers or narratives. If a sub is quiet, say so.
6. Draft the note using the **Output format** below (markdown).
7. Publish **once** to Notion via the Eve **Notion connection** (not a custom tool):
   - Use `connection_search` if needed to find Notion create/update tools (`notion__*`).
   - Prefer creating a child page under `NOTION_PARENT_PAGE_ID` from the schedule/session when provided.
   - Page title: `Reddit investment pulse — {YYYY-MM-DD}` (or include that as the leading `#` heading in markdown content).
   - Body: the full markdown below (tables/lists should be real markdown so Notion MCP can render them).
   - Optionally tag or mention in the page body: `investing`, `reddit`, `daily-pulse`, plus top 3–5 tickers.

If browser access fails for a sub, document which failed and continue with the rest.

## Output format (markdown body)

Use this structure exactly so daily notes compare across time:

```markdown
# Reddit investment pulse — {date}

## At a glance

{3–5 bullets: plain English, no jargon — what a casual investor should notice today}

## Tickers table

| Ticker | Buzz | Subreddits | Why people are talking | Sentiment | Substance (1–5) | Casual take |
| --- | --- | --- | --- | --- | --- | --- |
| EXAMPLE | High | r/stocks, r/wsb | … | Mixed | 2 | Watchlist only — hype heavy |

**Buzz**: High / Medium / Low (relative to today’s scan).  
**Sentiment**: Bullish / Bearish / Mixed / Unclear.  
**Casual take**: one short line — e.g. “Worth reading DD before acting”, “Noise only”, “Earnings-driven, check filing”.

## Ticker deep dives

Repeat this block only for **High** buzz or **substance ≥ 3** tickers (cap at 8 to keep the note readable):

### {TICKER}

- **Why today**: …
- **Arguments bulls mention**: …
- **Arguments bears / skeptics mention**: …
- **Catalysts cited**: …
- **Hype warning**: …
- **Representative threads**:
  - [{title}]({url}) — r/{sub} — one sentence summary

## Subreddit digests

### r/stocks
- Themes: …
- Notable threads: …

### r/investing
…

### r/StockMarket
…

### r/wallstreetbets
…

### r/ValueInvesting
…

### r/dividends
…

### r/SecurityAnalysis
…

## What didn’t matter today

{Tickers or themes that were loud but low substance — helps ignore noise tomorrow}

## Caveats

- Reddit is not financial advice; positions, bots, and manipulation exist.
- US-centric bias; timestamps may blur “today” across time zones.
- High upvotes ≠ correct thesis.

## Sources

- Bulleted list of every thread URL referenced above.
```

After publishing, report the Notion page URL from the connection tool output (or the configuration/auth error if publish failed).
