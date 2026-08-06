import { defineTool } from "eve/tools";
import { z } from "zod";
import { getActiveDestinations } from "../lib/notes/registry.js";

export default defineTool({
  description:
    "Publish a research note to configured notes destinations (Notion and future adapters).",
  inputSchema: z.object({
    title: z.string().min(1),
    markdown: z.string().min(1),
    tags: z.array(z.string()).optional(),
    destinations: z
      .array(z.string())
      .optional()
      .describe("Optional subset of destination ids; defaults to all active."),
  }),
  async execute(input) {
    const active = getActiveDestinations();
    if (active.length === 0) {
      return {
        ok: false as const,
        error:
          "No notes destinations configured. Set NOTION_API_KEY and NOTION_PARENT_PAGE_ID (see docs/SETUP_TODO.md).",
      };
    }

    const selected = input.destinations?.length
      ? active.filter((d) => input.destinations!.includes(d.id))
      : active;

    if (selected.length === 0) {
      return {
        ok: false as const,
        error: `No matching destinations. Active: ${active.map((d) => d.id).join(", ")}`,
      };
    }

    const date = new Date().toISOString().slice(0, 10);
    const published = await Promise.all(
      selected.map(async (destination) => {
        try {
          const result = await destination.publish({
            title: input.title,
            markdown: input.markdown,
            tags: input.tags,
            date,
          });
          return { destination: destination.id, ok: true as const, ...result };
        } catch (err) {
          const message = err instanceof Error ? err.message : String(err);
          return {
            destination: destination.id,
            ok: false as const,
            error: message,
          };
        }
      }),
    );

    const allOk = published.every((p) => p.ok);
    return { ok: allOk, published };
  },
});
