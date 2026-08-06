---
description: Run the daily research workflow — browse sources, synthesize findings, and publish one note to configured destinations.
---

When executing daily research:

1. Confirm the topic from the session prompt or `RESEARCH_TOPIC`.
2. Search and read a small set of high-signal sources (browser tools or web search if available).
3. Draft a markdown note with:
   - `# Daily research — <topic> — <date>`
   - **Summary** (3–5 sentences)
   - **Key developments** (bulleted)
   - **Sources** (linked list)
   - **Open questions** (bulleted)
4. Call `publish_note` with a short title and the full markdown body.
5. Report where the note was published (URLs from tool output) or the configuration error if publish failed.

Keep the note concise but actionable. Avoid duplicate publishes in the same run.
