# cpu_io.py
"""Определяет тип нагрузки заданий и проверяет, что их ускоряет."""
import hashlib
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

TASKS_PER_JOB = 8
CPU_BOUND_RATIO = 0.8


def primes_job(_=None):
    """Вычисления на чистом Python."""
    return sum(1 for n in range(2, 150_000)
               if all(n % d for d in range(2, int(n ** 0.5) + 1)))


def wait_job(_=None):
    """Ожидание (имитация ответа сети)."""
    time.sleep(0.5)


def hash_job(_=None):
    """Вычисления в C: SHA-256 от 100 МБ (hashlib отпускает GIL)."""
    return hashlib.sha256(bytes(100_000_000)).hexdigest()


JOBS = [primes_job, wait_job, hash_job]


def cpu_wall_ratio(job):
    """Запускает задание один раз и возвращает отношение CPU time к wall."""
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    job()
    cpu = time.process_time() - cpu_start
    wall = time.perf_counter() - wall_start
    return cpu / wall


def run_sequential(job, count):
    """Выполняет count копий задания последовательно."""
    for i in range(count):
        job(i)


def run_in_pool(executor_class, job, count, workers):
    """Выполняет count копий задания в пуле из workers воркеров."""
    with executor_class(workers) as executor:
        list(executor.map(job, range(count)))


def measure(func, *args):
    """Возвращает время работы func(*args) в секундах."""
    start = time.perf_counter()
    func(*args)
    return time.perf_counter() - start


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else os.cpu_count()
    print(f"Tasks per job: {TASKS_PER_JOB}, workers: {workers}")
    print(f"{'job':<11}{'type':<13}{'cpu/wall':>8}  {'sequential':>10}"
          f"  {'threads':>7}  {'processes':>9}  fastest")
    for job in JOBS:
        ratio = cpu_wall_ratio(job)
        kind = "CPU-bound" if ratio >= CPU_BOUND_RATIO else "I/O-bound"
        times = {
            "sequential": measure(run_sequential, job, TASKS_PER_JOB),
            "threads": measure(run_in_pool, ThreadPoolExecutor, job,
                               TASKS_PER_JOB, workers),
            "processes": measure(run_in_pool, ProcessPoolExecutor, job,
                                 TASKS_PER_JOB, workers),
        }
        fastest = min(times, key=times.get)
        print(f"{job.__name__:<11}{kind:<13}{ratio:>8.2f}  "
              f"{times['sequential']:>10.2f}  {times['threads']:>7.2f}  "
              f"{times['processes']:>9.2f}  {fastest}")


if __name__ == "__main__":
    main()
