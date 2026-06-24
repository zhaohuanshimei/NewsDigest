import type { DigestResource } from "../../../../../packages/shared-types/src/index.ts";

export const MOCK_LATEST_DIGEST: DigestResource = {
  date: "2026-06-24",
  published_at: "2026-06-24T09:00:00Z",
  entries: [
    {
      cluster_id: "cluster-ai-chip-001",
      rank: 1,
      category: "technology",
      headline: "AI 芯片与模型基础设施继续升温",
      summary: "多家厂商围绕训练基础设施与推理部署发布新进展。",
      source_count: 3
    }
  ]
};
