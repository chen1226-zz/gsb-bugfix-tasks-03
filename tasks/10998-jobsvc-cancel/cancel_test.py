"""复现脚本：提交一批任务后全部取消，检查线程是否能及时退出。"""

import threading
import time

from jobsvc import JobService

JOBS = 20
WORKERS = 4
STEPS = 100
STEP_SECONDS = 0.002          # 单个任务约 200ms
CANCEL_AFTER = 0.05
EXIT_BUDGET = 0.35


def main():
    base_threads = threading.active_count()
    service = JobService(workers=WORKERS, steps=STEPS, step_seconds=STEP_SECONDS)
    jobs = service.submit(JOBS)
    time.sleep(CANCEL_AFTER)

    for job in jobs:
        service.cancel(job)

    started = time.perf_counter()
    service.shutdown(grace=10)
    elapsed = time.perf_counter() - started
    time.sleep(0.05)
    now_threads = threading.active_count()

    completed = sum(1 for job in jobs if job.done and not job.cancelled)
    leaked = now_threads - base_threads

    problems = []
    if elapsed > EXIT_BUDGET:
        problems.append(f"取消后用了 {elapsed * 1000:.0f}ms 才退出（预算 {EXIT_BUDGET * 1000:.0f}ms）")
    if leaked > 0:
        problems.append(f"线程数没有回到基线，多出 {leaked} 个")
    if completed > WORKERS:
        problems.append(f"取消之后还有 {completed} 个任务跑完了")

    if problems:
        print(f"FAIL: all workers exited in {elapsed * 1000:.0f}ms, threads +{leaked}")
        for item in problems:
            print("  - " + item)
        raise SystemExit(1)
    print(f"OK: all workers exited in {elapsed * 1000:.0f}ms, threads back to baseline")


if __name__ == "__main__":
    main()
