import { createNotionDestination } from "./destinations/notion.js";
import type { NotesDestination } from "./types.js";

/** Destinations enabled via environment (extend by registering new factories here). */
export function getActiveDestinations(): NotesDestination[] {
  const destinations: NotesDestination[] = [];
  const notion = createNotionDestination();
  if (notion) destinations.push(notion);
  return destinations;
}
