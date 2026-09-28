"""带账户锁与索引锁的引擎。

对外接口（不得更改签名）：
    Engine()
        .transfer(src, dst, amount)
        .reindex(key)
        .snapshot() -> dict
"""

import threading
import time

BETWEEN_LOCKS_DELAY = 0.0002


class Engine:
    def __init__(self):
        self.account_lock = threading.Lock()
        self.index_lock = threading.Lock()
        self.accounts = {"x": 100, "y": 100}
        self.index = {}

    def transfer(self, src, dst, amount):
        with self.account_lock:
            time.sleep(BETWEEN_LOCKS_DELAY)
            with self.index_lock:
                self.accounts[src] = self.accounts.get(src, 0) - amount
                self.accounts[dst] = self.accounts.get(dst, 0) + amount
                self.index[f"{src}->{dst}"] = self.index.get(f"{src}->{dst}", 0) + 1

    def reindex(self, key):
        with self.index_lock:
            time.sleep(BETWEEN_LOCKS_DELAY)
            with self.account_lock:
                self.index[key] = self.index.get(key, 0) + 1
                total = sum(self.accounts.values())
                self.index["total"] = total

    def snapshot(self):
        return {"accounts": dict(self.accounts), "index": dict(self.index)}
