# mthread.py
"""Проверка списка ссылок в нескольких потоках."""
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

THREADS = 10
REQUEST_TIMEOUT = 10        # страховка, чтобы зависший сайт не держал поток


def read_urls(path):
    """Читает ссылки: пустые строки и строки, начинающиеся с #, пропускает."""
    with open(path, encoding="utf-8") as file:
        lines = (line.strip() for line in file)
        return [line for line in lines if line and not line.startswith("#")]


def check_url(url):
    """Возвращает (код ответа или "ERROR", время запроса, ссылка)."""
    start = time.perf_counter()
    try:
        status = requests.get(url, timeout=REQUEST_TIMEOUT).status_code
    except requests.RequestException:
        status = "ERROR"
    return status, time.perf_counter() - start, url


def main():
    if len(sys.argv) < 2:
        print("usage: mthread.py <urls file>", file=sys.stderr)
        return 2
    try:
        urls = read_urls(sys.argv[1])
    except OSError as error:
        print(error, file=sys.stderr)
        return 1

    start = time.perf_counter()
    with ThreadPoolExecutor(THREADS) as executor:
        results = list(executor.map(check_url, urls))
    total = time.perf_counter() - start

    for status, elapsed, url in results:
        print(f"{status:<5} {elapsed:.2f} s  {url}")
    print()
    print(f"Checked {len(urls)} links in {total:.1f} s")
    print(f"Sum of single request times: "
          f"{sum(elapsed for _, elapsed, _ in results):.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
