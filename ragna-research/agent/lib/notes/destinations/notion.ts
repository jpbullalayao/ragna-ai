import type { NotesDestination, PublishNoteInput } from "../types.js";

const NOTION_VERSION = "2022-06-28";
const MAX_TEXT_LENGTH = 2000;

type NotionRichText = { type: "text"; text: { content: string } };

type NotionBlock =
  | { type: "paragraph"; paragraph: { rich_text: NotionRichText[] } }
  | { type: "heading_1"; heading_1: { rich_text: NotionRichText[] } }
  | { type: "heading_2"; heading_2: { rich_text: NotionRichText[] } }
  | { type: "heading_3"; heading_3: { rich_text: NotionRichText[] } };

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

function paragraph(content: string): NotionBlock {
  return { type: "paragraph", paragraph: { rich_text: richText(content) } };
}

/** Minimal markdown → Notion blocks (headings and paragraphs). */
export function markdownToNotionBlocks(markdown: string): NotionBlock[] {
  const blocks: NotionBlock[] = [];
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  let paragraphBuffer: string[] = [];

  const flushParagraph = () => {
    const text = paragraphBuffer.join("\n").trim();
    paragraphBuffer = [];
    if (text) blocks.push(paragraph(text));
  };

  for (const line of lines) {
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    if (heading) {
      flushParagraph();
      const level = heading[1].length;
      const content = heading[2].trim();
      if (!content) continue;
      const rt = richText(content);
      if (level === 1) blocks.push({ type: "heading_1", heading_1: { rich_text: rt } });
      else if (level === 2)
        blocks.push({ type: "heading_2", heading_2: { rich_text: rt } });
      else blocks.push({ type: "heading_3", heading_3: { rich_text: rt } });
      continue;
    }
    if (line.trim() === "") {
      flushParagraph();
      continue;
    }
    paragraphBuffer.push(line);
  }
  flushParagraph();

  return blocks.length > 0 ? blocks : [paragraph("")];
}

async function createNotionPage(
  apiKey: string,
  parentPageId: string,
  title: string,
  children: NotionBlock[],
): Promise<{ id: string; url?: string }> {
  const body = {
    parent: { page_id: parentPageId },
    properties: {
      title: {
        title: richText(title),
      },
    },
    children: children.slice(0, 100),
  };

  const res = await fetch("https://api.notion.com/v1/pages", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Notion-Version": NOTION_VERSION,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

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
      let markdown = input.markdown;
      if (input.tags?.length) {
        markdown += `\n\n---\n\nTags: ${input.tags.join(", ")}`;
      }
      const children = markdownToNotionBlocks(markdown);
      return createNotionPage(apiKey, parentPageId, title, children);
    },
  };
}
