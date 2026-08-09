import { defineSchedule } from "eve/schedules";

/**
 * Daily investment-research cron. Topic and workflow live in the skill — this
 * schedule only kicks off the run. Duplicate this file pattern for other
 * daily skills (new filename → new cron job name in Eve/Vercel).
 *
 * cron: "0 14 * * *" — minute hour day-of-month month day-of-week (UTC on Vercel).
 * 14:00 UTC ≈ 07:00 US Pacific (PDT) / 06:00 (PST).
 */
const parentPageId = process.env.NOTION_PARENT_PAGE_ID?.trim();

export default defineSchedule({
  cron: "0 14 * * *",
  markdown: [
    "Run today's scheduled research workflow.",
    "Load the `daily_investment_research` skill and follow it end to end.",
    "Use browser tools as the skill directs.",
    "Publish exactly one consolidated note to Notion using the Notion connection tools (`notion__*`), not a custom publish tool.",
    parentPageId
      ? `Create the page under Notion parent page id \`${parentPageId}\`.`
      : "If `NOTION_PARENT_PAGE_ID` is unset, search Notion for an appropriate parent page the integration can write to, or stop with a clear configuration error.",
  ].join("\n\n"),
});
