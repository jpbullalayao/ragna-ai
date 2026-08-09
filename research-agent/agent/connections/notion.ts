import { connect } from "@vercel/connect/eve";
import { defineMcpClientConnection } from "eve/connections";

/**
 * Official Eve Notion connection (MCP via Vercel Connect).
 * User-scoped: Notion MCP via this connector does not mint app tokens yet.
 * Authorize once (eve TUI / `vercel connect token notion/notion --yes`), then
 * share target pages with the connected integration.
 *
 * Setup (from research-agent/):
 *   vercel connect create notion --connection-method mcp --name notion
 *   vercel connect attach notion/notion
 *   vercel env pull .env.local
 */
export default defineMcpClientConnection({
  url: "https://mcp.notion.com/mcp",
  description: "Notion workspace: search and edit pages and databases.",
  auth: connect("notion/notion"),
});
