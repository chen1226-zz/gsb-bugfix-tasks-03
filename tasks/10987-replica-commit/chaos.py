"""复现脚本：随机丢包 + 随机换主，检查已提交数据是否回滚。"""

import random

from replica import Replica

RUNS = 200
APPENDS_PER_RUN = 15
MAJORITY = 2


def one_run(rng):
    drop_rate = rng.random() * 0.5
    cluster = Replica(nodes=3, rng=rng, drop_rate=drop_rate)
    committed = []
    for index in range(APPENDS_PER_RUN):
        result = cluster.append(f"cmd-{index}")
        if result["committed"]:
            committed.append(f"cmd-{index}")
        if rng.random() < 0.4:
            cluster.elect_leader()

    lost = [cmd for cmd in committed if cluster.ack_count(cmd) < MAJORITY]
    return len(committed), lost, drop_rate


def main():
    rng = random.Random(20260928)
    for run in range(RUNS):
        total, lost, drop_rate = one_run(rng)
        if lost:
            print(f"FAIL: 第 {run + 1} 组出现回滚（丢包率 {drop_rate:.2f}）")
            print(f"  已提交 {total} 条，其中 {len(lost)} 条在多数派上找不到：{lost[:3]}")
            print("  提示：提交没有等到多数派确认")
            raise SystemExit(1)
    print(f"OK: {RUNS} runs, 0 rollbacks")


if __name__ == "__main__":
    main()
