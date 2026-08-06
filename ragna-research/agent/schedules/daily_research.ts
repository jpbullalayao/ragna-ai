import { defineSchedule } from "eve/schedules";

/**
 * Example daily research schedule. Duplicate this file (or add a `.md` schedule)
 * for each topic — the prompt is the topic definition. Eve names the cron job
 * from the path (`daily_research`, `vercel_ai_sdk`, etc.).
 *
 * cron: "0 14 * * *" — standard 5-field cron (minute hour day-of-month month day-of-week).
 * Vercel evaluates in UTC, so this fires at 14:00 UTC every day
 * (≈ 07:00 US Pacific during PDT, ≈ 06:00 during PST).
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
