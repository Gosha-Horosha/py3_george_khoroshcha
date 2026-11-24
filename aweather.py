# aweather.py
"""Текущая температура в городах: асинхронные запросы через httpx."""
import asyncio
import csv
import sys

import httpx

API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 5


def read_cities(path):
    """Читает CSV со столбцами city, latitude, longitude."""
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


async def fetch_temperature(client, city):
    """Температура в городе или None, если получить её не удалось."""
    try:
        params = {"latitude": city["latitude"],
                  "longitude": city["longitude"],
                  "current_weather": "true"}
        response = await client.get(API_URL, params=params)
        if response.status_code != 200:
            return None
        return float(response.json()["current_weather"]["temperature"])
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


async def fetch_all(cities):
    """Запрашивает все города одновременно, результаты в порядке файла."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(fetch_temperature(client, city))
                     for city in cities]
    return [task.result() for task in tasks]


def print_table(names, temperatures):
    """Печатает таблицу по убыванию температуры, города без данных в конце."""
    known = [(t, name) for name, t in zip(names, temperatures)
             if t is not None]
    known.sort(key=lambda item: item[0], reverse=True)
    missing = [name for name, t in zip(names, temperatures) if t is None]
    width = max((len(name) for name in names), default=4)
    width = max(width, len("City"))
    print(f"{'City':<{width}}  {'Temperature':>11}")
    for temperature, name in known:
        print(f"{name:<{width}}  {f'{temperature:.1f} °C':>11}")
    for name in missing:
        print(f"{name:<{width}}  {'нет данных':>11}")


def main():
    if len(sys.argv) < 2:
        print("usage: aweather.py <cities.csv>", file=sys.stderr)
        return 2
    try:
        cities = read_cities(sys.argv[1])
    except OSError as error:
        print(error, file=sys.stderr)
        return 1
    temperatures = asyncio.run(fetch_all(cities))
    print_table([city["city"] for city in cities], temperatures)
    return 0


if __name__ == "__main__":
    sys.exit(main())
