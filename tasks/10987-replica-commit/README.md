# 10987 · 复制日志提交索引（replica）

`replica.py` 在单进程内模拟三节点复制日志，网络丢包可注入。

接口：`Replica(nodes, rng, drop_rate)` 的 `.append(command)` / `.elect_leader()` /
`.ack_count(command)` / `.committed()`。

| 文件 | 说明 |
| --- | --- |
| `replica.py` | 待修复的模块 |
| `chaos.py` | 复现脚本：200 组随机丢包 + 随机换主 |
| `tests/test_replica.py` | unittest 用例 |

## 已知现象

注入丢包/延迟/重启的压力测试里，已经提交（commit）的数据会在后续选举或恢复后
消失，客户端读到的历史出现回退。

## 运行

```
python3 chaos.py
python3 -m unittest tests/test_replica.py -v
```
