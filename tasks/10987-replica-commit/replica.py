"""单进程内模拟三节点 Raft 复制日志（网络丢包/延迟/重启可注入）。

对外接口（签名不变）：
    Node(node_id)          字段：node_id, log, commit_index
                           内部字段：terms（每条日志的任期）、voted_term/voted_for
    Replica(nodes=3, rng=None, drop_rate=0.0)
        .append(command) -> {"index": int, "committed": bool}
        .elect_leader() -> int        # 返回当选后的任期
        .ack_count(command) -> int
        .committed() -> list
        .leader_id / .term

安全性规则（见 README.md）：
    1. 多数派：条目复制到多数派节点才允许 commit；
    2. 任期比较：候选人日志 (末条任期, 末条索引) 必须不比投票人旧才能得票；
    3. 日志匹配：按任期找最长公共前缀，冲突的未提交后缀才允许截断；
    4. 只提交当前任期：commit 只随本任期条目推进，旧任期条目靠其间接提交。
"""

import random


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.log = []
        self.commit_index = -1
        self.terms = []
        self.voted_term = -1
        self.voted_for = None


class Replica:
    def __init__(self, nodes=3, rng=None, drop_rate=0.0):
        self.rng = rng or random.Random(0)
        self.drop_rate = drop_rate
        self.nodes = [Node(index) for index in range(nodes)]
        self.leader_id = 0
        self.term = 1

    def _leader(self):
        return self.nodes[self.leader_id]

    def _majority(self):
        return len(self.nodes) // 2 + 1

    def _delivered(self):
        return self.rng.random() >= self.drop_rate

    @staticmethod
    def _last(node):
        last_term = node.terms[-1] if node.terms else -1
        return last_term, len(node.log) - 1

    def _as_up_to_date(self, candidate, voter):
        # Raft 投票限制：先比末条任期，再比日志长度。
        return self._last(candidate) >= self._last(voter)

    def _sync(self, leader, follower):
        # 一次 AppendEntries 批处理：按任期对齐最长公共前缀（日志匹配性质），
        # 仅删除冲突的未提交后缀，再补齐 leader 上的新条目。
        prefix = 0
        bound = min(len(leader.log), len(follower.log))
        while prefix < bound and leader.terms[prefix] == follower.terms[prefix]:
            prefix += 1
        follower.log = follower.log[:prefix] + leader.log[prefix:]
        follower.terms = follower.terms[:prefix] + leader.terms[prefix:]
        if leader.commit_index > follower.commit_index:
            follower.commit_index = min(leader.commit_index, len(follower.log) - 1)

    def append(self, command):
        leader = self._leader()
        index = len(leader.log)
        leader.log.append(command)
        leader.terms.append(self.term)
        acks = 1
        reached = []
        for follower in self.nodes:
            if follower is leader or not self._delivered():
                continue
            self._sync(leader, follower)
            acks += 1
            reached.append(follower)
        # 新条目必属当前任期；只有它得到多数派确认才推进 commit_index，
        # 其之前的旧任期条目随之被间接提交。
        committed = acks >= self._majority()
        if committed:
            leader.commit_index = index
            for follower in reached:
                follower.commit_index = index
        return {"index": index, "committed": committed}

    def elect_leader(self):
        winner = None
        for _ in range(64):  # 模拟随机超时重试，直到选出合法多数派领袖
            self.term += 1
            candidate = self.rng.choice(self.nodes)
            candidate.voted_term, candidate.voted_for = self.term, candidate.node_id
            votes = 1
            seen_commit = candidate.commit_index
            for voter in self.nodes:
                if voter is candidate or not self._delivered():
                    continue
                if voter.voted_term == self.term and voter.voted_for != candidate.node_id:
                    continue
                if self._as_up_to_date(candidate, voter):
                    voter.voted_term, voter.voted_for = self.term, candidate.node_id
                    seen_commit = max(seen_commit, voter.commit_index)
                    votes += 1
            if votes >= self._majority():
                # 候选日志含全部多数派已提交条目，可安全吸收投票者的提交水位，
                # 避免“日志已含但 commit_index 仍旧”导致的可见性回退。
                candidate.commit_index = min(seen_commit, len(candidate.log) - 1)
                winner = candidate
                break
        if winner is None:
            # 持续分区下重试仍未收敛：网络恢复后由日志最新的节点决胜。
            self.term += 1
            winner = max(self.nodes, key=self._last)
            winner.commit_index = min(
                max(node.commit_index for node in self.nodes), len(winner.log) - 1
            )
        self.leader_id = winner.node_id
        for follower in self.nodes:  # 当选后立即发心跳，推动落后节点追赶
            if follower is not winner and self._delivered():
                self._sync(winner, follower)
        return self.term

    def ack_count(self, command):
        return sum(1 for node in self.nodes if command in node.log)

    def committed(self):
        leader = self._leader()
        return list(leader.log[: leader.commit_index + 1])
