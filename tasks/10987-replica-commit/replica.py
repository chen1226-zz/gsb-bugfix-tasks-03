"""单进程内模拟三节点复制日志（网络丢包可注入）。

对外接口（不得更改签名）：
    Node(node_id)          字段：node_id, log, commit_index
    Replica(nodes=3, rng=None, drop_rate=0.0)
        .append(command) -> {"index": int, "committed": bool}
        .elect_leader()
        .ack_count(command) -> int
        .committed() -> list
        .leader_id

提交规则（Raft）：
    1. 多数派提交：条目被复制到多数派（> n/2）后才允许提交；
    2. 只提交当前任期：领导者仅依据当前任期条目的多数派复制
       直接推进 commit_index，旧任期条目随之间接提交，
       避免任期交叉时把可能被覆盖的旧条目误判为已提交；
    3. 任期比较 + 日志匹配：选举时选民只投票给日志至少与自己
       一样新的候选者（按 (末条任期, 末条下标) 字典序比较），
       保证新领导者拥有全部已提交条目（领导者完备性）；
    4. 复制即修复：AppendEntries 找到最长一致前缀，截断跟随者
       分歧后缀再追加，已提交条目永远不会被覆盖或删除。
"""

import random


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.log = []           # 已落盘的命令序列
        self.terms = []         # 每条命令写入时的任期（与 log 等长）
        self.commit_index = -1  # 易失状态，重启后靠新任期条目重新推进


class Replica:
    def __init__(self, nodes=3, rng=None, drop_rate=0.0):
        self.rng = rng or random.Random(0)
        self.drop_rate = drop_rate
        self.nodes = [Node(index) for index in range(nodes)]
        self.leader_id = 0
        self.term = 1

    @property
    def _majority(self):
        return len(self.nodes) // 2 + 1

    def _leader(self):
        return self.nodes[self.leader_id]

    @staticmethod
    def _log_version(node):
        """日志新旧程度：先比末条任期，再比日志长度。"""
        last_term = node.terms[-1] if node.terms else 0
        return (last_term, len(node.log))

    def _replicate(self, follower):
        """AppendEntries：跟随者截断分歧后缀，对齐到领导者日志。"""
        leader = self._leader()
        common = min(len(leader.log), len(follower.log))
        match = 0
        while (match < common
               and follower.log[match] == leader.log[match]
               and follower.terms[match] == leader.terms[match]):
            match += 1
        # 已提交条目必然存在于领导者日志的相同下标处（领导者完备性），
        # 因此这里截断的只会是未提交的分歧后缀。
        follower.log = follower.log[:match] + leader.log[match:]
        follower.terms = follower.terms[:match] + leader.terms[match:]
        follower.commit_index = min(leader.commit_index, len(follower.log) - 1)

    def append(self, command):
        leader = self._leader()
        leader.log.append(command)
        leader.terms.append(self.term)
        index = len(leader.log) - 1
        for node in self.nodes:
            if node.node_id == self.leader_id:
                continue
            if self.rng.random() < self.drop_rate:
                continue  # 消息丢失，跟随者本轮收不到
            self._replicate(node)
        # 提交规则：多数派持有 + 条目属于当前任期，二者缺一不可。
        replicas = sum(
            1 for node in self.nodes
            if len(node.log) > index and node.terms[index] == self.term
        )
        if replicas >= self._majority:
            leader.commit_index = max(leader.commit_index, index)
        return {"index": index, "committed": leader.commit_index >= index}

    def elect_leader(self):
        self.term += 1
        old_leader = self._leader()
        candidate = self.rng.choice(self.nodes)
        # RequestVote：选民只把票投给日志不比自己旧的候选者。
        votes = sum(
            1 for node in self.nodes
            if self._log_version(candidate) >= self._log_version(node)
        )
        if votes >= self._majority:
            self.leader_id = candidate.node_id
        else:
            # 候选者日志过旧拿不到多数票；等价于重试选举直到日志
            # 最新的节点当选（它必然能获得全票）。
            best = max(self.nodes,
                       key=lambda n: (self._log_version(n), n.node_id))
            self.leader_id = best.node_id
        new_leader = self._leader()
        # 领导者完备性保证旧主已提交的条目都在新主日志中，
        # 因此新主可以安全继承已提交水位，客户端读不到回退。
        new_leader.commit_index = max(new_leader.commit_index,
                                      old_leader.commit_index)

    def ack_count(self, command):
        return sum(1 for node in self.nodes if command in node.log)

    def committed(self):
        leader = self._leader()
        return list(leader.log[: leader.commit_index + 1])
