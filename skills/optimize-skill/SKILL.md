---
name: optimize-skill
description: >-
  Review a single agent skill's SKILL.md and improve it — find redundancies,
  contradictions, ambiguity, and fluff, then apply behavior-preserving rewrites
  for concise, clear instructions. Outlines findings before applying. Use when
  the user types /optimize-skill, or asks to "optimize this skill", "improve
  this skill", "tighten this skill", or "clean up this skill".
allowed-tools:
  - "Read"
  - "Edit"
  - "Write"
  - "Bash(ls *)"
  - "Bash(find *)"
  - "Bash(grep *)"
---

# Optimize Skill

Reviews one `SKILL.md`, finds opportunities to make it clearer and more concise, presents them, then applies the improvements — preserving exactly what the skill does.

Invocation: `/optimize-skill [<skill-name|path>]`.

## Target resolution

- **Arg given** — resolve to a single `SKILL.md`:
  - If it ends in `.md` or points to a directory, treat it as a path.
  - Otherwise search common locations for a matching skill directory (e.g. `skills/<arg>/SKILL.md`, `.claude/skills/<arg>/SKILL.md`, `~/.claude/skills/<arg>/SKILL.md`), then fall back to `find . -path "*<arg>*/SKILL.md"`.
- **No arg** — use `./SKILL.md` in the current directory.
- **Zero or multiple matches** — ask the user which one. Never guess.

## Guiding principle

Optimization is **behavior-preserving**: an agent reading the optimized skill must execute it identically to the original. Trim wording — never drop an actionable instruction, trigger phrase, constraint, or tool. Keep the frontmatter's `name` and `allowed-tools` intact; the `description` triggers may be tightened but never removed. When unsure whether something is fluff or load-bearing, keep it.

## What to look for

Improve clarity, concision, and executability. Common opportunities:

- **Redundancy** — the same rule, fact, or instruction stated in more than one place. Keep the single clearest statement; cross-reference instead of repeating.
- **Contradictions** — instructions that conflict. Surface both and propose the resolution matching the skill's evident intent; if genuinely unresolvable, flag it for the user rather than pick silently.
- **Fluff** — filler with no operational effect (motivational preamble, hedging, restating the obvious). Remove or compress.
- **Verbosity** — multi-sentence guidance that reduces to one tight sentence or bullet.
- **Ambiguity** — vague instructions an agent could reasonably execute more than one way. Make them precise.
- **Structure** — related guidance scattered across sections, or ordering that doesn't match the workflow. Consolidate and reorder.

Use judgment beyond this list — anything that makes the skill clearer to an agent without changing what it does is fair game.

## Workflow

1. **Resolve target** per the rules above and `Read` the full `SKILL.md`.
2. **Analyze** — build a findings list, each a one-line description of the improvement and where it applies.
3. **Present** the findings to the user as a concise outline. Note any contradiction that lacks a clear resolution as needing a human call.
4. **Apply** — `Edit` the file with the improvements. Preserve every unique instruction, trigger, tool, and necessary section. Leave unresolvable contradictions untouched and clearly called out.
5. **Sanity check** — frontmatter still valid (`name` unchanged, `allowed-tools` intact, `description` still carries its triggers); every actionable instruction from the original still present somewhere.

## Report

Summarize what changed, note anything left for the user (unresolved contradictions), and give a rough before/after size delta.
