---
name: address-pr-comments
description: >-
  Fetch the pull request review comments for the current branch's PR (or a
  user-provided branch/PR number), assess whether each comment is valid and
  actionable, concisely report each problem and its anticipated solution, then
  implement the necessary fixes and push them to the PR. Use when the user
  types /address-pr-comments [<branch>|<PR#>], or asks to "address PR
  comments", "handle the review feedback", "fix the review comments", or
  "respond to my PR reviews". Invalid or out-of-scope comments are reported
  with reasoning but not acted on. Requires `gh` CLI authenticated to GitHub.
allowed-tools:
  - "Bash(gh *)"
  - "Bash(git *)"
---

# Address PR Comments

Analyzes all review feedback on a pull request, judges which comments are
valid, outlines the problems and planned fixes, then implements and pushes
the fixes to the PR branch.

## Workflow

### Step 1: Resolve the target PR

- No argument → use the current branch: `gh pr view --json number,title,url,state,headRefName,baseRefName`
- Argument is a branch name → `gh pr view <branch> --json ...`
- Argument is a number → `gh pr view <number> --json ...`

If no PR is found, tell the user and stop. If the PR is `MERGED`, tell the
user and stop. If `CLOSED`, warn and ask whether to continue.

If the resolved PR's head branch is not the currently checked-out branch,
check it out first (`git fetch && git checkout <headRefName>`). If the working
tree is dirty, stop and ask the user how to proceed rather than stashing.

Store: `PR_NUMBER`, `HEAD_BRANCH`, `BASE_BRANCH`, `PR_URL`.

### Step 2: Fetch all review feedback

Run in parallel:

```bash
gh api "repos/{owner}/{repo}/pulls/PR_NUMBER/comments" --paginate   # inline review comments
gh pr view PR_NUMBER --json reviews,comments                         # review bodies + conversation comments
```

Collect every distinct piece of feedback. For inline comments, capture the
file path, line, diff hunk, author, comment body, and whether the thread is
already resolved/outdated. Skip:

- Comments authored by bots that are pure noise (CI status, coverage bots)
  unless they describe a concrete code problem
- Threads already marked resolved
- Comments that are replies agreeing with or thanking another comment

If nothing actionable remains, tell the user "No unaddressed review comments
found on PR #N" and stop.

### Step 3: Assess validity

For each remaining comment, read the referenced code (and enough surrounding
context to judge properly) and classify it:

- **Valid** — the comment identifies a real bug, regression, convention
  violation, or clearly better approach. A fix is warranted.
- **Invalid** — the comment is factually wrong, based on a misreading, or the
  concern is already handled elsewhere in the code. No fix.
- **Judgment call / out of scope** — stylistic preference with no clear
  winner, or a request that expands the PR's scope. Default to **not** fixing
  these; note them for the user.
- **Question** — the reviewer is asking for clarification, not a change. No
  code fix; note it so the user can reply.

Judge each comment on its merits — do not assume the reviewer is right.
Equally, do not dismiss a comment just because the fix is inconvenient.

### Step 4: Report problems and planned fixes

**Before making any changes**, output a concise summary:

```
## Review Comment Analysis — PR #<number>

### Will fix (N)
1. `path/to/file.ts:42` — <one-line problem> (from @reviewer)
   → Fix: <one-line anticipated solution>
2. ...

### Won't fix (M)
1. `path/to/file.ts:10` — <one-line comment summary> (from @reviewer)
   → Reason: <invalid / out of scope / question — one line>
```

Keep each entry to the two lines shown — problem and solution/reason. No
diffs, no extended reasoning.

Then proceed directly to implementing the "Will fix" items — do not wait for
approval unless the user asked to review the plan first, or a fix is
destructive/risky (schema migrations, deletions of features, dependency
major bumps), in which case ask about that item.

### Step 5: Implement the fixes

For each "Will fix" item:

- Make the minimal change that addresses the reviewer's concern.
- Preserve all existing behavior not implicated by the comment.
- Match the surrounding code's style and conventions.

After all fixes, run the project's relevant checks if quickly discoverable
(lint, typecheck, tests touching the changed files). If a check fails because
of a fix, repair it before committing.

### Step 6: Commit and push

```bash
git add <changed files>
git commit -m "fix: address PR review comments"
git push
```

Use a more specific commit message when the fixes share a theme (e.g.
`fix: handle null dates in parser per review`). Never force-push.

### Step 7: Output summary

```
Addressed X of Y review comments on PR #<number>
  • Fixed: <one line per fix>
  • Not fixed: <one line per skipped comment with reason>
Pushed <commit sha> to <branch>
<PR URL>
```

Suggest the user reply to any "Question" comments and resolve the fixed
threads on GitHub.

## Constraints

- **`gh` auth is required.** Run `gh auth status` first; if unauthenticated,
  tell the user to run `gh auth login` and stop.
- **Always report the analysis (Step 4) before editing any file.**
- **Never fix comments judged invalid or out of scope** — report them instead.
- **Never force-push, amend published commits, or rebase.**
- **Never resolve review threads or reply to reviewers on GitHub** unless the
  user explicitly asks — the user should own the conversation with reviewers.
- **Never hardcode PR numbers, repos, or branch names** — derive everything
  from `gh`/`git` output.
