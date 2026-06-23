# 翻译链路与 RSS 改造计划

## 目标

本轮改造解决两个直接影响可发布性的痛点：

1. 机器翻译链路从“可调用”升级为“可批量、可回退、可解释”。
2. RSS 输出从“人类可读说明页”恢复为“订阅器可消费的标准 feed”，并单独提供订阅说明页。

## 非目标

- 不在本轮引入新的翻译供应商。
- 不在本轮实现多分类 feed、邮件订阅或后台编辑能力。
- 不在本轮重做首页信息架构，只做必要导航调整。

## 设计结论

### 1. 翻译链路

- 保留现有 provider 抽象和 fallback 策略。
- `TranslationService` 改为优先使用批量翻译接口：
  - 标题批量翻译一次。
  - 摘要批量翻译一次，仅处理非空摘要。
- 批量结果统一落库，减少逐文章提交事务。
- 增加轻量质量护栏：
  - 译文为空时视为失败。
  - 对英文媒体名做最小术语规范化：`Reuters -> 路透社`、`AP -> 美联社`、`BBC -> BBC`、`NYT -> 纽约时报`。
  - 对标题和摘要做空白清洗，避免前后空格与空字符串入库。
- 继续保留 `provider` 字段，记录实际成功 provider，便于前端与调试使用。

### 2. RSS 输出

- `/feed.xml` 必须返回标准 RSS XML，`Content-Type` 为 `application/rss+xml; charset=utf-8`。
- 新增 `/rss` 页面承载“如何订阅”的说明，取代当前 `feed.xml.ts` 里的 HTML 说明页职责。
- RSS item 使用站内入口作为 `<link>`，原文链接放入 `<description>` 文本中，兼顾站内消费与跳转原文。
- 空数据或坏数据场景仍生成合法空 feed，避免构建失败。

## 文件级改动

### 后端

- `src/news_digest/translation_service.py`
  - 增加批量翻译主路径。
  - 增加译文清洗与术语规范化辅助函数。
  - 减少逐文章 `commit()`，改为批次写库。
- `tests/test_translation_service.py`
  - 新增批量翻译路径测试。
  - 新增空摘要混合场景测试。
  - 新增 provider 记录与术语规范化测试。

### 前端

- `web/src/lib/rss.ts`
  - 调整 item 的 `link`、`guid`、`description` 生成策略。
  - 保持空 feed 兼容。
- `web/src/pages/feed.xml.ts`
  - 仅返回 XML response，不再输出 HTML。
- `web/src/pages/rss.astro`
  - 新增订阅说明页，展示 feed 链接、订阅方法和常见阅读器入口。
- `web/src/pages/index.astro`
  - 导航中的 `RSS` 链接改为 `/rss`。
- `web/scripts/verify-build.mjs`
  - 调整构建校验：`feed.xml` 必须始终为 XML。
  - 增加 `/rss/index.html` 说明页的构建验证。

## 测试与验证

### Python

- 运行：

```bash
python -m pytest tests/test_translation_service.py tests/test_translator.py -q
```

### Web

- 运行：

```bash
cd web
npm run test:build
npm run check
```

### 手动验收

- 访问 `/feed.xml`，确认浏览器显示原始 XML。
- 访问 `/rss`，确认显示订阅说明页。
- 访问首页，确认导航 `RSS` 指向 `/rss`。
- 构建有效 digest 数据时，feed item 包含中文标题、中文摘要和站内链接。

## 执行顺序

1. 先改 RSS 路由与构建校验，快速恢复标准 feed。
2. 再改翻译服务批量路径与最小质量护栏。
3. 补齐 Python 与前端验证。
4. 如验证通过，再考虑把计划状态同步回 `docs/DEVELOPMENT_PLAN.md`。

## 提交边界

建议拆为两个提交：

1. `feat: fix RSS feed route and add subscribe page`
2. `feat: batch digest translation with normalization guards`
