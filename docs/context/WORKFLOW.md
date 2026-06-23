# 开发工作流

## 核心约定

**每个任务"开发 → 测试通过 → 提交 git"构成一次完整更新。**
未提交的改动视为**未完成**，下一次开发从最近一次 git 提交处继续。

## 任务级工作流

```
1. 从 docs/DEVELOPMENT_PLAN.md 挑选下一个未完成任务 Tx.y
2. 创建分支：git checkout -b task/Tx.y-<slug>
3. 开发
4. 本地测试通过（pytest / lint / 手动验收）
5. git add -A && git commit -m "Tx.y: <简述>"
6. 合并回 main：git checkout main && git merge --no-ff task/Tx.y-<slug>
7. 在 docs/DEVELOPMENT_PLAN.md 中把该任务标记为 [x]
8. 再次 commit：docs: mark Tx.y done
9. （可选）git push
```

简化路径：小改动可直接在 `main` 上开发提交，跳过分支。

## 提交信息规范

格式：`<type>(Tx.y): <简述>`

- `type` ∈ `feat` / `fix` / `docs` / `refactor` / `test` / `chore` / `ci`
- 示例：
  - `feat(T1.1): RSS 抓取模块支持超时与重试`
  - `test(T2.2): 标题 SimHash 去重用例`
  - `docs: mark T1.3 done`

## "从上次提交处重新开始"如何做

每次开始新开发前：

```bash
git status                 # 确认工作区干净
git log -1 --oneline       # 看最近一次提交是哪个任务
grep "^- \[x\]" docs/DEVELOPMENT_PLAN.md | tail -5   # 看最近完成的任务
```

如果本地有未提交的改动：
- 如果上次是**已测试通过**但忘了提交 → 补 commit
- 如果是**未完成的半成品**且本次不继续 → `git stash` 或 `git restore`，回到上次提交的干净状态重新开始

## 测试通过的判定

每个 Phase 有各自的验收标准（见 `DEVELOPMENT_PLAN.md`）。通用要求：

- [ ] `ruff check` 无错
- [ ] `pytest` 相关测试通过
- [ ] 任务本身的"验收"标准满足
- [ ] 无调试语句、无注释掉的代码残留

## 分支与版本

- `main`：始终可运行
- `task/*`：单任务分支，合并后可删
- 里程碑 tag：`v0.1-mvp`、`v0.2-translate` 等，Phase 完成时打 tag

## 一个任务的生命周期示例

```bash
# 开始 T1.1
git checkout -b task/T1.1-rss-fetcher

# ... 开发 ...
pytest tests/test_rss.py        # 通过
ruff check .                    # 通过

git add -A
git commit -m "feat(T1.1): RSS fetcher with retry and timeout"

git checkout main
git merge --no-ff task/T1.1-rss-fetcher
# 编辑 docs/DEVELOPMENT_PLAN.md，把 T1.1 标记为 [x]
git add docs/DEVELOPMENT_PLAN.md
git commit -m "docs: mark T1.1 done"

git branch -d task/T1.1-rss-fetcher
```

下次开发开始时，`git log --oneline` 可清晰看到"上次干到哪里"。
