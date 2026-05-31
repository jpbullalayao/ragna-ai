---
allowed-tools:
    - Bash(gh *)
description: Post the findings from the current conversation's /self-code-review output as GitHub PR comments on the current branch's pull request. Use AFTER running /self-code-review, when the user types /submit-code-review or asks to "submit the review", "post the comments to GitHub", or "push the review to the PR". Does NOT re-analyze the diff — it reads findings already present in the conversation. Optionally filters by a user-provided focus area. Prioritizes inline PR review comments (attached to the specific file and line) where a file:line citation exists; falls back to regular PR conversation comments when no citation is available or the inline post fails. Each comment starts with "_Comment from Claude Code agent · [Model]_" in italics (where [Model] is the short name of the Claude model currently running, e.g. "Sonnet 4.6", "Opus 4.7", "Haiku 4.5"), two blank lines, then "non-blocking" (default) or "blocking" (only when the user explicitly says so), then the finding on a new line. Requires `gh` CLI authenticated to GitHub.
metadata:
    github-path: skills/submit-code-review
    github-ref: refs/heads/main
    github-repo: https://github.com/jpbullalayao/ragna-ai
    github-tree-sha: 54cd237e501fd1c7f6b3a15349b80507860b5c4e
name: submit-code-review
---
# Submit Code Review

Takes the findings already produced by `/self-code-review` in the current
conversation and posts them on the current branch's GitHub pull request via
the `gh` CLI. **Inline comments are preferred** — findings with a `file:line`
citation are posted directly on the relevant line; everything else falls back
to a regular PR conversation comment.

**Never re-analyzes the diff.** This skill is the second step in a two-step flow:
1. `/self-code-review` — analyzes the diff, outputs findings in the conversation
2. `/submit-code-review` — posts those findings as GitHub PR comments

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

Look back through the current conversation for output from `/self-code-review`.
That output contains findings grouped under these categories:

- **Functionality Regressions**
- **Hook Usage**
- **Duplication / Reuse Opportunities**
- **Stale Code**
- **Other Notes**

Extract each individual bullet-point finding as a separate item to post.

If `FOCUS` is set, filter to only findings relevant to that area and skip the rest.

If no `/self-code-review` output is found in the conversation, stop immediately and
tell the user:

> "No /self-code-review output found in this conversation. Run /self-code-review
> first, then re-run /submit-code-review."

If every finding is "None spotted.", tell the user there is nothing to post and stop.

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

Findings from **Other Notes** (high-level observations without a specific location)
almost never have citations — treat them as regular comments.

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

### Step 7: Post comments sequentially

Process each finding one at a time (never in parallel). For each finding:

#### A — Inline comment (has file:line citation)

Attempt to post an inline review comment on the specific line:

```bash
gh api "repos/REPO/pulls/PR_NUMBER/comments" \
  --method POST \
  --field commit_id="HEAD_SHA" \
  --field path="PATH" \
  --field line=LINE \
  --field side="RIGHT" \
  --field body="FORMATTED_BODY"
```

If this call fails for any reason (line not in diff, path not found, API error),
**fall back immediately** to a regular PR comment (see B below). Do not retry
the inline call.

#### B — Regular PR comment (no citation, or inline fallback)

```bash
gh pr comment --body "FORMATTED_BODY"
```

### Step 8: Output summary

After all comments are posted:

```
Posted N comment(s) on PR #<number>: <title>
  • X inline comment(s)
  • Y conversation comment(s)
<PR URL>
```

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

**Regular conversation comment** (no specific line, e.g. Other Notes):
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
- **Inline failures are silent fallbacks.** Do not surface API errors to the user for
  individual inline attempts — just fall back and continue. Report the final tally in
  the summary.
- **Read-only.** Never modify any files in the working tree.
- **Never hardcode PR numbers, SHAs, or repo paths.** Always derive from `gh` output.
