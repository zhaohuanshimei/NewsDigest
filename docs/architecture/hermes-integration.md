# Hermes Integration Guide

> Hermes Agent 作为 News Digest pipeline 的"编辑判断层"接入。本文记录方案、指引和待办。
> 上游愿景见 `news-pipeline-vision.md`。

## 什么是 Hermes

Hermes Agent 是 [Nous Research](https://nousresearch.com) 开发的**自我进化 AI agent**。

- 仓库：https://github.com/NousResearch/hermes-agent
- 文档：https://hermes-agent.nousresearch.com/docs/
- Rust 重写版（v0.1）：https://github.com/Lumio-Research/hermes-agent-rs
- 许可证：MIT

核心能力（与我们 pipeline 相关的）：

| 能力 | 我们用在哪 |
|------|-----------|
| 自我学习循环——从每次运行积累经验，自动改进技能 | dedup 阈值、编辑判断越用越准 |
| 定时自动化 (cron)——自然语言配置定时任务 | 替代手动 `run_pipeline.py` |
| 子 agent 并行——spawn 隔离 subagent | 每源抓取、每 cluster 摘要并行 |
| 多模型切换——OpenRouter/OpenAI/自定义，无 lock-in | 便宜模型做摘要，好模型做编辑判断 |
| 技能系统——复杂任务后自动创建可复用 skill | 每个 pipeline stage 封装成 skill |
| 内存系统——记住过去选择，FTS5 搜索历史 | 编辑判断的记忆库 |
| 部署灵活——$5 VPS 到 GPU cluster | 我们就是 VPS |

## 集成方案：方案乙（轻量，推荐起步）

**Hermes 只做 LLM editor 层。现有 Python pipeline 不变。**

```
现有 Python pipeline（fetch → dedup → cluster → rule_score）
    ↓
输出 top 25 候选 cluster（JSON）
    ↓
Hermes 作为"编辑 agent"介入：
    - 读取 25 个候选
    - 利用记忆库比对历史编辑判断
    - 输出 ranking + should_feature + editorial_note + topic_label
    - 把这次判断存入记忆（自我学习）
    ↓
Python pipeline 继续：按 ranking 生成 digest
```

**为什么选方案乙：**
1. 渐进式——不动现有架构，Hermes 挂了 pipeline 还能跑（回退到纯规则评分）
2. AI 克制——Hermes 限定在一个环节，符合"AI 使用尽量克制"原则
3. 自我进化的核心价值在"编辑判断越用越准"，正好是 Hermes 强项
4. 未来效果好可渐进迁移更多 stage 到 Hermes（走向方案甲）

**不选方案甲（全 pipeline 编排）的理由：** Hermes Rust 版还是 v0.1，Nous 原版快速迭代，把整个 pipeline 压上去风险太高。先用方案乙验证效用。

## 前置条件：基础层必须先做好

**Hermes 集成在 P6，P1-P3 规则版必须先稳定。** 没有 rule_score，Hermes 没有候选可判断。

P1-P3 详见 `docs/superpowers/parallel-tasks.md`：
- P1: 多层 dedup + topic 分类（规则版）
- P2: 源 quality_score 学习机制
- P3: 重要性评分（规则 70%）+ topic 分区 digest

**P3 完成且稳定运行 1 周后，再启动 Hermes 集成（P6）。**

## Hermes 侧需要做什么

### 1. 安装 Hermes

```bash
# Linux/macOS/WSL2
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 重载 shell
source ~/.bashrc  # 或 ~/.zshrc

# 启动交互式配置向导
hermes setup
```

安装包含：uv, Python 3.11, Node.js, ripgrep, ffmpeg, Git Bash。

### 2. 配置 LLM provider

```bash
hermes model  # 选择 provider 和 model
```

推荐配置：
- **编辑判断**：用稍好的模型（GPT-4o-mini / Claude Haiku / DeepSeek V3），每天 1 次调用，成本可控
- **摘要生成**：用便宜模型（GPT-4o-mini / Haiku），每 cluster 1 次
- 可选：[Nous Portal](https://portal.nousresearch.com) 一个订阅覆盖 300+ 模型 + web search + TTS + cloud browser

环境变量（`~/.hermes/.env`）：
```bash
ANTHROPIC_API_KEY=sk-...     # 或
OPENAI_API_KEY=sk-...        # 或
OPENROUTER_API_KEY=sk-or-... # 多模型路由
```

### 3. 创建"News Editor"技能

在 Hermes 里创建一个 skill，定义编辑判断的工作流：

```
hermes
> /skill create news-editor
```

Skill 内容（伪代码，具体格式参考 Hermes 文档的 [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)）：

```markdown
# Skill: news-editor

## 触发
当收到 `news_digest_editor` 工具调用或定时任务触发时执行。

## 输入
- candidates: JSON array of 25 clusters
  每个 cluster: {id, headline, summary, sources[], rule_score, cluster_size, age_hours}
- target_date: YYYY-MM-DD

## 任务
1. 读取 candidates
2. 查询记忆库：历史上对类似 cluster 的编辑判断（topic/重要性/是否 feature）
3. 对每个 cluster 评估：
   - importance_rank (1-25)
   - editorial_note (一句话理由)
   - topic_label (politics/business/tech/science/world/health/general)
   - should_feature (bool: 是否上头版)
   - diversity_flag (是否需要补充对立视角)
4. 保证约束：
   - 单 topic 不超过 5 条
   - 至少 3 个 topic 有 representation
   - 排除明显煽动性标题（标题含 ALL CAPS / 情绪化词）
5. 输出 JSON：
   {rankings: [{cluster_id, rank, topic, should_feature, note}], digest_date}
6. 把本次判断存入记忆（供下次学习）

## Prompt 约束
"你是 Techmeme 的编辑。目标是用最短篇幅让读者获得最全面信息。
排除煽动性标题和未经核实的突发。保证 topic 多样性。
参考历史判断保持一致性，但对新事件保持敏感。"
```

### 4. 配置定时任务（可选，P6 后期）

```bash
hermes
> /cron
```

自然语言配置：
```
每天早上 7:00 和晚上 19:00，运行 news-editor 技能，
读取 /api/v1/pipeline/candidates 端点，把结果写回 /api/v1/pipeline/rankings。
```

或用 Hermes cron DSL（详见 [Cron Scheduling 文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)）。

### 5. 启用记忆系统

Hermes 默认启用记忆。确认配置：
```bash
hermes config set memory.enabled true
hermes config set memory.backend sqlite  # 或其他后端
```

记忆库存的是：每次编辑判断的输入候选 + 输出 ranking + 是否被用户反馈修正。Hermes 用这些做自我进化。

## 我们（News Digest API）侧需要做什么

### 1. 新增 candidates 导出端点（P3 末尾或 P6 初）

```python
# services/api/app/routers/pipeline.py
@router.get("/pipeline/candidates")
def get_candidates(date: date, db: Session = Depends(get_db)):
    """返回 rule_score top 25 cluster，供 Hermes editor 消费。"""
    # 查询当日 cluster + rule_score
    # 返回 JSON: [{id, headline, summary, sources[], rule_score, cluster_size, age_hours}]
```

### 2. 新增 rankings 回写端点

```python
@router.post("/pipeline/rankings")
def post_rankings(payload: RankingPayload, db: Session = Depends(get_db)):
    """接收 Hermes editor 的 ranking 结果，更新 cluster importance_score。"""
    # payload: {rankings: [{cluster_id, rank, topic, should_feature, note}], digest_date}
    # 更新 cluster.importance_score = 0.7 * rule_score + 0.3 * llm_rank_score
    # 更新 cluster.topic_label
    # 标记 cluster.editorial_status = "ranked"
```

### 3. Pipeline 集成开关

在 `run_pipeline.py` 加一个 `--editor` 标志：

```python
# 默认：纯规则评分
python -m app.scripts.run_pipeline --date 2026-06-30

# 启用 Hermes editor：
python -m app.scripts.run_pipeline --date 2026-06-30 --editor hermes
```

`--editor hermes` 时：
1. 先跑规则评分得到 rule_score
2. 调 `/pipeline/candidates` 导出 top 25
3. 等 Hermes 处理（或主动触发）
4. Hermes 回写到 `/pipeline/rankings`
5. Pipeline 继续生成 digest

**如果 Hermes 不可用，自动回退到纯规则评分。** 这是方案乙的容错设计。

### 4. 部署 Hermes 实例

选项：
- **同机部署**：和现有 API 容器同一台 VPS，Hermes 作为独立进程跑
- **单独 VPS**：$5 VPS 跑 Hermes，通过 HTTP API 和主服务通信（推荐，隔离故障域）

同机部署的 docker-compose 增量：
```yaml
# infra/docker-compose.server.yml
hermes:
  image: nousresearch/hermes-agent:latest  # 或自建
  volumes:
    - ./hermes-data:/root/.hermes
    - ./hermes-skills:/root/.hermes/skills
  env_file: .env
  restart: unless-stopped
```

## 集成验证清单（P6 执行时用）

- [ ] Hermes 安装并能 `hermes` 启动交互
- [ ] LLM provider 配置完成，能对话
- [ ] news-editor skill 创建并测试
- [ ] `/pipeline/candidates` 端点返回正确 JSON
- [ ] `/pipeline/rankings` 端点能回写
- [ ] `run_pipeline.py --editor hermes` 全流程跑通
- [ ] Hermes 不可用时自动回退到纯规则评分
- [ ] 记忆系统启用，第二次运行能引用历史判断
- [ ] 成本监控：每日 LLM 调用次数 < 60，成本 < $3

## 成本预估

| 项目 | 日成本 | 月成本 |
|------|--------|--------|
| 翻译（已有，500 篇）| $0.50 | $15 |
| 摘要（~20 cluster）| $0.04 | $1.2 |
| 编辑判断（1 次批调用）| $0.05 | $1.5 |
| **合计** | **~$0.6** | **~$18** |

远低于之前估算的 $60/月，因为编辑判断是单次批调用不是每篇调。

## 回退方案

如果 Hermes 集成失败或效果不好：
1. `run_pipeline.py` 不加 `--editor` 标志，回到纯规则评分
2. `/pipeline/candidates` 和 `/pipeline/rankings` 端点保留但不调用
3. Hermes 实例停掉，不影响主服务

**方案乙的设计目标就是：Hermes 是增强项，不是依赖项。**

## 未来演进：方案甲（全 pipeline 编排）

如果方案乙效果好，可渐进迁移更多 stage 到 Hermes：

```
Hermes cron 触发
  → Skill: fetch_all_sources（并行子 agent）
  → Skill: multi_layer_dedup
  → Skill: topic_classify
  → Skill: cluster_articles
  → Skill: importance_score（规则层）
  → Hermes 自身做 LLM editor 判断
  → Skill: generate_digest
  → Skill: publish
```

每个 stage 迁移后，Python 对应 service 保留作为回退。这是 P7+ 的事，不在当前规划内。

## 参考链接

- Hermes Agent 主仓库：https://github.com/NousResearch/hermes-agent
- Hermes 文档：https://hermes-agent.nousresearch.com/docs/
- Skills 系统：https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- Cron 调度：https://hermes-agent.nousresearch.com/docs/user-guide/features/cron
- 记忆系统：https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- Nous Portal（多模型订阅）：https://portal.nousresearch.com
- 上游愿景：`docs/architecture/news-pipeline-vision.md`
