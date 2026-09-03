---
name: code-review-walkthrough
description: >-
  Run Claude's native /code-review on the current branch (or a given PR
  number/branch), then invoke /html-walkthrough to publish a visual walkthrough
  of the change that frames it as a Before and After — what problem the pull
  request set out to solve, how things worked before it, and how they work
  after. Use when the user types /code-review-walkthrough [<PR#>|<branch>], or
  asks to "review and walk me through this PR", "review this branch and explain
  the change", or "code review with a walkthrough".
---

# Code Review Walkthrough

Chains two existing skills: `/code-review` for findings, then `/html-walkthrough` for a visual explanation of the change. Adds one requirement on top of the walkthrough: it must present the pull request as a Before and After so the reader understands the problem it solves in full context.

Invocation: `/code-review-walkthrough [<PR#>|<branch>] [--level <low|medium|high>]` — arguments are passed straight through to `/code-review`. With no argument, both steps operate on the current branch's diff against its base branch (the open PR's base branch when one exists, otherwise the repo's default branch).

## Workflow

### Step 1: Run the code review

Invoke `/code-review` via the Skill tool, forwarding any target or level arguments the user provided. Let it complete and report its findings as it normally would. Do not re-implement or summarize the review logic here.

### Step 2: Gather the change's context

Before invoking the walkthrough, collect what the walkthrough will need to explain the Before and After:

- The diff and commit messages for the reviewed target.
- The PR title, body, and linked ticket if a PR exists (`gh pr view`), since these usually state the intended problem directly.
- The pre-change version of the touched code paths (`git show <base>:<path>`), so the "before" behavior is grounded in the actual source rather than inferred from the diff alone.

### Step 3: Run the HTML walkthrough

Invoke `/html-walkthrough` via the Skill tool with the topic set to the reviewed change (e.g. "the change in PR #123" or "the diff on branch `feat/foo` against `main`"), and instruct it to structure the walkthrough as a Before and After. All existing `/html-walkthrough` rules (research, conciseness, visual-first, grounding) apply unchanged; the only additions are the sections below.

The walkthrough must include, in this order:

1. **The problem.** One or two sentences on what was broken, missing, or hard before this change, and why it mattered. Pull this from the PR description, ticket, and commit messages; verify against the code.
2. **Before.** How the relevant flow worked prior to the change, built from the base-branch version of the code. Use a diagram (flow chart or step list) for the old path and point out exactly where the problem showed up.
3. **After.** How the same flow works with the change applied, using a parallel diagram so the reader can compare the two directly. Highlight the specific steps that changed.
4. **What changed and why.** A short table or list mapping each meaningful change to the part of the problem it addresses. Skip mechanical churn (renames, formatting, moved imports).
5. **Review findings.** A brief section listing the `/code-review` findings from Step 1 with their file and line, so the reader sees the review and the explanation in one place. If the review had no findings, say so in one line.

### Step 4: Report

Return the Artifact link with a one-line description, and restate the count of review findings from Step 1.

## Constraints

- Do not duplicate the logic of `/code-review` or `/html-walkthrough` here — always invoke them via the Skill tool.
- The Before section must be derived from the base-branch source, never guessed from the diff's removed lines alone.
- Never fabricate the problem statement; if no PR description, ticket, or commit message states it, infer it from the code and label it as inferred.
