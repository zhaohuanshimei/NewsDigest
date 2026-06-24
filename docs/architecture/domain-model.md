# V2 领域模型

## 建模目标

V2 的领域模型用于统一三类表达：

- 后端内部服务如何理解内容链路
- API 如何向外暴露稳定资源
- 前端如何使用一致的业务术语渲染页面

这份文档不直接等同于数据库 schema，也不等同于前端组件 props；它定义的是两者共享的业务语言。

## 核心实体

### Source

表示一个被系统管理的内容来源。

**职责**

- 定义抓取入口
- 定义来源语言、来源类型与启停状态
- 提供抓取和健康监测的配置上下文

**关键字段**

- `id`
- `name`
- `kind`：如 `rss`、`crawl`
- `language`
- `enabled`
- `fetch_strategy`
- `base_url`

### Article

表示一次抓取和规范化之后的标准化新闻文章。

**职责**

- 承载原始标题、摘要、正文和来源信息
- 作为去重、聚类、翻译的输入对象
- 作为详情页和代表文章的基础素材

**关键字段**

- `id`
- `source_id`
- `url`
- `title`
- `summary`
- `body`
- `published_at`
- `language`
- `normalized_url`
- `dedupe_key`

### Cluster

表示多个 `Article` 围绕同一事件形成的聚合结果。

**职责**

- 将同一新闻事件的不同报道归为一个聚类
- 提供代表文章、聚类规模和排序分值
- 作为日报生成的主要输入单位

**关键字段**

- `id`
- `representative_article_id`
- `size`
- `score`
- `first_seen_at`
- `last_updated_at`

### Digest

表示某个发布日期对外发布的一组精选内容。

**职责**

- 将若干 `Cluster` 以排序结果组织成面向读者的日报
- 提供首页和归档页的核心内容载体
- 作为 RSS 和未来多客户端同步阅读的首发资源

**关键字段**

- `date`
- `entries`
- `published_at`
- `status`

### DigestEntry

表示 `Digest` 中的一条可阅读条目。

**职责**

- 连接 `Digest` 与 `Cluster`
- 承载排序、分类、摘要展示与原文跳转所需信息
- 成为首发 Web 页面和 RSS 项目级资源的最小单位

**关键字段**

- `cluster_id`
- `rank`
- `category`
- `headline`
- `summary`
- `source_count`

### Translation

表示面向某一目标语言的翻译结果。

**职责**

- 为 `Article` 或 `DigestEntry` 提供机器翻译或人工修订结果
- 记录翻译来源、状态与回退路径
- 为后续审校体系保留扩展空间

**关键字段**

- `id`
- `target_language`
- `translated_title`
- `translated_summary`
- `provider`
- `status`
- `review_state`

## 关系

- `Source -> Article`：一个来源可以产出多篇文章
- `Article -> Cluster`：多篇文章可以归入同一个事件聚类
- `Cluster -> DigestEntry`：一个聚类可在某次发布中表现为一条日报条目
- `Digest -> DigestEntry`：一个日报包含多条按顺序排列的条目
- `Article/DigestEntry -> Translation`：原始内容可衍生多语言翻译结果

## 生命周期

### 内容生产链路

`Source -> Article -> Cluster -> DigestEntry -> Digest`

解释如下：

- 来源先被系统读取
- 文章经过抓取、规范化、去重后沉淀为 `Article`
- 多篇文章归并为事件级 `Cluster`
- 聚类经排序与摘要组织形成 `DigestEntry`
- 一组条目最终构成某个日期的 `Digest`

### 内容增强链路

`Article/DigestEntry -> Translation`

翻译属于增强信息，不改变原始内容的事实地位。即使翻译失败，核心内容链路也必须仍然成立。

## 统一术语

为避免 V1 残留词汇继续污染 V2，统一采用以下命名：

- “来源” 对应 `Source`
- “文章” 对应 `Article`
- “事件” 对应 `Cluster`
- “日报” 对应 `Digest`
- “日报条目” 对应 `DigestEntry`
- “翻译结果” 对应 `Translation`

不再把以下词作为核心模型名：

- `export`
- `feed item`
- `post`
- `output json`

这些词只允许在实现细节或历史背景中出现，不作为 V2 的正式领域对象。

## 与 V1 的衔接

V1 已验证的数据表为 V2 提供重要参考，尤其是：

- `sources`
- `articles`
- `translations`
- `clusters`
- `cluster_members`
- `daily_digests`

V2 不要求逐字段复刻这些表，但要求：

- 语义上能映射回这些已验证对象
- 不引入与现有业务链路相冲突的新概念
- 优先在现有验证经验之上提升抽象清晰度
