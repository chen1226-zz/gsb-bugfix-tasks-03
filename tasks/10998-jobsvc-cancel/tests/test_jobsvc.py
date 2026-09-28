import unittest

from jobsvc import JobService


class TestJobService(unittest.TestCase):
    def test_job_completes(self):
        """既有断言：正常提交的任务会跑完。"""
        service = JobService(workers=2, steps=5, step_seconds=0.001)
        jobs = service.submit(2)
        service.shutdown(grace=5)
        self.assertTrue(all(job.done for job in jobs))

    def test_result_records_steps(self):
        """既有断言：result 记录完成的步数。"""
        service = JobService(workers=1, steps=5, step_seconds=0.001)
        job = service.submit(1)[0]
        service.shutdown(grace=5)
        self.assertEqual(job.result, 5)

    def test_cancel_marks_job(self):
        """既有断言：cancel 会把任务标记为已取消。"""
        service = JobService(workers=1, steps=5, step_seconds=0.001)
        job = service.submit(1)[0]
        service.cancel(job)
        self.assertTrue(job.cancelled)
        service.shutdown(grace=5)


if __name__ == "__main__":
    unittest.main()
