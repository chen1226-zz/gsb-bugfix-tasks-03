"""复现脚本：业务耗时超过租约时，检查是否出现两个 worker 同时进入临界区。"""

import threading
import time

from lockd import LockDaemon

RUNS = 60
LEASE = 0.05
WORK = 0.12


def one_run(interval):
    daemon = LockDaemon(lease=LEASE)
    guard = threading.Lock()
    inside = {"now": 0, "max": 0}

    def worker(name):
        lease = daemon.acquire("res", name)
        if lease is None:
            return
        with guard:
            inside["now"] += 1
            inside["max"] = max(inside["max"], inside["now"])
        time.sleep(WORK)
        with guard:
            inside["now"] -= 1
        lease.release()

    first = threading.Thread(target=worker, args=("w1",))
    second = threading.Thread(target=worker, args=("w2",))
    first.start()
    # 等第一个 worker 的租约过期、但业务还没做完的时刻
    time.sleep(WORK * 0.6)
    second.start()
    first.join(timeout=5)
    second.join(timeout=5)
    return inside["max"]


def main():
    worst = 0
    for _ in range(RUNS):
        worst = max(worst, one_run(LEASE))
        if worst > 1:
            break

    if worst > 1:
        print(f"FAIL: {worst} 个 worker 同时进入临界区（租约 {LEASE}s，业务 {WORK}s）")
        print("  提示：持锁方没有续期，租约到期后别人也能进来")
        raise SystemExit(1)
    print(f"OK: {RUNS} runs, 0 concurrent entries")


if __name__ == "__main__":
    main()
