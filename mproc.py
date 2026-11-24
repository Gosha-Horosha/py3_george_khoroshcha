# mproc.py
"""Умножение матриц в нескольких процессах."""
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

USAGE = 'usage: mproc.py "<A>" "<B>"  |  mproc.py <n>'


def parse_number(token):
    """Превращает слово в int, а если не получилось, то в float."""
    try:
        return int(token)
    except ValueError:
        return float(token)


def parse_matrix(text):
    """Разбирает строку вида "1 2,3 4" в список строк матрицы."""
    try:
        rows = [[parse_number(token) for token in row.split()]
                for row in text.split(",")]
    except ValueError:
        raise ValueError(f"invalid matrix: {text!r}") from None
    if not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError(f"invalid matrix: {text!r}")
    return rows


def format_number(value):
    """Печатает число без лишних нулей: 19, а не 19.0."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def multiply_rows(rows, columns):
    """Умножает блок строк на матрицу, заданную списком её столбцов."""
    return [[sum(x * y for x, y in zip(row, column)) for column in columns]
            for row in rows]


def split_rows(rows, parts):
    """Делит строки на parts подряд идущих блоков почти равной длины."""
    size, extra = divmod(len(rows), parts)
    blocks, start = [], 0
    for i in range(parts):
        end = start + size + (1 if i < extra else 0)
        blocks.append(rows[start:end])
        start = end
    return blocks


def multiply_sequential(a, b):
    """Обычное умножение матриц в одном процессе."""
    return multiply_rows(a, list(zip(*b)))


def multiply_parallel(a, b, workers):
    """Умножение блоками строк A в workers процессах."""
    columns = list(zip(*b))
    with ProcessPoolExecutor(workers) as executor:
        parts = executor.map(multiply_rows, split_rows(a, workers),
                             repeat(columns))
        return [row for part in parts for row in part]


def count_workers(rows):
    """Число процессов: os.cpu_count(), но не больше числа строк."""
    return min(os.cpu_count() or 1, rows)


def multiply_command(text_a, text_b):
    """Режим «две матрицы из командной строки»."""
    try:
        a, b = parse_matrix(text_a), parse_matrix(text_b)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    if len(a[0]) != len(b):
        print(f"error: A has {len(a[0])} columns, B has {len(b)} rows",
              file=sys.stderr)
        return 1
    for row in multiply_parallel(a, b, count_workers(len(a))):
        print(" ".join(format_number(value) for value in row))
    return 0


def random_matrix(rng, n):
    """Случайная матрица n x n из целых чисел от 0 до 9."""
    return [[rng.randint(0, 9) for _ in range(n)] for _ in range(n)]


def benchmark_command(n):
    """Режим «случайные матрицы n x n»: сравнение времени и проверка."""
    rng = random.Random(1)
    a, b = random_matrix(rng, n), random_matrix(rng, n)
    workers = count_workers(n)

    start = time.perf_counter()
    sequential = multiply_sequential(a, b)
    sequential_time = time.perf_counter() - start

    start = time.perf_counter()
    parallel = multiply_parallel(a, b, workers)
    parallel_time = time.perf_counter() - start

    label = f"row blocks ({workers} processes)"
    print(f"n = {n}, workers = {workers}")
    print(f"{'sequential':<30}{sequential_time:.2f} s")
    print(f"{label:<30}{parallel_time:.2f} s")
    print(f"results equal: {sequential == parallel}")
    print(f"speedup of row blocks: {sequential_time / parallel_time:.2f}x")
    return 0


def main(argv):
    if len(argv) == 3:
        return multiply_command(argv[1], argv[2])
    if len(argv) == 2 and argv[1].isdigit() and int(argv[1]) > 0:
        return benchmark_command(int(argv[1]))
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
