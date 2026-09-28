import random
import unittest

from replica import Replica


class TestReplica(unittest.TestCase):
    def test_append_without_drops_is_replicated(self):
        """既有断言：不丢包时副本一致。"""
        cluster = Replica(nodes=3, rng=random.Random(1), drop_rate=0.0)
        cluster.append("cmd-0")
        self.assertEqual(cluster.ack_count("cmd-0"), 3)

    def test_committed_returns_prefix(self):
        """既有断言：committed 返回已提交前缀。"""
        cluster = Replica(nodes=3, rng=random.Random(2), drop_rate=0.0)
        cluster.append("cmd-0")
        cluster.append("cmd-1")
        self.assertEqual(cluster.committed(), ["cmd-0", "cmd-1"])

    def test_elect_leader_changes_term(self):
        """既有断言：换主会推进任期。"""
        cluster = Replica(nodes=3, rng=random.Random(3), drop_rate=0.0)
        before = cluster.term
        cluster.elect_leader()
        self.assertGreater(cluster.term, before)

    def test_ack_count_is_zero_for_unknown(self):
        """既有断言：不存在的命令 ack_count 为 0。"""
        cluster = Replica(nodes=3, rng=random.Random(4), drop_rate=0.0)
        self.assertEqual(cluster.ack_count("nope"), 0)


if __name__ == "__main__":
    unittest.main()
