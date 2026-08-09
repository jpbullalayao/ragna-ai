import { connect } from "@vercel/connect/eve";
import { defineMcpClientConnection } from "eve/connections";

/**
 * Official Eve Notion connection (MCP via Vercel Connect).
 * App-scoped so schedules/cron can publish without an interactive user principal.
 *
 * Setup: from research-agent/, run `eve add connection/notion --skip-install`
 * (or `vercel connect create notion`) and share the target Notion pages with the
 * connected integration.
 */
export default defineMcpClientConnection({
  url: "https://mcp.notion.com/mcp",
  description: "Notion workspace: search and edit pages and databases.",
  auth: connect({ connector: "notion", principalType: "app" }),
});
