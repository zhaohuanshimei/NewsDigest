export interface ClusterDetailResource {
  id: string;
  category: string;
  headline: string;
  summary: string;
  source_count: number;
  digest_dates: string[];
  headline_translated?: string;
  summary_translated?: string;
}
