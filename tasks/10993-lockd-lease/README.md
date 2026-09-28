# 10993 · 分布式锁租约（lockd）

接口：`LockDaemon(lease, clock)` 的 `.acquire(resource, owner)` / `.release(...)` /
`.holders()`；`acquire` 返回 `Lease` 对象（`.token` / `.release()`）。

| 文件 | 说明 |
| --- | --- |
| `lockd.py` | 待修复的模块 |
| `chaos.py` | 复现脚本：业务耗时 > 租约时的并发进入 |
| `tests/test_lockd.py` | unittest 用例 |

## 已知现象

偶发两个 worker 同时进入临界区（重复扣减、重复写入），多发生在慢请求、进程被挂起
或网络抖动之后；单机单元测试不重现。

## 运行

```
python3 chaos.py
python3 -m unittest tests/test_lockd.py -v
```
