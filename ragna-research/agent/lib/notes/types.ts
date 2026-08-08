export interface PublishNoteInput {
  title: string;
  markdown: string;
  tags?: string[];
  /** ISO date (YYYY-MM-DD) */
  date?: string;
}

export interface PublishNoteResult {
  url?: string;
  id?: string;
}

export interface NotesDestination {
  id: string;
  publish(input: PublishNoteInput): Promise<PublishNoteResult>;
}
