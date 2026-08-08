import type { NotesDestination, PublishNoteInput } from "../types.js";

/** Supports native `markdown` on page create (tables, lists, links). */
const NOTION_VERSION = "2026-03-11";
const MAX_TEXT_LENGTH = 2000;
const ASYNC_MARKDOWN_THRESHOLD = 8000;

type NotionRichText = { type: "text"; text: { content: string } };

function chunkText(text: string): string[] {
  const chunks: string[] = [];
  for (let i = 0; i < text.length; i += MAX_TEXT_LENGTH) {
    chunks.push(text.slice(i, i + MAX_TEXT_LENGTH));
  }
  return chunks.length > 0 ? chunks : [""];
}

function richText(content: string): NotionRichText[] {
  return chunkText(content).map((c) => ({
    type: "text",
    text: { content: c },
  }));
}

/** Drop leading H1 when the page title is set separately in properties. */
function bodyMarkdown(markdown: string, tags?: string[]): string {
  let md = markdown.replace(/\r\n/g, "\n").replace(/^#\s+.+\n?/, "").trim();
  if (tags?.length) {
    md += `\n\n---\n\nTags: ${tags.join(", ")}`;
  }
  return md;
}

type AsyncTaskResponse = {
  object?: string;
  id?: string;
  status?: string;
  poll_after_seconds?: number;
  result?: { object?: string; id?: string; url?: string };
  error?: { message?: string };
};

async function pollAsyncTask(
  apiKey: string,
  taskId: string,
): Promise<{ id: string; url?: string }> {
  const maxAttempts = 90;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const res = await fetch(`https://api.notion.com/v1/async_tasks/${taskId}`, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Notion-Version": NOTION_VERSION,
      },
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Notion async task poll error (${res.status}): ${detail}`);
    }
    const task = (await res.json()) as AsyncTaskResponse;
    if (task.status === "succeeded") {
      const pageId = task.result?.id;
      if (!pageId) {
        throw new Error("Notion async task succeeded but returned no page id");
      }
      return { id: pageId, url: task.result?.url };
    }
    if (task.status === "failed") {
      throw new Error(
        `Notion async task failed: ${task.error?.message ?? "unknown error"}`,
      );
    }
    const waitSec = task.poll_after_seconds ?? 2;
    await new Promise((resolve) => setTimeout(resolve, waitSec * 1000));
  }
  throw new Error("Notion async page create timed out");
}

async function createNotionPage(
  apiKey: string,
  parentPageId: string,
  title: string,
  markdown: string,
): Promise<{ id: string; url?: string }> {
  const body: Record<string, unknown> = {
    parent: { page_id: parentPageId },
    properties: {
      title: {
        title: richText(title),
      },
    },
    markdown,
  };
  if (markdown.length >= ASYNC_MARKDOWN_THRESHOLD) {
    body.allow_async = true;
  }

  const res = await fetch("https://api.notion.com/v1/pages", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Notion-Version": NOTION_VERSION,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (res.status === 202) {
    const task = (await res.json()) as AsyncTaskResponse;
    if (!task.id) {
      throw new Error("Notion returned async task without id");
    }
    return pollAsyncTask(apiKey, task.id);
  }

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Notion API error (${res.status}): ${detail}`);
  }

  const data = (await res.json()) as { id: string; url?: string };
  return { id: data.id, url: data.url };
}

export function createNotionDestination(): NotesDestination | null {
  const apiKey = process.env.NOTION_API_KEY?.trim();
  const parentPageId = process.env.NOTION_PARENT_PAGE_ID?.trim();
  if (!apiKey || !parentPageId) return null;

  return {
    id: "notion",
    async publish(input: PublishNoteInput) {
      const datePrefix = input.date ? `[${input.date}] ` : "";
      const title = `${datePrefix}${input.title}`.slice(0, 2000);
      const markdown = bodyMarkdown(input.markdown, input.tags);
      return createNotionPage(apiKey, parentPageId, title, markdown);
    },
  };
}
