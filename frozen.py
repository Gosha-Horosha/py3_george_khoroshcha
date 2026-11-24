# frozen.py
"""Блокирующий вызов в корутине замораживает цикл событий."""
import asyncio
import time

TICK = 0.1
WORK = 1
MARGIN = 0.25           # ticker работает немного до и после «работы»


def blocking_call():
    """Имитирует стороннюю функцию, которую нельзя заменить на async."""
    time.sleep(1)


async def ticker(stamps):
    """Каждые 0,1 с записывает текущее время."""
    while True:
        stamps.append(time.perf_counter())
        await asyncio.sleep(TICK)


async def blocking_in_coroutine():
    """Вариант 1 (ошибочный): блокирующий вызов прямо в корутине."""
    blocking_call()


async def async_sleep():
    """Вариант 2: корутина ожидает asyncio.sleep."""
    await asyncio.sleep(WORK)


async def blocking_in_thread():
    """Вариант 3: блокирующий вызов уходит в отдельный поток."""
    await asyncio.to_thread(blocking_call)


async def run_variant(work):
    """Возвращает (длительность работы, макс. промежуток, число записей)."""
    stamps = []
    task = asyncio.create_task(ticker(stamps))
    await asyncio.sleep(MARGIN)
    start = time.perf_counter()
    await work()
    duration = time.perf_counter() - start
    await asyncio.sleep(MARGIN)
    task.cancel()
    pauses = [b - a for a, b in zip(stamps, stamps[1:])]
    return duration, max(pauses), len(stamps)


async def main():
    variants = [("time.sleep in coroutine", blocking_in_coroutine),
                ("await asyncio.sleep", async_sleep),
                ("asyncio.to_thread", blocking_in_thread)]
    print(f"{'variant':<24}{'work, s':>8}{'max pause, s':>14}{'ticks':>7}")
    for name, work in variants:
        duration, pause, ticks = await run_variant(work)
        print(f"{name:<24}{duration:>8.2f}{pause:>14.2f}{ticks:>7}")


if __name__ == "__main__":
    asyncio.run(main())
