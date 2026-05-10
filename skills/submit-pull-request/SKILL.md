---
name: submit-pull-request
description: Open a GitHub pull request from the current branch using a fixed template (ticket, Problem, Solution, Before, After, Test plan). Use this skill whenever the user types `/submit-pull-request`, asks to "submit a PR", "open a PR", "create a pull request", "push this up as a PR", or otherwise wants a pull request created from the current branch — even if they don't explicitly mention the template. Always prefer this skill over writing an ad-hoc PR description.
---

# Submit Pull Request

Create a pull request from the current branch with a consistent body template. The template is non-negotiable: every PR opened through this skill uses the same six sections in the same order so reviewers always know where to look.

## When to invoke

Trigger on any of:
- `/submit-pull-request`
- "submit a pull request" / "submit a PR"
- "open a PR" / "create a PR" / "create a pull request"
- "push this up as a PR" / "turn this branch into a PR"

If the user is clearly asking for a PR but is on `main` (or the repo's default branch), stop and ask which branch they want to PR — do not create a PR from the default branch.

## Workflow

1. **Confirm the branch is ready.** Run in parallel:
   - `git status` — check for uncommitted changes. If there are any, ask the user whether to commit them first or proceed without them.
   - `git branch --show-current` — capture the branch name.
   - `git log <base>..HEAD --oneline` — review the commits that will be in the PR. Use the repo's default branch as `<base>` (usually `main`; check with `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` if unsure).
   - `git diff <base>...HEAD` — read the diff so you can write a real Problem/Solution. Skim, don't dump.

2. **Push the branch if needed.** If `git status` shows the branch isn't tracking a remote or is ahead of remote, push with `git push -u origin <branch>`.

3. **Infer the ticket reference from the branch name.** Common patterns:
   - `KOR-123-some-description` or `kor-123-...` → ticket `KOR-123`
   - `feature/KOR-123-...`, `fix/KOR-123-...` → ticket `KOR-123`
   - `<user>/KOR-123-...` (e.g. `jourdan/KOR-123-foo`) → ticket `KOR-123`
   - `fix/some-description` (no ticket id) → no ticket; leave the line as `_No ticket_`

   If the user mentions a ticket in conversation (e.g. "this is for KOR-456"), prefer that over what's in the branch name.

4. **Draft the title.** Keep under 70 characters. Use Conventional Commits style (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`) matching what the repo's recent commits use. Title should describe the change, not the ticket id.

5. **Fill the template.** Use the exact structure in [The template](#the-template) below. Sections marked "leave empty" must be empty — the user will paste media in afterward.

6. **Create the PR.** Run `gh pr create --title "<title>" --body "<body>"`. Pass the body as a plain `-m`-style string (no HEREDOC, no command substitution — those trip the permission scanner). If the body contains characters that need escaping, write it to a temp file first and use `--body-file`.

7. **Return the PR URL** so the user can open it and paste in the Before/After media.

## The template

Every PR body produced by this skill MUST follow this exact structure, in this order:

```markdown
**Ticket:** <ticket reference, or _No ticket_>

## Problem

<1–3 sentences describing what was wrong or missing before this change. Derive from the diff and commit messages — focus on *why* the change was needed, not what files moved.>

## Solution

<1–3 sentences (or short bullets) describing what this PR does to fix it. Focus on the approach, not a file-by-file changelog.>

## Before

<!-- Screenshot or recording of the prior behavior. Leave blank — the author will paste media here. -->

## After

<!-- Screenshot or recording of the new behavior. Leave blank — the author will paste media here. -->

## Test plan

- [ ] <verification step 1>
- [ ] <verification step 2>
- [ ] <verification step 3>
```

### Why each section exists

- **Ticket** — links the PR to the work item so reviewers and future readers can find the original context.
- **Problem** — forces the author to articulate the user-visible or system-level issue, not just the code change.
- **Solution** — gives reviewers a one-paragraph mental model before they start reading the diff.
- **Before / After** — empty by design. The skill cannot capture screenshots or recordings; the author fills these in after the PR is opened. Keep the HTML comment so the author sees a hint when editing.
- **Test plan** — concrete steps a reviewer (or the author) can run to verify the change. Bullets should be checkable, not vague ("works correctly" is not a test plan).

## Filling Problem / Solution / Test plan well

Read the diff and commits before writing — these sections should reflect the actual change, not boilerplate.

- **Problem**: lead with the user/system impact. "Contract preview didn't render after refresh because the active tab wasn't set on initial derivation" is good. "Updated some logic in chat-tabs.tsx" is bad.
- **Solution**: describe the mechanism in plain language. "Activate the derived tab as soon as derivation completes" is good. "Added a useEffect" is bad.
- **Test plan**: prefer steps a human can follow in the running app or repo. Include relevant commands (`pnpm typecheck`, `pnpm test --filter=<pkg>`) and UI flows when the change is visual.

## Edge cases

- **No commits ahead of base** — stop and tell the user; nothing to PR.
- **Detached HEAD** — stop and tell the user; can't PR a detached HEAD.
- **`gh` not authenticated** — surface the `gh auth login` prompt to the user; don't try to authenticate on their behalf.
- **PR already exists for this branch** — `gh pr create` will fail. Run `gh pr view --json url -q .url` to surface the existing PR URL instead of creating a duplicate.
- **Stacked PRs (Graphite)** — if the repo uses `gt` and the user mentions a stack, defer to the `graphite` skill rather than calling `gh pr create` directly.

## Example

Branch: `fix/contract-preview-not-rendering-on-refresh`
Recent commits:
- `fix(chat): activate derived tab on initial derivation so reload renders the preview`
- `refactor(chat): simplify pdf tab activation by dropping pendingActiveTabIdRef`

Resulting PR body:

```markdown
**Ticket:** _No ticket_

## Problem

After refreshing a chat with a derived contract, the contract preview pane stayed blank because the derived tab was never activated on initial load — the user had to click the tab manually to see the preview.

## Solution

Activate the derived tab as soon as derivation completes (and on initial mount when a derived contract already exists), and drop the `pendingActiveTabIdRef` workaround that was masking the issue.

## Before

<!-- Screenshot or recording of the prior behavior. Leave blank — the author will paste media here. -->

## After

<!-- Screenshot or recording of the new behavior. Leave blank — the author will paste media here. -->

## Test plan

- [ ] Open a chat with a derived contract, hard-refresh, and confirm the contract preview renders without clicking the tab.
- [ ] Upload a new contract in a fresh chat and confirm the preview tab activates as soon as derivation finishes.
- [ ] `pnpm --filter=web typecheck` passes.
```
