import type { ApiError, HealthResource } from "../src/index.ts";

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

void health;
void error;
