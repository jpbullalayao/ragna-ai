---
name: recall
description: >-
  Recalls prior agent-session context about a topic so follow-up work can
  continue in the current session without hunting for the original chat.
  Searches local transcripts across Cursor, Claude Code, Codex, and Gemini,
  ranks the most relevant sessions, and synthesizes an inline context briefing.
  Use when the user invokes /recall <query>, or asks to "recall", "what did we
  do about", "continue where we left off", or resume work on a prior topic.
allowed-tools:
  - "Bash(python3 *)"
  - "Read"
---

# Recall

Gathers all relevant context about a topic from the **current session** and **prior sessions** so the user can continue work without remembering which chat they used.

Invocation: `/recall <query>` — the text after the command is the topic to recall.

This skill is **harness-agnostic**. It searches local transcripts from Cursor, Claude Code, Codex, and Gemini via the bundled search script.

## Workflow

### Step 1: Parse the query

Extract `<query>` from `/recall <query>`. If empty, show:

```
Usage: /recall <query>
```

### Step 2: Search prior sessions

Run the bundled search script from the skill directory:

```bash
python3 scripts/recall_search.py search "<query>"
```

If the skill is installed elsewhere, resolve the script path relative to this skill's location.

Useful flags:

- `--limit N` (default 5) — cap ranked results
- `--all-projects` — search beyond the current project
- `--harness cursor|claude|codex|gemini` — limit to one harness

The script returns a JSON array of ranked sessions: `harness`, `path`, `sessionId`, `title`, `firstTs`, `lastTs`, `score`, `snippets`.

If no matches are returned, say so and continue with whatever context exists in the current session.

### Step 3: Include the current session

Always treat the **current session** as a source. The user may already have relevant context here even if prior sessions also match.

Determine whether the relevant context lives in one session or spans several. Either way, the output format is the same.

### Step 4: Read top-ranked sessions

For the top 1–3 matches (or all matches if fewer), pull only the relevant turns:

```bash
python3 scripts/recall_search.py show "<path>" --query "<query>" --context 2
```

Use `show` without `--query` only when the session is short or the filtered output drops important context.

**Reading in parallel (optional, narrow case).** Do NOT fan out subagents to scan the corpus — Step 2's single `search` call already does that in one fast pass. Only consider parallelism here, and only when **both** hold:

- the relevant context spans **several** sessions (roughly 3+ top-ranked matches), and
- each session's filtered `show` output is large enough that reading them all inline would bloat this session's context.

In that case, and only if the host harness supports subagents, dispatch **one subagent per top-ranked session** (never per available session) to read its `show --query` output and return a short extract; then synthesize their extracts in Step 5. For the common case of 1–3 small filtered excerpts, just read them directly here — spawning subagents is slower and costlier than reading inline.

### Step 5: Synthesize an inline context briefing

Produce a concise briefing in the current session. Use this structure:

```markdown
## Recall: <query>

**Sources:** <harness/session ids or "current session only">
**Scope:** <single session | multiple sessions>

### Summary
<1–3 sentences on what was explored and where things stand>

### Key decisions & findings
- <decision or finding>
- <decision or finding>

### Files & paths touched
- `path/to/file` — <why it matters>

### Current state
<what is done, in progress, or blocked>

### Suggested next steps
1. <concrete next action>
2. <concrete next action>
```

Keep it scannable and actionable. Omit sections with nothing useful to report.

## Additional resources

- Transcript search implementation: [scripts/recall_search.py](scripts/recall_search.py)

