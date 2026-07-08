---
name: root-cause
description: Finds, fixes, and verifies the underlying root cause of a task or bug rather than applying a surface band-aid. Reasons with itself to confirm the chosen fix addresses the problem at its root before implementing. Use when the user invokes /root-cause <query>, asks to fix or get to the root cause or bottom of a specific bug, or asks to check or confirm that a fix actually resolved the root cause.
---

# Root Cause

Addresses a specific task or bug by tracing to and fixing the true underlying cause — not the symptom. Before implementing, the agent must reason with itself to confirm the chosen fix is root-level, not a band-aid.

Invocation: `/root-cause <query>` — the text after the command is the task or bug to address.

## Step 1: Understand the task

- Parse `<query>` into: the goal, the symptom or failure, and any constraints the user stated.
- Reproduce or locate exactly where the problem manifests — error message, failing test, wrong output, broken flow.
- Gather context with read-only tools before changing anything. Read the relevant code paths, callers, and recent changes.

## Step 2: Trace to the origin

Follow the causal chain upstream — ask "why does this happen?" repeatedly — until you reach the deepest controllable cause in the codebase.

- **Symptom site** — where the problem is visible (error thrown, wrong value rendered, test fails).
- **Cause site** — where the incorrect assumption, missing invariant, bad data, or broken contract originates.

Do not stop at the first broken line. Keep tracing until you hit the layer that, if fixed, would prevent this class of problem — not just this instance.

## Step 3: The band-aid vs root test

Before committing to a fix, interrogate the proposed approach:

1. Does this fix the **cause** or hide the **symptom**?
2. Would it prevent the **whole class** of this bug, or only this one instance?
3. Are there **other symptoms** of the same cause that this leaves unfixed?
4. If the fix is at the symptom site, what would have to be true for that to be the **correct** root-level fix?

**Decision:**

- If the fix addresses the root → proceed to Step 4.
- If it does not → redesign. Trace further upstream or rethink the approach. Do not implement a band-aid without explicit acknowledgment.

## Step 4: Implement the root fix

- Make the **minimal correct change** at the cause site.
- Follow existing codebase conventions — reuse shared utilities and patterns where they exist.
- If the true root is genuinely out of scope (third-party dependency, large refactor, explicit user constraint):
  - State the real root cause plainly.
  - Apply a clearly labeled **guarded mitigation** (not a silent band-aid).
  - Note the recommended follow-up to address the root properly.

## Step 5: Verify and sweep

- Confirm the original task from `<query>` is resolved.
- Check for **sibling symptoms** of the same cause elsewhere in the codebase.
- Run or adjust relevant tests to cover the root fix, not just the symptom path.

## Constraints

- **Fix at the root by default.** The goal is a durable fix, not a patch that papers over the symptom.
- **Never ship a band-aid silently.** If forced to mitigate instead of fix, label it explicitly and flag the real root cause.
- **Ground everything.** Every path, function, and claim must trace to the actual codebase — no invented references.
- **Keep changes minimal and conventional.** Fix the cause without unrelated refactors; match how the repo already solves similar problems.
- **Be decisive but flexible.** Pivot to the root fix by default; defer to an explicit user constraint while surfacing what is being left unaddressed.