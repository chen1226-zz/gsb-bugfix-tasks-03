"""带租约的分布式锁。

对外接口（不得更改签名）：
    Lease 对象：.resource / .owner / .token / .release()
    LockDaemon(lease=0.2, clock=None)
        .acquire(resource, owner) -> Lease | None
        .release(resource, owner, token)
        .holders() -> dict
"""

import threading
import time


class Lease:
    def __init__(self, daemon, resource, owner, token):
        self.daemon = daemon
        self.resource = resource
        self.owner = owner
        self.token = token

    def release(self):
        return self.daemon.release(self.resource, self.owner, self.token)


class LockDaemon:
    def __init__(self, lease=0.2, clock=None):
        self.lease = float(lease)
        self._clock = clock or time.monotonic
        self._held = {}
        self._lock = threading.Lock()
        self._seq = 0

    def acquire(self, resource, owner):
        now = self._clock()
        with self._lock:
            entry = self._held.get(resource)
            if entry is not None and entry["expires_at"] > now:
                return None
            self._seq += 1
            token = self._seq
            self._held[resource] = {
                "owner": owner,
                "token": token,
                "expires_at": now + self.lease,
            }
        return Lease(self, resource, owner, token)

    def renew(self, resource, owner, token):
        with self._lock:
            entry = self._held.get(resource)
            if entry is None or entry["token"] != token:
                return False
            entry["expires_at"] = self._clock() + self.lease
            return True

    def release(self, resource, owner, token):
        with self._lock:
            entry = self._held.get(resource)
            if entry is not None and entry["token"] == token:
                del self._held[resource]
                return True
            return False

    def holders(self):
        with self._lock:
            return {key: dict(value) for key, value in self._held.items()}
