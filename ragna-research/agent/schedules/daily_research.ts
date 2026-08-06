import { defineSchedule } from "eve/schedules";

const topic =
  process.env.RESEARCH_TOPIC?.trim() ||
  "(unset — configure RESEARCH_TOPIC on the deployment)";

export default defineSchedule({
  cron: "0 14 * * *",
  markdown: [
    `Conduct daily research on: **${topic}**.`,
    "Load the `daily_research` skill and follow it end to end.",
    "Use browser tools to gather current information from the public web.",
    "Publish exactly one consolidated note with `publish_note`.",
  ].join("\n\n"),
});
