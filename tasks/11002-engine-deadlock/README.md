# 11002 · 锁顺序不一致导致死锁（engine）

接口：`Engine()` 的 `.transfer(src, dst, amount)` / `.reindex(key)` / `.snapshot()`。
内部有两把锁：账户锁与索引锁。

| 文件 | 说明 |
| --- | --- |
| `engine.py` | 待修复的模块 |
| `deadlock.py` | 复现脚本：反复交叉触发两条路径 |
| `tests/test_engine.py` | unittest 用例 |

## 已知现象

高并发下偶发整个服务卡死——所有线程都阻塞、只能重启进程；没有异常抛出，用
`faulthandler` 能看到全部停在锁等待上。

## 运行

```
python3 deadlock.py
python3 -m unittest tests/test_engine.py -v
```
