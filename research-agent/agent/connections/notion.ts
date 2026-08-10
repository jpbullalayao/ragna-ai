import { connect } from "@vercel/connect/eve";
import { defineMcpClientConnection } from "eve/connections";

/**
 * Notion MCP via Vercel Connect.
 *
 * Connector UID must match the Connect client (`notion/notion` when created with
 * `--name notion`). User-scoped: authorize with
 * `vercel connect token notion/notion --yes`, then share target pages with the
 * integration. Full setup: README "Notion connection".
 */
export default defineMcpClientConnection({
  url: "https://mcp.notion.com/mcp",
  description: "Notion workspace: search and edit pages and databases.",
  auth: connect("notion/notion"),
});
