export interface DigestEntryResource {
  cluster_id: string;
  rank: number;
  category: string;
  headline: string;
  summary: string;
  source_count: number;
}

export interface DigestResource {
  date: string;
  published_at: string;
  entries: DigestEntryResource[];
}
