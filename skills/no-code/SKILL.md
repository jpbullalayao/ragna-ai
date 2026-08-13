---
name: no-code
description: >-
  Answer the user's query with an explanation only — do not apply any code
  changes. Use only when the user explicitly invokes /no-code <query>.
disable-model-invocation: true
---

# No Code

Answer the query after `/no-code` without applying any code changes.

## Rules

1. Provide your answer as prose — illustrative code snippets are fine. Do not
   create, edit, or delete any files, and do not apply any code changes.
2. If the answer would naturally involve a fix or implementation, describe the
   approach instead of implementing it.

If no query follows `/no-code`, respond:

```text
Usage: /no-code <query>
```
