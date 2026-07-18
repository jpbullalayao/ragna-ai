---
name: optimize-skill
description: >-
  Review a single agent skill's SKILL.md and tighten it — flag internal
  redundancies, contradictions, and fluff, then apply behavior-preserving
  rewrites for concise, clear instructions. Outlines findings before applying.
  Use when the user types /optimize-skill, or asks to "optimize this skill",
  "tighten this skill", "trim this skill", or "clean up this skill's
  instructions".
allowed-tools:
  - "Read"
  - "Edit"
  - "Write"
  - "Bash(ls *)"
  - "Bash(find *)"
  - "Bash(grep *)"
---

# Optimize Skill

Reviews one `SKILL.md`, flags internal conflicts, redundancies, and fluff, then rewrites it for concise, clear instructions — preserving exactly what the skill does.

Invocation: `/optimize-skill [<skill-name|path>]`.

## Target resolution

- **Arg given** — resolve to a single `SKILL.md`:
  - If it ends in `.md` or points to a directory, treat it as a path.
  - Otherwise search in order: `skills/<arg>/SKILL.md`, `~/.claude/skills/<arg>/SKILL.md`, then `find . -path "*<arg>*/SKILL.md"`.
- **No arg** — use `./SKILL.md` in the current directory.
- **Zero or multiple matches** — ask the user which one (AskUserQuestion). Never guess.

## Guiding principle

Optimization is **behavior-preserving**: an agent reading the optimized skill must execute it identically to the original. Trim wording — never drop an actionable instruction, trigger phrase, constraint, or tool. Frontmatter `name` and `allowed-tools` stay intact; `description` triggers may be tightened but never removed. When unsure whether something is fluff or load-bearing, keep it.

## What to flag (within the target skill only)

- **[REDUNDANCY]** — the same rule, fact, or instruction stated in more than one place. Keep the single clearest statement; cross-reference instead of repeating.
- **[CONFLICT]** — instructions that contradict each other. Surface both and propose the resolution matching the skill's evident intent; if genuinely unresolvable, flag it for the user rather than pick silently.
- **[FLUFF]** — filler with no operational effect (motivational preamble, hedging, restating the obvious). Remove or compress.
- **[VERBOSITY]** — multi-sentence guidance that reduces to one tight sentence or bullet.

## Workflow

1. **Resolve target** per the rules above and `Read` the full `SKILL.md`.
2. **Analyze** — build a findings list, each tagged `[REDUNDANCY]` / `[CONFLICT]` / `[FLUFF]` / `[VERBOSITY]` with a one-line description and the section it lives in.
3. **Present** the findings to the user as a concise outline grouped by tag. Mark any `[CONFLICT]` lacking a clear resolution as needing a human call.
4. **Apply** — `Edit` the file to remove redundancy and fluff and tighten wording. Preserve every unique instruction, trigger, tool, and structural section. Leave unresolvable conflicts untouched and clearly called out.
5. **Sanity check** — frontmatter still valid (`name` unchanged, `allowed-tools` intact, `description` still carries its triggers); every actionable instruction from the original still present somewhere.

## Report

Summarize counts per category, note anything left for the user (unresolved conflicts), and give a rough before/after size delta.

## Constraints

- Behavior-preserving — never invent new instructions or remove a trigger phrase or tool.
- State each rule once.
- When in doubt whether something is fluff or load-bearing, keep it.
