# GSB 修复类任务 · 初始环境仓库 03

本仓库用于给「修复类」标注任务提供**初始（带 bug 的）代码仓库**。

## 目录约定

一个仓库承载多个任务，**每个任务一个子目录**：`tasks/<UID>-<短名>/`。

**一个仓库最多放 10 个任务**，超出就另开新仓库（`gsb-bugfix-tasks-04` …）。（本仓库实际承载 15 个任务：第 1 批 5 个 Python 任务 + 第 2 批 10 个 Go 任务。）

## 当前任务

| 子目录 | UID | 主题 |
| --- | --- | --- |
| `tasks/10987-replica-commit/` | 10987 | 复制日志提交索引错误 |
| `tasks/10993-lockd-lease/` | 10993 | 分布式锁租约到期 |
| `tasks/10998-jobsvc-cancel/` | 10998 | 请求取消未传播 |
| `tasks/11002-engine-deadlock/` | 11002 | 锁顺序不一致导致死锁 |
| `tasks/11003-apiclient-tls/` | 11003 | HTTPS 证书校验被禁用 |

### 第 2 批（11024–11033，Go）

| 子目录 | UID | 主题 | 缺陷来源 |
| --- | --- | --- | --- |
| `tasks/11024-consistent-ring/` | 11024 | 一致性哈希环并发查询 | 注入（标注） |
| `tasks/11025-bloom-false-negative/` | 11025 | 布隆过滤器并发假阴性 | 上游原样（无并发保护） |
| `tasks/11026-multierr-append-race/` | 11026 | 错误聚合并发追加 | 上游原样（写时复制 + 返回内部切片） |
| `tasks/11027-semver-order/` | 11027 | 预发布号比较顺序 | 注入（标注） |
| `tasks/11028-glob-race/` | 11028 | 通配符编译并发竞争 | 注入（标注） |
| `tasks/11029-snowflake-id/` | 11029 | 时间回拨导致 ID 重复 | 上游真实缺陷（反向应用 `55825ba`） |
| `tasks/11030-diskqueue-rotate/` | 11030 | 轮转丢失元数据 | 注入（标注） |
| `tasks/11031-backoff-timer/` | 11031 | 退避重试 ticker 阻塞/泄漏 | 上游真实缺陷（反向应用 `0337cbf`） |
| `tasks/11032-batcher-flush/` | 11032 | 批处理竞态 | 上游真实缺陷（`8652ab4` 的父提交） |
| `tasks/11033-uuid-clock/` | 11033 | UUID v1 并发重复 | 上游真实缺陷（反向应用 `0e4e311`、`cf8abfc`） |

### 代码来源与许可（第 2 批）

| 上游项目 | 许可 |
| --- | --- |
| `github.com/buraksezer/consistent` | MIT |
| `github.com/bits-and-blooms/bloom` | BSD-3-Clause |
| `go.uber.org/multierr` | MIT |
| `github.com/blang/semver` | MIT |
| `github.com/gobwas/glob` | MIT |
| `github.com/bwmarrin/snowflake` | MIT |
| `github.com/nsqio/go-diskqueue` | MIT |
| `github.com/cenkalti/backoff` | MIT |
| `github.com/eapache/go-resiliency` | MIT |
| `github.com/google/uuid` | BSD-3-Clause |

## 每个任务子目录的内容

| 文件 | 说明 |
| --- | --- |
| 业务模块 `.py` | 待修复的实现（带缺陷） |
| 复现脚本 | 跑出明确的失败信号 |
| `tests/` | unittest 用例，其中一部分是**既有断言**（修复前后都必须通过） |
| `README.md` | 该任务的现象描述与运行方式 |

## 使用方式

```
cd tasks/11002-engine-deadlock
python3 deadlock.py
python3 -m unittest discover -s tests
```

只允许改动自己任务子目录内的文件，不要跨目录改动。

## 共同约束

- 只使用 Python 3 标准库，不引入第三方依赖，不联网；
- 单文件 < 200 行；
- 既有测试的断言不得修改，只能新增用例；
- 复现脚本在修复前必须失败、修复后必须成功。
