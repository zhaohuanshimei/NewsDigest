import type {
  ApiError,
  ArchiveDateListResource,
  ClusterDetailResource,
  DigestResource,
  HealthResource,
} from "../src/index.ts";

const health: HealthResource = {
  status: "ok",
  service: "news-digest-api",
  version: "0.1.0",
};

const error: ApiError = {
  code: "service_unavailable",
  message: "服务暂时不可用",
  request_id: "req_placeholder",
};

const digest: DigestResource = {
  date: "2026-06-24",
  published_at: "2026-06-24T09:00:00Z",
  entries: [
    {
      cluster_id: "cluster-ai-chip-001",
      rank: 1,
      category: "technology",
      headline: "AI 芯片与模型基础设施继续升温",
      summary: "多家厂商围绕训练基础设施与推理部署发布新进展。",
      source_count: 3,
    },
  ],
};

const archive: ArchiveDateListResource = {
  dates: ["2026-06-24", "2026-06-23"],
};

const cluster: ClusterDetailResource = {
  id: "cluster-ai-chip-001",
  category: "technology",
  headline: "AI 芯片与模型基础设施继续升温",
  summary: "多家厂商围绕训练基础设施与推理部署发布新进展。",
  source_count: 3,
  digest_dates: ["2026-06-24"],
};

void health;
void error;
void digest;
void archive;
void cluster;
