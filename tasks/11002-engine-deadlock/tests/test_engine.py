import unittest

from engine import Engine


class TestEngine(unittest.TestCase):
    def test_transfer_moves_money(self):
        """既有断言：转账后余额正确。"""
        engine = Engine()
        engine.transfer("x", "y", 30)
        self.assertEqual(engine.snapshot()["accounts"], {"x": 70, "y": 130})

    def test_reindex_updates_index(self):
        """既有断言：重建索引会写入 key。"""
        engine = Engine()
        engine.reindex("k")
        self.assertEqual(engine.snapshot()["index"]["k"], 1)

    def test_snapshot_shape(self):
        """既有断言：snapshot 返回账户与索引两部分。"""
        snap = Engine().snapshot()
        self.assertEqual(sorted(snap), ["accounts", "index"])


if __name__ == "__main__":
    unittest.main()
