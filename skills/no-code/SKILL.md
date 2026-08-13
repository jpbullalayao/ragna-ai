---
name: no-code
description: >-
  Answer the user's query with an explanation only — do not apply any code
  changes. Use only when the user explicitly includes /no-code in their
  message, before or after the query.
disable-model-invocation: true
---

# No Code

Answer the user's query without applying any code changes. The query is the
rest of the message around `/no-code` — it may come before or after the
marker (e.g. "<query> /no-code" or "/no-code <query>").

## Rules

1. Provide your answer as prose — illustrative code snippets are fine. Do not
   create, edit, or delete any files, and do not apply any code changes.
2. If the answer would naturally involve a fix or implementation, describe the
   approach instead of implementing it.

If the message contains no query besides `/no-code` itself, respond:

```text
Usage: /no-code <query>
```
