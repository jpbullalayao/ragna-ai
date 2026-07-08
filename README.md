# ragna-ai

Personal agent skills for my developer & other personal workflows. Each skill is individually installable via the [skills.sh](https://skills.sh) CLI.

## Skills

### `/self-code-review`

Reviews the current branch's diff against its base branch — the open PR's base branch when the branch has one, otherwise the repo's default branch. Flags functionality regressions, unnecessary React hooks, duplicated helpers/components, and stale leftover code. Use before opening a PR or when asked to "review my changes".

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

Analyzes the current branch's diff against its base branch — a specified branch via `/code-cleanup <branch>`, else the open PR's base branch, else the repo's default branch — and auto-applies cleanup fixes across three areas: code brevity & quality, regression risks, and CI/build health. For large diffs, invokes `/simplify` first; for React files, invokes `/react-doctor` before applying fixes. Each finding is classified as `[AUTO]` (applied immediately), `[ARCH]` (architectural improvement — shown as before/after, then applied), or `[MANUAL]` (surfaced for human review, not touched). Runs type checks and build verification after each pass.

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

### `/pull-latest-default-branch`

Fast-forwards the local default branch (main, master, etc.) to match the remote without switching away from your current branch. Uses `git pull --ff-only` when already on the default branch, or `git fetch origin DEFAULT:DEFAULT` for an in-place update from a feature branch. Prunes stale remote-tracking refs afterward. Use when you want to "pull latest main", "update local main", "sync default branch", or keep your local default branch current while staying on your working branch.

```bash
npx skills add jpbullalayao/ragna-ai --skill pull-latest-default-branch
```

### `/npm-increment [<version>]`

Analyzes changes since the last package version, recommends a semver bump (patch/minor/major), and runs `npm version` after user confirmation. Supports explicit target versions (e.g. `/npm-increment 2.0.0`) and re-prompts when you decline the recommendation (different bump, custom version, or cancel). Use when you want to "bump the version", "increment package version", or "release a new version".

```bash
npx skills add jpbullalayao/ragna-ai --skill npm-increment
```

### `/staff-engineer-plan <query>`

Operates alongside Plan Mode in any agent to turn a free-form query into a production-grade implementation plan — one a staff+ engineer would both author and approve in review. Adopts senior engineering philosophy (architecture, elegance, simplification, performance), adversarially stress-tests any approach you proposed and pivots to a clearly better one when warranted (while staying flexible if you insist), and adds an easy-to-follow Mermaid/ASCII diagram only when the solution is genuinely hard to follow in prose. Always plans first (enters Plan Mode where available, else writes a plan file), and produces a plan any other agent or human can execute. Use when you want to "plan this like a staff engineer" or "review my approach and plan it properly".

```bash
npx skills add jpbullalayao/ragna-ai --skill staff-engineer-plan
```

### `/root-cause <query>`

Addresses a specific task or bug by tracing to and fixing the true underlying cause rather than applying a surface band-aid. Follows the causal chain upstream from the symptom site to the cause site, then reasons with itself — via an explicit band-aid vs root test — to confirm the chosen fix resolves the whole class of problem before implementing. When the real root is genuinely out of scope, it applies a clearly labeled mitigation and flags the follow-up instead of patching silently. Use when you want to "fix", "address", "solve", or "get to the bottom of" a specific task or bug.

```bash
npx skills add jpbullalayao/ragna-ai --skill root-cause
```

### `/recall <query>`

Recalls prior agent-session context about a topic so follow-up work can continue in the current session without hunting for the original chat. Searches local transcripts across Cursor, Claude Code, Codex, and Gemini, ranks the most relevant sessions, and synthesizes an inline context briefing with summary, key decisions, files touched, current state, and next steps. Use when you want to "recall" a topic, ask "what did we do about", or "continue where we left off".

```bash
npx skills add jpbullalayao/ragna-ai --skill recall
```

### `/update-skills`

Updates globally installed agent skills from the ragna-ai repo. Runs `npx skills add jpbullalayao/ragna-ai` from the home directory to refresh all skills at once. Does not commit, push, or modify the ragna-ai workspace. Use when you want to "update skills", "refresh skills", "sync skills", or pull the latest skill definitions.

```bash
npx skills add jpbullalayao/ragna-ai --skill update-skills
```

## Install all at once

```bash
npx skills add jpbullalayao/ragna-ai
```

## Requirements

- `gh` CLI authenticated to GitHub (`gh auth login`):
  - Required for `/submit-code-review` and `/submit-pull-request` (post PR comments / open PRs)
  - Optional for `/self-code-review` and `/code-cleanup` (detect the open PR's base branch — degrade gracefully to the repo's default branch if unavailable)
- Claude Code with MCP Linear server connected:
  - Required for `/create-ticket` (used to create issues)
  - Optional for `/self-code-review` (fetches ticket context — degrades gracefully if unavailable)
