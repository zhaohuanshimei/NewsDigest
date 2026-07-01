export interface DigestEntryResource {
  cluster_id: string;
  rank: number;
  category: string;
  topic?: string;
  headline: string;
  summary: string;
  source_count: number;
  sources?: string[];
  image_url?: string;
  video_url?: string;
  headline_translated?: string;
  summary_translated?: string;
}

export interface DigestResource {
  date: string;
  published_at: string;
  entries: DigestEntryResource[];
}
