# News Pipeline Vision

> 2026-06-30 讨论总结。本文记录 News Digest V2 从"能跑"到"好用"的 pipeline 演进方向，是后续任务规划的依据。

## 北极星指标

**用户用最短时间获得最全面的信息。**

这决定了所有设计取向：
- Digest 有明确边界（~20 条），不是无限刷
- 排序按 importance 不按 click
- 摘要要 dense（100 字精要），不是长文
- 一个事件一个 cluster，不做"相关推荐"无限链
- 明确拒绝：愤怒驱动、无限滚动、filter bubble、通知轰炸、标题党奖励

## 现状与缺陷

当前 pipeline：
```
Fetch → URL dedup → TF-IDF cluster → 按簇大小排名 → Digest
```

三个核心问题：
1. **抓不到重点** — 簇大小 ≠ 重要性，10 个低质源报同一件事 > 2 个顶级源报的另一件事
2. **重复内容** — URL dedup 抓不住跨源同事件（AP 稿被多家转载，URL 不同内容相同）
3. **无法分类** — 所有条目混在一个 digest 里，没有 topic 维度

## 目标 Pipeline（端到端）

```
┌─ 收集层 ──────────────────────────────────────────┐
│  Multi-Fetcher (RSS / Web / API / Newsletter)      │
│  + Source Profile (tier / trust / quality)         │
│  + 用户自订源 (pending → 升级机制)                   │
└───────────────────────────────────────────────────┘
                      ↓
┌─ 整理层 ──────────────────────────────────────────┐
│  多层 Dedup (URL → 标题 → 内容 → 实体)               │
│  + Topic 分类（规则起步，后期可 LLM 升级）            │
│  + 事件聚类 (TF-IDF + topic 一致)                   │
└───────────────────────────────────────────────────┘
                      ↓
┌─ 处理层 ──────────────────────────────────────────┐
│  翻译（已有）+ 摘要压缩（RSS summary 统一为 100 字）  │
│  + 重要性评分（规则 70% + LLM editor 30%）           │
│  + Quality-weighted ranking (源质量加权)             │
│  + Bias 标注（后期，用 MBFC 数据）                   │
└───────────────────────────────────────────────────┘
                      ↓
┌─ 分发层 ──────────────────────────────────────────┐
│  默认: Topic 分区 digest（免费）                    │
│  + 多样性约束（每 section 至少 1 条）                │
│  + 多端: Web / RSS out / Newsletter / API          │
│  未来 VIP: 个性化排序 + 探索注入                     │
└───────────────────────────────────────────────────┘
                      ↓
┌─ 点评层（未来 VIP）──────────────────────────────┐
│  深度分析 + 多源对比 + 事件时间线 + Q&A              │
│  + Fact-check 标注 + 社区评论                       │
└───────────────────────────────────────────────────┘
```

## AI 使用策略（克制原则）

**没有 VIP 计划，AI 使用最小必要集。** 当前阶段不做深度分析、Q&A、个性化。

| 环节 | 用 AI 吗 | 理由 |
|------|---------|------|
| Topic 分类 | ❌ 关键词规则 | 零成本、可解释、效果够用 |
| 实体抽取（NER）| ❌ P1-P3 不做 | 暂不需要 |
| 摘要生成 | ✅ 便宜模型 | RSS 自带摘要参差，需压缩统一 |
| 翻译 | ✅ 已有 | 核心功能 |
| 编辑判断（ranking）| ✅ 每天 1 次批调用 | Techmeme 模式核心，替代人工 |
| 深度分析 / Q&A | ❌ 不做 | 用户明确暂不做 |
| 个性化推荐 | ❌ 暂不做 | 先做全局 digest |

**预估成本：** 每天 ~50 次 LLM 调用 ≈ $2/天 ≈ $60/月，可持续。

## Techmeme 模式 + LLM 替代人工

80% 的 Techmeme 人工工作可被 LLM 替代（候选筛选、事件归并、主链接选择、排序、摘要）。剩下 20% 靠规则 + 权重兜底（突发秒级响应、品味判断、政治平衡）。

**LLM-as-Editor Pipeline：**
```
聚类后候选 cluster（30-50 个/天）
    ↓
规则层先筛（tier 加权 + 多源覆盖 + 新鲜度 + 去重置信度）
    → rule_score top 25
    ↓
LLM Editor（单次批调用）：
  输入: 25 个 cluster 的标题+摘要+源列表+rule_score
  输出: importance_rank / editorial_note / topic_label / should_feature / diversity_flag
  Prompt 约束: "你是 Techmeme 编辑，目标最短篇幅最全信息；排除煽动标题；保证 topic 多样性"
    ↓
最终 digest（~20 条，按 importance 排序）
```

**关键原则：LLM 只做编辑判断，不做内容生成。** 编辑判断 1 次调用吃 25 候选；摘要每入选 cluster 调 1 次；不做评论/Q&A。

## 吸收其他家优点

| 借鉴源 | 吸收什么 | 落地 |
|--------|---------|------|
| Techmeme | 源分层 + 一事件一主链接 + 编辑判断 | tier 字段 + cluster 内 canonical article + LLM editor |
| Google News | story clustering + 多样性约束 | 已有聚类 + topic 多样性约束 |
| Ground News | bias 透明化 | 后期加 bias 标签展示盲区 |
| 1440 | 人工语调精编摘要 | LLM 摘要指定中性简洁 style |
| Hacker News | 社区反馈信号 | 后期加有用/不感兴趣按钮调权 |

**明确不吸收：** 无限滚动、个性化到 filter bubble、算法只看点击率。

## 异构源统一接入（主流 + 小众 + 自订）

SourceProfile 设计：
```
fetch_method: rss | web-scrape | api | newsletter | podcast | user-submit
source_tier:  tier-1 | tier-2 | community | pending
content_type: breaking | analysis | opinion | mixed
trust_level:  verified | community | pending
quality_score: 0.1–1.0（学出来的，不是写死的）
tags: 多对多标签（topic/bias/region/credibility/custom）
```

Fetcher 适配器：
```
BaseFetcher (ABC)
  ├─ RssFetcher        # 已有
  ├─ WebScraperFetcher # readability-lxml 抓正文
  ├─ ApiFetcher        # Twitter/Reddit JSON API
  ├─ NewsletterFetcher # email 接入
  └─ PodcastFetcher    # whisper 转录
```

**quality_score 学习机制：** 追踪每源文章"进 digest 比例""被 dedup 淘汰比例""被标记低质次数"，定期调整。新源 0.3 起步，靠表现升级。

**用户自订源流程：** 提交 RSS URL → 验证可达 → 抓 10 篇样本初评 → pending 状态进个人队列 → 累积 30 天数据后自动调 trust_level。

## 推荐算法借鉴与反借鉴

**借鉴：**
- Topic affinity（用户读 tech 多 → tech section 提前）
- Diversity constraint（每 topic 至少 1 条）
- Freshness decay（`score *= exp(-age_hours/24)`）
- Exploration（10% 概率插入用户 topic 之外的高分文章，防茧房）
- "不感兴趣"反馈降权

**反借鉴（重要）：**
- 拒绝愤怒驱动推送（涨流量但 degrade 公共讨论）
- 拒绝无限滚动（与"高效 informed"矛盾）
- 拒绝 filter bubble（用户只看一面，丧失全景）
- 拒绝通知轰炸（新闻焦虑是真问题）
- 拒绝标题党奖励（点击率 ≠ 重要性）

## 标签系统（取代固定字段）

固定字段（credibility/bias/category）是单维度单值，标签是多维度多值，表达力更强。

```python
class Tag(Base):
    id, name, slug, namespace, color, description
    # namespace: topic | bias | region | credibility | custom

class SourceTag(Base):
    source_id (FK), tag_id (FK)  # 多对多
```

系统标签 vs 用户标签两套；slug 唯一约束防同义词；namespace 防维度混杂。

## Hermes 集成方案（方案乙）

详见 `docs/architecture/hermes-integration.md`。

**方案乙：Hermes 只做 LLM editor 层。** 现有 Python pipeline 不变，Hermes 作为"编辑 agent"介入 importance ranking 环节，利用其自我进化能力让编辑判断越用越准。

**基础层优先：没有 AI 也能用。** 先做 P1-P3 规则版（dedup + topic + score），规则版稳定后再接 Hermes。

## 实施路线（增量，P1-P3 优先）

| Phase | 内容 | 依赖 | 价值 |
|-------|------|------|------|
| **P1** | 多层 dedup + topic 分类（规则起步）| 标签系统 | 立刻减重复、可分区 |
| **P2** | 源 quality_score 学习机制 | Source profile | 自动源分层 |
| **P3** | 重要性评分（规则 70%）+ topic 分区 digest | P1+P2 | 解决"抓不到重点" |
| P4 | WebScraper fetcher | BaseFetcher | 支持非 RSS 源 |
| P5 | 用户自订源 + 个人队列 | P4 | 开放性 |
| P6 | LLM editor 层（接 Hermes）| P3 稳定 | 编辑判断自我进化 |
| P7 | 个性化推荐 + 探索注入 | P3 + 用户数据 | 留存 |

**P1-P3 是地基（零 AI 成本），P4-P5 是开放性，P6-P7 是进化。**

## 参考来源

- Techmeme — 算法+人工 hybrid，源权威度加权
- Google News — story clustering + 多样性约束
- Ground News — bias 透明化（MBFC/AllSides 评级）
- 1440 / Morning Brew — 人工精编 newsletter
- Hacker News — 社区投票排序
- Media Bias/Fact Check (mediabiasfactcheck.com) — 6200+ 源 bias+credibility 评级
- Ad Fontes Media (adfontesmedia.com) — Media Bias Chart
- AllSides (allsides.com) — 左/中/右光谱
- FeedSpot (rss.feedspot.com) — RSS 目录按权威性排名
- Hermes Agent (Nous Research) — 自我进化 AI agent
