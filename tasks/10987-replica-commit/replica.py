"""单进程内模拟三节点复制日志（网络丢包可注入）。

对外接口（不得更改签名）：
    Node(node_id)          字段：node_id, log, commit_index
    Replica(nodes=3, rng=None, drop_rate=0.0)
        .append(command) -> {"index": int, "committed": bool}
        .elect_leader()
        .ack_count(command) -> int
        .committed() -> list
        .leader_id
"""

import random


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.log = []
        self.commit_index = -1


class Replica:
    def __init__(self, nodes=3, rng=None, drop_rate=0.0):
        self.rng = rng or random.Random(0)
        self.drop_rate = drop_rate
        self.nodes = [Node(index) for index in range(nodes)]
        self.leader_id = 0
        self.term = 1

    def _leader(self):
        return self.nodes[self.leader_id]

    def append(self, command):
        leader = self._leader()
        leader.log.append(command)
        index = len(leader.log) - 1
        for node in self.nodes:
            if node.node_id == self.leader_id:
                continue
            if self.rng.random() < self.drop_rate:
                continue
            node.log = leader.log[:]
        leader.commit_index = index
        return {"index": index, "committed": True}

    def elect_leader(self):
        self.term += 1
        self.leader_id = self.rng.choice(self.nodes).node_id
        new_leader = self._leader()
        for node in self.nodes:
            if node.node_id == self.leader_id:
                continue
            if len(node.log) > len(new_leader.log):
                node.log = node.log[: len(new_leader.log)]

    def ack_count(self, command):
        return sum(1 for node in self.nodes if command in node.log)

    def committed(self):
        leader = self._leader()
        return list(leader.log[: leader.commit_index + 1])
