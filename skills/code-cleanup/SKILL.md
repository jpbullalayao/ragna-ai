---
name: code-cleanup
description: >-
  Analyze the current branch's diff against main (or a user-specified branch)
  and auto-fix cleanup opportunities across three areas: code brevity & quality,
  potential regressions, and CI/build health. Use when the user runs
  /code-cleanup [<branch>], or asks to "clean up the code", "simplify these
  changes", or "polish this branch". Outlines findings per area to the user
  before applying fixes. Auto-fixes meet the bar a staff-level engineer would
  approve — conservative, behavior-preserving, and clearly motivated. For large
  diffs (>300 lines or >15 files), invokes /simplify first. For React files in
  the diff, invokes /react-doctor before applying fixes.
allowed-tools:
  - "Bash(git fetch *)"
  - "Bash(git log *)"
  - "Bash(git diff *)"
  - "Bash(git status *)"
  - "Bash(git rev-parse *)"
  - "Bash(git merge-base *)"
  - "Bash(git show *)"
  - "Bash(git branch *)"
  - "Bash(find *)"
  - "Bash(grep *)"
  - "Bash(cat *)"
  - "Bash(npm run *)"
  - "Bash(npx *)"
  - "Bash(yarn *)"
  - "Bash(pnpm *)"
  - "Read"
  - "Edit"
---

# Code Cleanup

Analyzes the current branch's diff and auto-applies targeted, conservative fixes across code brevity & quality, regression risks, and CI/build health. **Mutates the working tree** — all edits are applied inline using the Edit tool.

Invocation: `/code-cleanup` (compares against `origin/main` by default) or `/code-cleanup <branch>` to compare against a specific branch.

## Workflow

### Step 1: Parse invocation and establish baseline

Check if a branch argument was provided (e.g. `/code-cleanup feature/foo`). If not, determine the default base:
1. Try `origin/main`
2. Fall back to `origin/master` if `main` doesn't exist
3. Fall back to local `main`/`master` with a note if no remote is reachable

Run in parallel:

```bash
git rev-parse --abbrev-ref HEAD
git fetch origin <base-branch> --quiet
git status --short
```

- If currently on `main` or `master`, stop and tell the user to switch to a feature branch.
- If `git status` shows uncommitted changes unrelated to the diff (i.e., files not in the branch diff), warn the user and ask whether to proceed.

Then compute the merge base:

```bash
git merge-base origin/<base-branch> HEAD
```

Store the resulting SHA as `BASE`.

### Step 2: Gather diff context

Run in parallel:

```bash
git diff --stat <BASE>..HEAD
git diff --name-status <BASE>..HEAD
git diff <BASE>..HEAD
git log <BASE>..HEAD --oneline
```

- If the diff is empty, stop and tell the user there is nothing to clean up.
- Compute `LINE_COUNT` (sum of `+` and `-` lines from `--stat`) and `FILE_COUNT` (count of changed files from `--name-status`).

### Step 3: Detect CI and build tooling

Run in parallel:

```bash
find . -maxdepth 2 -name "package.json" -not -path "*/node_modules/*"
find . -maxdepth 3 -path "./.github/workflows/*.yml"
find . -maxdepth 2 -name "tsconfig.json" -not -path "*/node_modules/*"
```

From `package.json` scripts, identify commands for `build`, `type-check` / `typecheck` / `tsc`, and `lint`. Store as `BUILD_CMD`, `TYPECHECK_CMD`, and `LINT_CMD`. If no `TYPECHECK_CMD` is found but a `tsconfig.json` exists, fall back to `npx tsc --noEmit`.

### Step 4: Invoke /simplify if diff is large

If `LINE_COUNT > 300` OR `FILE_COUNT > 15`:
- Invoke `/simplify` via the Skill tool.

### Step 5: Invoke /react-doctor if React files are in the diff

Check whether any file in `git diff --name-status <BASE>..HEAD` has a `.tsx` or `.jsx` extension, or is a `.ts`/`.js` file containing a React component definition (look for `React`, `JSX`, `export default function`, `const ... = () => <` patterns in the diff).

If yes:
- Invoke the `/react-doctor` skill via the Skill tool to get React-specific analysis (hook correctness, component structure, rendering patterns) against real React expertise.
- Capture its findings — they feed into Pass A below, annotated `[REACT]`.

If no React files are present in the diff, skip this step.

### Step 6: Analysis pass A — Code brevity & quality

Scan the diff additions for:

- **Unnecessary intermediate variables** — `const x = expr; return x;` should be `return expr;`
- **Redundant type assertions** — casts that TypeScript already infers from context
- **Verbose boolean patterns** — `if (x === true)` → `if (x)`, `x === false` → `!x`
- **Dead code paths** — branches added in this diff that can never be reached (e.g. `if (false)`, exhausted enum/union checks)
- **Over-extracted one-liners** — new helper functions called exactly once in the diff that add no clarity
- **Unnecessary async/await wrappers** — `async () => await expr` where no error boundary or intermediate await is needed; → `() => expr`
- **Any other obvious verbosity** that a simpler, equivalent expression would replace without behavior change
- **Architectural improvements** — if a simpler or more logical structure would make the code meaningfully better or clearer, even if it requires restructuring, include it as `[ARCH]`; always show a before/after snapshot to the user before applying
- **React-specific findings** from Step 5, annotated `[REACT]`

**Fix classification:**
- `[AUTO]` — syntactically unambiguous, zero behavior change; apply immediately with Edit
- `[ARCH]` — architectural improvement making code logically better/simpler; present before/after inline, then apply
- `[MANUAL]` — requires human judgment; surface it, do not apply

Present findings before applying any fixes:

```
### A. Code Brevity & Quality
- `path/to/file.ts:42` — [AUTO] Unnecessary intermediate: `const x = ...; return x` → `return ...`
- `path/to/file.ts:18` — [ARCH] <description>
  Before: <snippet>
  After: <snippet>
- `path/to/file.ts:77` — [REACT] [AUTO] <React-specific finding and fix>
- `path/to/file.ts:99` — [MANUAL] <finding requiring human judgment>
(or: Nothing to clean up.)
```

Then apply all `[AUTO]` and `[ARCH]` fixes using the Edit tool. After all fixes in this pass, run `TYPECHECK_CMD` and report the result. If type checking fails, fix the error before continuing.

### Step 7: Analysis pass B — Regression risks

Scan the diff for changes that could silently break existing callers or behavior:

- **Removed or narrowed exports** — grep the repo for anything removed from the diff to confirm no other file imports it (`grep -r "<symbol>" --include="*.ts" --include="*.tsx"`)
- **Signature changes** — new required parameters added, return types changed; grep callers to confirm they were all updated
- **Renamed or moved files** — grep for the old import path to confirm all references were updated
- **Narrowed conditionals** — `if (a || b)` → `if (a)` without a corresponding change at all call sites
- **Removed enum cases or union members** — check for exhaustive switches over the affected type
- **Behavior changes in shared utilities** — any change to a function used outside the diff

**Fix classification:**
- `[AUTO]` — mechanical, unambiguous (e.g. updating an import path for a rename already present in the diff)
- `[MANUAL]` — anything requiring judgment (e.g. restoring a removed branch, reverting a narrowed conditional); surface with a clear warning, do not apply

Present findings:

```
### B. Regression Risks
- `path/to/file.ts:20` — [AUTO] <finding and fix>
- `path/to/file.ts:55` — [MANUAL] <warning — requires human review>
(or: None spotted.)
```

Apply `[AUTO]` items. After fixes, re-run `TYPECHECK_CMD` and report the result.

### Step 8: Analysis pass C — CI / build health

Scan the diff for issues that would fail CI:

- **TypeScript type errors** visible from the diff context — missing required props, wrong argument types, values that may be `null`/`undefined` where non-nullable is expected
- **Missing imports** — newly used symbols that are not imported in the same file
- **Unused imports** — imports added (or left orphaned) by the diff that are no longer referenced
- **Broken test references** — if the diff renames or removes a function, check test files for references to the old name

**Fix classification:**
- `[AUTO]` — clearly broken and mechanically fixable (add missing import, remove unused import, fix a type error the compiler catches)
- `[MANUAL]` — requires judgment (e.g. a type error that implies a logic fix, not just a cast)

Do not auto-fix lint style opinions — only mechanical correctness issues that a compiler or CI step would fail on.

Present findings:

```
### C. CI / Build Health
- `path/to/file.ts:10` — [AUTO] <finding and fix>
- `path/to/file.ts:77` — [MANUAL] <warning requiring human action>
(or: None spotted.)
```

Apply `[AUTO]` items. After fixes, run `TYPECHECK_CMD`. Also run `BUILD_CMD` unless the script name suggests a slow production bundle (e.g. contains `prod`, `deploy`, or `release`).

### Step 9: Final verification and summary

Run `TYPECHECK_CMD` (and `BUILD_CMD` if applicable) one final time.

If any verification step fails: do **not** leave the working tree in a broken state. Report the failure with full error output, attempt a mechanical fix, and if not automatically resolvable, tell the user exactly what to address.

Output:

```
## Code Cleanup Summary

**Branch:** <current> vs <base-branch>
**Diff:** <LINE_COUNT> lines across <FILE_COUNT> files

### Applied Fixes
- [A] Code Brevity & Quality: N fix(es) applied
- [B] Regression Risks: M fix(es) applied, K item(s) flagged [MANUAL]
- [C] CI / Build Health: P fix(es) applied, Q item(s) flagged [MANUAL]

### Manual Items Requiring Attention
- `path/to/file.ts:55` — [B] <description>
- `path/to/file.ts:77` — [C] <description>

### Verification
- Type check: PASS / FAIL
- Build: PASS / FAIL / SKIPPED
```

---

## Constraints

- **Conservative by default.** Only auto-fix patterns that are syntactically unambiguous and cannot change runtime behavior. When in doubt, flag `[MANUAL]`.
- **Architectural improvements are allowed** when they make code logically better or simpler — always show a before/after to the user as part of the output before applying. Never apply architectural changes silently.
- **Never touch files outside the diff.** Only edit files that appear in `git diff --name-status <BASE>..HEAD`.
- **Verify after each pass.** Run type checks after Pass A, B, and C. A broken type check must be addressed before moving to the next pass.
- **No style opinions.** Do not auto-fix formatting, naming conventions, or patterns that a linter already catches. Focus on substance.
- **[MANUAL] items are never silently dropped.** Every regression risk or judgment call must appear in the summary output so the user can act on it.
- **Respect working tree state.** If `git status` shows uncommitted changes unrelated to the diff, warn the user and ask whether to proceed before making any edits.
- **Never run destructive git commands.** No `checkout`, `reset`, `stash`, `commit`, or `push`.
