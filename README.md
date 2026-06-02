# ragna-ai

Personal agent skills for my developer & other personal workflows. Each skill is individually installable via the [skills.sh](https://skills.sh) CLI.

## Skills

### `/self-code-review`

Reviews the current branch's diff against `origin/main`. Flags functionality regressions, unnecessary React hooks, duplicated helpers/components, and stale leftover code. Use before opening a PR or when asked to "review my changes".

```bash
npx skills add jpbullalayao/ragna-ai --skill self-code-review
```

### `/submit-code-review`

Posts the findings from `/self-code-review` as GitHub PR comments via the `gh` CLI. Inline comments are preferred (attached to the specific file and line); falls back to regular PR conversation comments. Run `/self-code-review` first, then `/submit-code-review`.

```bash
npx skills add jpbullalayao/ragna-ai --skill submit-code-review
```

### `/submit-pull-request`

Creates a GitHub PR from the current branch using a fixed template (Ticket, Problem, Solution, Before, After, Test plan). Use when you want to "open a PR", "create a pull request", or "push this up as a PR".

```bash
npx skills add jpbullalayao/ragna-ai --skill submit-pull-request
```

### `/code-cleanup [<branch>]`

Analyzes the current branch's diff against `origin/main` (or a specified branch) and auto-applies cleanup fixes across three areas: code brevity & quality, regression risks, and CI/build health. For large diffs, invokes `/simplify` first; for React files, invokes `/react-doctor` before applying fixes. Each finding is classified as `[AUTO]` (applied immediately), `[ARCH]` (architectural improvement — shown as before/after, then applied), or `[MANUAL]` (surfaced for human review, not touched). Runs type checks and build verification after each pass.

```bash
npx skills add jpbullalayao/ragna-ai --skill code-cleanup
```

### `/create-ticket`

Creates a ticket in your preferred issue tracker (defaults to Linear) with a consistent two-section format designed to be clear to both humans and AI agents. The **Context** section explains how the current system works; the **Requirements** section lists actionable acceptance criteria. Explores the codebase to ground the Context in real implementation details. Use when you want to "create a ticket", "file an issue", "write up a ticket", or "open a Linear issue".

```bash
npx skills add jpbullalayao/ragna-ai --skill create-ticket
```

### `/write-docs`

Writes concise, token-efficient markdown documentation about a user-specified query, function, module, or project. Docs are readable by both humans and agents, auto-placed by project architecture, and the query can override defaults (verbosity, output path, format). Use when you want to "document this", "write docs for", or "write documentation about".

```bash
npx skills add jpbullalayao/ragna-ai --skill write-docs
```

### `/post-merge-cleanup`

Syncs the default branch and deletes the merged working branch after a PR merge. Checks out main, pulls latest, deletes the local branch (with confirmation for force-delete on squash/rebase merges), deletes the remote branch if still present (with confirmation), and prunes stale remote-tracking refs. Use after merging a PR when you want to "clean up my branch", "pull main and delete this branch", or "post-merge cleanup".

```bash
npx skills add jpbullalayao/ragna-ai --skill post-merge-cleanup
```

### `/staff-engineer-plan <query>`

Operates alongside Plan Mode in any agent to turn a free-form query into a production-grade implementation plan — one a staff+ engineer would both author and approve in review. Adopts senior engineering philosophy (architecture, elegance, simplification, performance), adversarially stress-tests any approach you proposed and pivots to a clearly better one when warranted (while staying flexible if you insist), and adds an easy-to-follow Mermaid/ASCII diagram only when the solution is genuinely hard to follow in prose. Always plans first (enters Plan Mode where available, else writes a plan file), and produces a plan any other agent or human can execute. Use when you want to "plan this like a staff engineer" or "review my approach and plan it properly".

```bash
npx skills add jpbullalayao/ragna-ai --skill staff-engineer-plan
```

## Install all at once

```bash
npx skills add jpbullalayao/ragna-ai
```

## Requirements

- `gh` CLI authenticated to GitHub (`gh auth login`)
- Claude Code with MCP Linear server connected:
  - Required for `/create-ticket` (used to create issues)
  - Optional for `/self-code-review` (fetches ticket context — degrades gracefully if unavailable)
