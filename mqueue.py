# mqueue.py
"""Разложение чисел на простые множители: очередь заданий и воркеры."""
import os
import sys
from collections import Counter
from multiprocessing import Process, Queue


def factorize(n):
    """Простые множители числа n перебором делителей."""
    if n < 2:
        raise ValueError(f"cannot factorize {n}")
    factors, d = [], 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append(n)
    return factors


def worker(tasks, results):
    """Берёт числа из очереди заданий до сигнала None, кладёт результаты."""
    while True:
        n = tasks.get()
        if n is None:
            break
        results.put((n, factorize(n)))


def format_factors(factors):
    """Одинаковые множители печатаются степенью: 12 -> 2^2 * 3."""
    return " * ".join(str(p) if k == 1 else f"{p}^{k}"
                      for p, k in sorted(Counter(factors).items()))


def read_numbers(path):
    """Читает числа из файла; плохие строки сообщает в stderr и пропускает."""
    numbers = []
    with open(path, encoding="utf-8") as file:
        for line_no, line in enumerate(file, 1):
            text = line.strip()
            if not text:
                continue
            try:
                n = int(text)
            except ValueError:
                print(f"line {line_no}: not a number: {text}",
                      file=sys.stderr)
                continue
            if n < 2:
                print(f"line {line_no}: cannot factorize {n}",
                      file=sys.stderr)
                continue
            numbers.append(n)
    return numbers


def main():
    if len(sys.argv) < 2:
        print("usage: mqueue.py <numbers file> [processes]", file=sys.stderr)
        return 2
    try:
        numbers = read_numbers(sys.argv[1])
    except OSError as error:
        print(error, file=sys.stderr)
        return 1
    count = int(sys.argv[2]) if len(sys.argv) > 2 else os.cpu_count()

    tasks, results = Queue(), Queue()
    workers = [Process(target=worker, args=(tasks, results))
               for _ in range(count)]
    for n in numbers:
        tasks.put(n)
    for _ in workers:
        tasks.put(None)                 # по одному сигналу остановки на воркер
    for process in workers:
        process.start()

    factored = [results.get() for _ in numbers]
    for process in workers:
        process.join()

    for n, factors in sorted(factored):
        print(f"{n} = {format_factors(factors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
