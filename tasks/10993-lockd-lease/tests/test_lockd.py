import unittest

from lockd import LockDaemon


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class TestLockDaemon(unittest.TestCase):
    def test_acquire_then_reject(self):
        """既有断言：被占用时第二个调用者拿不到锁。"""
        daemon = LockDaemon(lease=10.0, clock=FakeClock())
        self.assertIsNotNone(daemon.acquire("r", "w1"))
        self.assertIsNone(daemon.acquire("r", "w2"))

    def test_release_allows_reacquire(self):
        """既有断言：释放后可以重新获取。"""
        daemon = LockDaemon(lease=10.0, clock=FakeClock())
        lease = daemon.acquire("r", "w1")
        lease.release()
        self.assertIsNotNone(daemon.acquire("r", "w2"))

    def test_token_is_increasing(self):
        """既有断言：每次获取都会拿到新的 token。"""
        daemon = LockDaemon(lease=10.0, clock=FakeClock())
        first = daemon.acquire("r", "w1")
        first.release()
        second = daemon.acquire("r", "w1")
        self.assertGreater(second.token, first.token)

    def test_holders_reports_owner(self):
        """既有断言：holders 能看到当前持有者。"""
        daemon = LockDaemon(lease=10.0, clock=FakeClock())
        daemon.acquire("r", "w1")
        self.assertEqual(daemon.holders()["r"]["owner"], "w1")


if __name__ == "__main__":
    unittest.main()
