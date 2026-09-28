"""带后台计算的任务服务。

对外接口（不得更改签名）：
    Job(job_id, steps)   字段：cancelled, done, result
    JobService(workers=4, steps=100, step_seconds=0.002)
        .submit(count) -> [Job]
        .cancel(job)
        .shutdown(grace=None)
        .pending() -> int
"""

import queue
import threading
import time


class Job:
    def __init__(self, job_id, steps):
        self.job_id = job_id
        self.steps = steps
        self.cancelled = False
        self.done = False
        self.result = None


class JobService:
    def __init__(self, workers=4, steps=100, step_seconds=0.002):
        self.steps = steps
        self.step_seconds = step_seconds
        self.queue = queue.Queue()
        self.workers = []
        self.jobs = []
        for index in range(workers):
            thread = threading.Thread(target=self._run, name=f"jobsvc-{index}", daemon=True)
            thread.start()
            self.workers.append(thread)

    def submit(self, count):
        created = []
        for index in range(count):
            job = Job(len(self.jobs), self.steps)
            self.jobs.append(job)
            created.append(job)
            self.queue.put(job)
        return created

    def cancel(self, job):
        job.cancelled = True

    def pending(self):
        return self.queue.qsize()

    def _run(self):
        while True:
            job = self.queue.get()
            if job is None:
                self.queue.task_done()
                return
            total = 0
            for _ in range(job.steps):
                time.sleep(self.step_seconds)
                total += 1
            job.result = total
            job.done = True
            self.queue.task_done()

    def shutdown(self, grace=None):
        for _ in self.workers:
            self.queue.put(None)
        for thread in self.workers:
            thread.join(timeout=grace)
