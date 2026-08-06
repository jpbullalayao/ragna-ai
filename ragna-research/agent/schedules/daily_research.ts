import { defineSchedule } from "eve/schedules";

/**
 * Example daily research schedule. Duplicate this file (or add a `.md` schedule)
 * for each topic — the prompt is the topic definition. Eve names the cron job
 * from the path (`daily_research`, `vercel_ai_sdk`, etc.).
 */
export default defineSchedule({
  cron: "0 14 * * *",
  markdown: [
    "Conduct daily research on: **Replace this with your topic**.",
    "Load the `daily_research` skill and follow it end to end.",
    "Use browser tools to gather current information from the public web.",
    "Publish exactly one consolidated note with `publish_note`.",
  ].join("\n\n"),
});
