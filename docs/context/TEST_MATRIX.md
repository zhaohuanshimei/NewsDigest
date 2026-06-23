# 测试矩阵

## 说明

本矩阵将项目功能拆分为三类状态：

- `已实现并已自动化验证`
- `已实现但仍需增强验证`
- `未实现，先建立测试规格`

目标是让测试覆盖与产品路线保持同步，而不是等功能完成后再补救式写测试。

## A. 已实现功能

### A1. 配置与启动

#### 已验证

- 版本号格式
- `sources.yaml` 基本结构
- 源 URL 唯一性
- 统一配置加载与校验入口（enabled 过滤、字段校验、重复 URL 拦截）
- CLI `digest` 与 `translate-digest` 基本命令路径
- 前端健康页 `/admin/health` 与探活 JSON `/health.json`（无导出时降级占位）

#### 应持续增强

- CLI 非法参数路径
- 配置缺失文件时的失败路径
- 环境变量缺失时的错误提示

### A2. RSS 抓取

#### 已验证

- `Article.url_hash`
- RSS 内容解析基础行为
- 抓取器 timeout / UA 配置透传
- 抓取重试后恢复成功
- CLI `fetch` 单源抓取入库主路径
- CLI `fetch-all` 仅处理启用源配置
- 入库去重：标题 SimHash 去重（阈值可配）
- 真实网络 RSS 用例占位

#### 应持续增强

- HTTP 成功路径 mock
- 非法 feed 失败路径
- 缺少 link/title 的 entry 过滤
- 发布时间字段回退逻辑

### A3. 正文抓取与限流

#### 已验证

- robots 开关
- `trafilatura` 基础提取
- `RateLimiter` 独立测试
- 正文补全：扫描 `body` 为空的文章并回填（含失败统计）
 - backoff 触发后对单域名隔离，不影响其他域名限流状态

#### 应持续增强

- `fetch_content()` 成功时记录 success
- `fetch_content()` 失败时记录 failure
- robots 拒绝时抛出权限错误

### A4. 仓储与数据持久化

#### 已验证

- 文章入库
- 基于 `url_hash` 幂等去重

#### 应持续增强

- `get_or_create_source()` 幂等
- `simhash` 落库
- 空摘要 / 正文字段行为

### A5. 聚类、排序、digest

#### 已验证

- 聚类基础行为
- 排序得分逻辑
- digest 生成、空集、重跑覆盖、rank 顺序
- digest 导出 schema、排序稳定性与无译文降级策略
- 生产流水线健康导出 `exports/health.json`（含每源统计与连续失败告警字段）

#### 应持续增强

- 边界阈值行为
- 最近时间窗外数据过滤
- digest 导出与前端构建的集成测试

### A6. 翻译链路

#### 已验证

- DeepL provider
- Google provider
- provider fallback
- 翻译缓存
- digest 批量翻译
- CLI 触发翻译与失败返回码

#### 应持续增强

- 实际落库 `provider` 来源记录
- 批量翻译全量失败时日志与错误摘要

### A7. 调度器

#### 已验证

- 配置加载
- 调度器初始化

#### 应持续增强

- `add_job()` 注册参数
- `fetch_all_sources()` 成功/失败统计
- session 关闭行为

### A8. 前端（Astro 静态站）

#### 已验证

- Astro 项目可在无导出数据时构建通过（占位页）
- 首页 `/`、归档页 `/archive`、单日页 `/archive/YYYY-MM-DD` 基础路由
- 站点 RSS `/feed.xml` 基础输出
- 前端构建集成测试：无导出 / 坏 JSON / 有效 JSON 三场景
- Lighthouse 移动端基线（Performance/Accessibility/Best-Practices ≥ 95，SEO ≥ 90）

#### 应持续增强

- 构建时读取导出数据的契约验证（与导出 JSON schema 严格对齐）
- Lighthouse 关键指标回归基线

## B. 已实现但缺少工程级验证的方向

- 导出层和前端集成验证
- 面向真实数据库的最小冒烟测试
- 生产流水线的全链路集成测试（抓取 mock + DB + 导出文件 + webhook mock）

## C. 未实现功能的测试规格

### C1. 前端数据接入

#### 计划验证

- 构建时读取导出数据成功
- 空 digest / 部分缺字段时构建行为
- 页面渲染与归档页面链接正确

### C2. 构建流水线

#### 计划验证

- 抓取 -> digest -> 翻译 -> 导出 的串联执行
- 中间失败可补跑
- 重跑不会产生重复产物

### C3. 监控与告警

#### 计划验证

- 日报未按时生成时产生告警
- 翻译缺失率超阈值时产生告警
- 抓取源连续失败时产生告警

## 工程级验证命令

### 当前基线

```bash
python -m pytest
```

### 建议下一步升级

```bash
python -m pytest --cov=src/news_digest --cov-report=term-missing --cov-fail-under=85
ruff check .
mypy src/news_digest
```
