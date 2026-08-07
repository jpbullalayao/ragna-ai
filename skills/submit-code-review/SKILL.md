---
name: submit-code-review
description: >-
  Post the code-review findings already present in the current conversation as
  GitHub PR comments on the current branch's pull request. Use AFTER a code
  review has been run in the conversation, when the user types
  /submit-code-review or asks to "submit the review", "post the comments to
  GitHub", or "push the review to the PR".
  Does NOT re-analyze the diff — it reads findings already present in the
  conversation. Optionally filters by a user-provided focus area. Prioritizes
  inline PR review comments (attached to the specific file and line) where
  a file:line citation exists; falls back to regular PR conversation comments
  when no citation is available. All inline comments are submitted together as
  a single PR review, never one review per finding. Each comment starts
  with "_Comment from Claude Code agent · [Model]_" in italics (where [Model]
  is the short name of the Claude model currently running, e.g. "Sonnet 4.6",
  "Opus 4.7", "Haiku 4.5"), two blank lines, then "non-blocking" (default) or
  "blocking" (only when the user explicitly says so), then the finding on a new
  line. Requires `gh` CLI authenticated to GitHub.
allowed-tools:
  - "Bash(gh *)"
  - "Write"
---

# Submit Code Review

Takes the code-review findings already present in the current conversation and
posts them on the current branch's GitHub pull request via the `gh` CLI.
**Inline comments are preferred** — findings with a `file:line` citation are
posted directly on the relevant line; everything else falls back to a regular
PR conversation comment.

**All inline comments ship as one review.** They are batched into a single
`POST /pulls/{n}/reviews` call.

**Never re-analyzes the diff.** This skill only posts findings; it assumes a
code review has already been run earlier in the conversation and its findings
are in context.

## Workflow

### Step 1: Gather user input

Ask the user two questions before doing anything else:

1. "Is there a particular focus area? Should I only post a subset of the findings
   (e.g. 'only stale code', 'only regressions')? Press Enter to post all findings."
2. "Should comments be posted as **blocking**? (default: non-blocking)"

Store:
- `FOCUS` — filter string (empty → post all findings)
- `BLOCKING` — `true` if user says yes, `false` otherwise (default)

### Step 2: Read findings from the conversation

Look back through the current conversation for the most recent code-review
output. Findings may be grouped under categories (bugs, regressions,
duplication, stale code, etc.) or listed flat — extract each individual finding
as a separate item to post.

If `FOCUS` is set, filter to only findings relevant to that area and skip the rest.

If no code-review findings are found in the conversation, stop immediately and
tell the user:

> "No code-review findings found in this conversation. Run a code review first,
> then re-run /submit-code-review."

If the review reported no issues, tell the user there is nothing to post and stop.

### Step 3: Gather PR metadata

Run these in parallel:

```bash
gh pr view --json number,title,url,state,headRefOid
gh repo view --json owner,name
```

- If no PR is found for the current branch, tell the user and stop.
- If the PR state is `CLOSED` or `MERGED`, warn the user and ask whether to continue.

Store:
- `PR_NUMBER` — from `number`
- `PR_TITLE` — from `title`
- `PR_URL` — from `url`
- `HEAD_SHA` — from `headRefOid`
- `REPO` — `"{owner.login}/{name}"` constructed from the repo view output

### Step 4: Classify each finding

For each finding, check whether it contains a `file:line` citation — i.e. a
backtick-wrapped path followed by a colon and a line number, such as:

```
`src/lib/utils.ts:42`
`apps/web/components/Foo.tsx:15`
```

- **Has citation → inline candidate.** Extract `PATH` and `LINE`.
- **No citation → regular comment.** Post to the PR conversation.

High-level observations without a specific location almost never have
citations — treat them as regular comments.

**Then validate every inline candidate against the diff.** GitHub rejects the
*entire* batched review with a 422 if even one comment targets a line outside the
diff, so filter before posting rather than discovering it on submit:

```bash
gh api "repos/REPO/pulls/PR_NUMBER/files" --jq '.[] | select(.filename=="PATH") | .patch'
```

For each hunk header `@@ -old,oldCount +new,newCount @@`, the commentable range on
the right side is `new` through `new + newCount - 1`. A candidate survives if `PATH`
appears in the file list **and** `LINE` falls inside one of that file's hunk ranges.

Any candidate that fails validation is **demoted to a regular comment** — keep its
`file:line` citation in the body so the location is not lost. Prefer re-anchoring a
finding to a nearby changed line over demoting it, when the nearby line still makes
the point.

### Step 5: Determine severity label

- Use `non-blocking` for all comments by default.
- Use `blocking` **only** if the user explicitly requested it in Step 1.

### Step 6: Format each comment body

Determine the **model label** first: use the short friendly name of the Claude model
currently running this skill — e.g. `Sonnet 4.6`, `Opus 4.7`, `Haiku 4.5`. This is
known from the session context; do not hard-code it.

The body format differs slightly between inline and regular comments.

**For inline comments** — the file, path, and line number must be stripped from the
finding text. GitHub already anchors the comment to the exact line, so repeating
that info is redundant. Use:

```
_Comment from Claude Code agent · [Model]_


non-blocking

[finding text with the file:line citation removed — observation and suggestion only]

**Suggested fix:**
```lang
[corrected code snippet]
```
```

**For regular conversation comments** — keep the `file:line` citation in the text
since there is no GitHub anchor to provide that context:

```
_Comment from Claude Code agent · [Model]_


non-blocking

[finding text verbatim, including any file:line citations]

**Suggested fix:**
```lang
[corrected code snippet]
```
```

Swap `non-blocking` for `blocking` when `BLOCKING` is `true` (applies to both types).

**Code block rules:**
- Include a `**Suggested fix:**` block whenever the finding implies a concrete code
  change. The goal is that the contributor can copy-paste the block directly.
- Use the correct language tag (`ts`, `tsx`, `js`, `jsx`, `py`, `sql`, etc.) derived
  from the file extension in the citation.
- The snippet should be minimal — show only the corrected lines plus enough
  surrounding context (2–3 lines) to locate the change, not the entire function.
- If the fix is genuinely architectural or cannot be expressed as a snippet (e.g.
  "consider splitting this into two modules"), omit the block entirely rather than
  writing placeholder pseudo-code.

### Step 7: Post the review

#### A — Inline comments → one batched review

Skip this section entirely when no inline candidates survived Step 4.

Write the whole review as a single JSON payload, then submit it in one call.
Compose the file with the Write tool — the bodies contain markdown, backticks, and
newlines, so building JSON inline in the shell is unreliable. Put it in the session
scratchpad directory when one is available, otherwise a temp path; call it
`PAYLOAD_PATH`.

```json
{
  "commit_id": "HEAD_SHA",
  "event": "COMMENT",
  "body": "_Code review from Claude Code agent · [Model]_",
  "comments": [
    { "path": "PATH", "line": LINE, "side": "RIGHT", "body": "FORMATTED_BODY" }
  ]
}
```

- `body` is **required** when `event` is `COMMENT` — a review with only comments
  and an empty body is rejected. Keep it to the one-line attribution above.
- Each comment keeps its own `_Comment from Claude Code agent · [Model]_` header.
  It reads as redundant on the PR page but is what a reader sees when a single
  comment arrives by email or is quoted in isolation.
- `commit_id` defaults to the PR's most recent commit; pass `HEAD_SHA` anyway so
  the review anchors to the revision that was actually reviewed.

```bash
gh api "repos/REPO/pulls/PR_NUMBER/reviews" --method POST --input PAYLOAD_PATH
```

**If the call fails**, do not retry with `POST /pulls/{n}/comments` — that is the
behavior this batching exists to avoid. Instead:

1. If the error names an offending `path`/`line`, drop those comments to the
   regular-comment bucket (keeping their citations) and retry the batched review
   **once**.
2. If it still fails, post the remaining inline findings as regular PR comments
   via B. Line anchoring is lost but the citations remain in the bodies, and the
   PR timeline stays clean.

#### B — Regular PR comments (no citation, demoted, or review fallback)

One call per finding, sequentially:

```bash
gh pr comment PR_NUMBER --body-file BODY_PATH
```

Use `--body-file` rather than `--body` so markdown and newlines survive intact.
These are issue comments, not review comments, so they add no reviews to the PR.

### Step 8: Output summary

After everything is posted:

```
Posted N comment(s) on PR #<number>: <title>
  • X inline comment(s) in 1 review
  • Y conversation comment(s)
<PR URL>
```

Omit a bullet whose count is zero. If the batched review had to be degraded to
conversation comments, say so explicitly rather than reporting a clean tally.

---

## Comment Format Reference

**Inline comment with suggested fix** (posted on `src/lib/utils.ts` line 42 — no path/line in body):
```markdown
_Comment from Claude Code agent · [Model]_


non-blocking

`parseDate` is called with potentially undefined input. Add a null check before
passing to `Date.parse()`.

**Suggested fix:**
```ts
if (!rawDate) return null;
const parsed = Date.parse(rawDate);
```
```

**Inline comment without a fix** (architectural note, no copyable snippet):
```markdown
_Comment from Claude Code agent · [Model]_


non-blocking

Session token is stored in `localStorage`. Consider `httpOnly` cookies to reduce
XSS exposure.
```

**Regular conversation comment** (no specific line):
```markdown
_Comment from Claude Code agent · [Model]_


non-blocking

The PR description doesn't mention the schema migration — worth noting for reviewers.
```

---

## Constraints

- **Never re-analyze the diff.** All findings come from the existing conversation context.
- **Never post an empty comment.** If there are no findings to post (or none match
  the focus filter), tell the user: "No findings to post — no comments were submitted."
- **`gh` auth is required.** Run `gh auth status` first. If unauthenticated, tell the
  user to run `gh auth login` and stop.
- **One review, always.** Every inline comment goes in a single
  `POST /pulls/{n}/reviews` call. `POST /pulls/{n}/comments` is never correct here —
  it produces one review per finding.
- **Inline failures are silent fallbacks.** Do not surface API errors to the user for
  individual demotions — just fall back and continue. Report the final tally in
  the summary.
- **Read-only in the repo.** Never modify any files in the working tree. The review
  payload is written to the scratchpad, not the project.
- **Never hardcode PR numbers, SHAs, or repo paths.** Always derive from `gh` output.
