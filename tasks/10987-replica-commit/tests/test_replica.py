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


class TestReplicaSafety(unittest.TestCase):
    """新增用例：脑裂恢复 / 落后追赶 / 任期交叉 / 崩溃恢复。"""

    def test_split_brain_recovery(self):
        """脑裂恢复：旧主未提交条目被覆盖，已提交条目保留。"""
        cluster = Replica(nodes=3, rng=random.Random(7), drop_rate=0.0)
        cluster.append("a")
        self.assertEqual(cluster.committed(), ["a"])
        old_leader = cluster.leader_id
        cluster.drop_rate = 1.0  # 旧主被隔离，写入到不了任何跟随者
        self.assertFalse(cluster.append("x")["committed"])
        while cluster.leader_id == old_leader:
            cluster.elect_leader()  # 另一分区选出新主
        cluster.drop_rate = 0.0  # 网络恢复
        cluster.append("b")
        for node in cluster.nodes:
            self.assertEqual(node.log, ["a", "b"])  # 分歧的 x 被修复掉
        self.assertEqual(cluster.committed(), ["a", "b"])
        self.assertGreaterEqual(cluster.ack_count("a"), 2)

    def test_lagging_node_catches_up(self):
        """落后节点追赶：丢包落下的节点最终与领导者日志一致。"""
        cluster = Replica(nodes=3, rng=random.Random(11), drop_rate=0.4)
        for i in range(6):
            cluster.append(f"cmd-{i}")
        cluster.drop_rate = 0.0  # 网络恢复
        cluster.append("final")
        leader = cluster.nodes[cluster.leader_id]
        for node in cluster.nodes:
            self.assertEqual(node.log, leader.log)
            self.assertEqual(node.terms, leader.terms)
        self.assertEqual(cluster.committed(), leader.log)

    def test_term_crossing_does_not_commit_old_term_entry(self):
        """任期交叉：旧任期条目即使在多数派上，也不能被直接提交。"""
        cluster = Replica(nodes=3, rng=random.Random(5), drop_rate=0.0)
        cluster.append("a")  # 任期 1，已提交
        cluster.elect_leader()  # 任期 2
        # 手工构造：任期 2 的未提交条目 "b" 已落在多数派（主 + 一个跟随者）上
        leader = cluster.nodes[cluster.leader_id]
        leader.log.append("b")
        leader.terms.append(cluster.term)
        follower = next(n for n in cluster.nodes
                        if n.node_id != cluster.leader_id)
        follower.log.append("b")
        follower.terms.append(cluster.term)
        cluster.elect_leader()  # 任期 3，新主日志里带有 b
        new_leader = cluster.nodes[cluster.leader_id]
        self.assertIn("b", new_leader.log)
        # b 是旧任期条目，不允许被直接提交
        self.assertEqual(cluster.committed(), ["a"])
        # 任期 3 的条目提交后，b 随之间接提交
        cluster.append("c")
        self.assertEqual(cluster.committed(), ["a", "b", "c"])

    def test_crash_recovery_after_commit(self):
        """提交后立即崩溃再恢复：已提交数据不丢、历史不回退。"""
        cluster = Replica(nodes=3, rng=random.Random(9), drop_rate=0.0)
        cluster.append("a")
        cluster.append("b")
        self.assertEqual(cluster.committed(), ["a", "b"])
        # 模拟全体重启：日志已落盘保留，易失的 commit_index 丢失
        for node in cluster.nodes:
            node.commit_index = -1
        cluster.elect_leader()
        cluster.append("c")  # 新任期条目提交，恢复全部已提交历史
        self.assertEqual(cluster.committed(), ["a", "b", "c"])
        self.assertGreaterEqual(cluster.ack_count("a"), 2)
        self.assertGreaterEqual(cluster.ack_count("b"), 2)

    def test_committed_entries_survive_random_chaos(self):
        """随机故障回归：任何已提交条目永远留在多数派上。"""
        rng = random.Random(42)
        for _ in range(50):
            cluster = Replica(nodes=3, rng=rng, drop_rate=rng.random() * 0.5)
            committed = []
            for i in range(10):
                if cluster.append(f"cmd-{i}")["committed"]:
                    committed.append(f"cmd-{i}")
                if rng.random() < 0.4:
                    cluster.elect_leader()
            for cmd in committed:
                self.assertGreaterEqual(cluster.ack_count(cmd), 2)
