import random
import unittest

from replica import Replica


class TestReplica(unittest.TestCase):
    def _scripted(self, choices=(), draws=()):
        """确定性 rng：choices 控制 elect_leader 的候选人，draws 控制丢包。"""

        class ScriptedRNG:
            def __init__(self):
                self.choices = iter(choices)
                self.draws = iter(draws)

            def choice(self, seq):
                return seq[next(self.choices)]

            def random(self):
                return next(self.draws)

        return ScriptedRNG()

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

    def test_append_needs_majority(self):
        """少数派确认时不得提交；网络恢复后下一次复制可补上并提交。"""
        cluster = Replica(nodes=3, rng=random.Random(7), drop_rate=1.0)
        result = cluster.append("cmd-x")
        self.assertFalse(result["committed"])
        self.assertEqual(cluster.committed(), [])
        cluster.drop_rate = 0.0
        result = cluster.append("cmd-y")  # 同一任期补齐复制，间接提交 cmd-x
        self.assertTrue(result["committed"])
        self.assertIn("cmd-x", cluster.committed())
        self.assertEqual(cluster.ack_count("cmd-x"), 3)

    def test_split_brain_recovery(self):
        """脑裂期间提交的数据，在换主恢复后不得消失，读历史不得回退。"""
        cluster = Replica(nodes=3, rng=random.Random(11), drop_rate=0.0)
        cluster.append("a")
        cluster.append("b")
        self.assertEqual(cluster.ack_count("b"), 3)
        cluster.drop_rate = 1.0  # 完全分区：旧主 0 隔离
        cluster.append("c")
        self.assertFalse(cluster.committed().count("c"))
        cluster.drop_rate = 0.0  # 网络恢复，多数派一侧换主
        cluster.elect_leader()
        self.assertEqual(cluster.committed(), ["a", "b"])
        self.assertEqual(cluster.ack_count("a"), 3)
        self.assertEqual(cluster.ack_count("b"), 3)

    def test_lagging_node_catches_up(self):
        """落后节点的未提交旧尾必须按日志匹配性质对齐，并最终追平已提交前缀。"""
        # 选举序列：1、0；节点 2 连续错过两次心跳和中间的复制，随后一次补齐。
        rng = self._scripted(
            choices=(1, 0),
            draws=(1.0, 1.0,                    # append a（1=送达 0=丢弃）
                    1.0, 1.0, 1.0, 0.0,         # elect#1 投票 + 心跳(丢给 2)
                    1.0, 0.0,                    # append b（2 丢失）
                    1.0, 1.0, 1.0, 0.0,         # elect#2 投票 + 心跳(丢给 2)
                    1.0, 1.0),                  # append c：节点 2 一次追平
        )
        cluster = Replica(nodes=3, rng=rng, drop_rate=1.0)
        cluster.append("a")
        cluster.elect_leader()
        cluster.append("b")
        cluster.elect_leader()
        self.assertEqual(cluster.ack_count("b"), 2)
        cluster.append("c")  # 节点 2 此轮收到复制，按任期对齐并补齐
        self.assertEqual(cluster.ack_count("a"), 3)
        self.assertEqual(cluster.ack_count("b"), 3)
        self.assertEqual(cluster.ack_count("c"), 3)
        self.assertEqual(cluster.nodes[2].log[: cluster.nodes[2].commit_index + 1],
                         ["a", "b", "c"])

    def test_term_cross_uncommitted_tail_truncated(self):
        """任期交叉：旧主分区期内的未提交尾必须被新高任期日志截断。"""
        # 选举序列：0（连任 t2）、2（t3 当选，不含节点 0 的未提交尾）。
        rng = self._scripted(
            choices=(0, 2),
            draws=(1.0, 1.0,                    # append a（1=送达 0=丢弃）
                    1.0, 1.0, 1.0, 1.0,         # elect#1 投票 + 心跳
                    0.0, 0.0,                    # 分区：b-stale 只在节点 0
                    1.0, 1.0, 1.0, 1.0,         # elect#2 投票 + 心跳（截断旧尾）
                    1.0, 1.0),                  # append c
        )
        cluster = Replica(nodes=3, rng=rng, drop_rate=1.0)
        cluster.append("a")
        cluster.elect_leader()
        cluster.append("b-stale")
        self.assertEqual(cluster.ack_count("b-stale"), 1)
        cluster.elect_leader()
        self.assertEqual(cluster.leader_id, 2)
        self.assertEqual(cluster.ack_count("b-stale"), 0)  # 冲突的未提交尾被截断
        cluster.append("c")
        self.assertEqual(cluster.committed(), ["a", "c"])

    def test_commit_then_crash_and_restart(self):
        """已提交条目在主节点崩溃、新主当选后依旧存在且仍为已提交前缀。"""
        cluster = Replica(nodes=3, rng=random.Random(23), drop_rate=0.0)
        cluster.append("durable-0")
        cluster.append("durable-1")
        before = cluster.committed()
        cluster.drop_rate = 1.0  # 旧主崩溃 / 完全失联
        cluster.drop_rate = 0.0
        cluster.elect_leader()
        self.assertEqual(cluster.committed(), before)
        self.assertGreaterEqual(cluster.ack_count("durable-0"), 2)
        self.assertGreaterEqual(cluster.ack_count("durable-1"), 2)
        cluster.elect_leader()
        self.assertEqual(cluster.committed(), before)
        self.assertEqual(cluster.ack_count("durable-0"), 3)
        self.assertEqual(cluster.ack_count("durable-1"), 3)


if __name__ == "__main__":
    unittest.main()
