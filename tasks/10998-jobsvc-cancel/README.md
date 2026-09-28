# 10998 · 请求取消未传播（jobsvc）

接口：`JobService(workers, steps, step_seconds)` 的 `.submit(count)` / `.cancel(job)` /
`.shutdown(grace)` / `.pending()`。

| 文件 | 说明 |
| --- | --- |
| `jobsvc.py` | 待修复的模块 |
| `cancel_test.py` | 复现脚本：提交后全部取消，测退出时间与线程数 |
| `tests/test_jobsvc.py` | unittest 用例 |

## 已知现象

客户端断开或取消请求后，后台任务仍在跑，高峰期出现大量「幽灵任务」把 CPU 占满；
压测结束后活跃线程数不下降。

## 运行

```
python3 cancel_test.py
python3 -m unittest tests/test_jobsvc.py -v
```
