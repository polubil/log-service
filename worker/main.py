import asyncio
import csv
import fcntl
import os
from datetime import datetime
from typing import Generator

from httpx import AsyncClient, ConnectError


def reverse_readlines(fd: int, buf_size: int = 4096, encoding: str = "utf-8") -> Generator[str]:
    """
    Идея заключается в том, что когда в csv записываем новые данные, они упорядочены по возрастанию даты.
    Нам нужна первая строка, поэтому читаем файл с конца и забираем первую (с конца) строку.
    """
    with open(fd, "rb") as f:
        f.seek(0, os.SEEK_END)
        position = f.tell()
        trailing = b""
        while position > 0:
            read_size = min(buf_size, position)
            position -= read_size
            f.seek(position)
            chunk = f.read(read_size) + trailing
            lines = chunk.split(b"\n")
            trailing = lines[0]
            for line in reversed(lines[1:]):
                if line:
                    yield line.decode(encoding)
        if trailing:
            yield trailing.decode(encoding)


async def fetch_data(
    client: AsyncClient, 
    url: str, 
    gt_date: datetime | None, 
    limit: int = 100, 
    retries: int = 3) -> list[dict[str]]:
    try:
        params = {"limit": limit}
        if gt_date:
            params["gt"] = gt_date
        data = await client.get(url, params=params)
        return data.json()
    except ConnectError as e:
        if retries > 0:
            await asyncio.sleep((4 - retries) ** 2)
            return await fetch_data(client, url, gt_date, limit, retries - 1)
        return []


def get_last_date(filename: str) -> datetime | None:
    header = ["id", "created", "ip", "method", "uri", "status_code"]
    exists = os.path.exists(filename)
    if not exists:
        with open(filename, "x", encoding="UTF-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            return None

    last_row = next(reverse_readlines(filename))
    r = csv.reader([last_row])
    return list(r)[0][1]


def write_new_data(filename: str, data: list[dict]):
    with open(filename, "a", encoding="UTF-8") as f:
        for d in data:
            log = d["log"]
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(
                [
                    d["id"],
                    d["created"],
                    log["ip"],
                    log["method"],
                    log["uri"],
                    log["status_code"],
                ]
            )


async def start():
    url = os.environ.get("WORKER_REQUESTS_URL", "http://api:8000/api/data")
    try:
        delay_s = int(os.environ.get("WORKER_REQUESTS_DELAY_S", 10))
        if delay_s < 1:
            raise ValueError()
    except ValueError as e:
        raise ValueError("WORKER_REQUESTS_DELAY_S must be positive int") from e
    
    try:
        limit = int(os.environ.get("WORKER_REQUESTS_MAX_ROWS", 100))
    except ValueError as e:
        if limit < 1:
            raise ValueError()
        raise ValueError("WORKER_REQUESTS_MAX_ROWS must be positive int") from e

    try:
        http_timeout = int(os.environ.get("WORKER_HTTP_TIMEOUT", 2))
    except ValueError as e:
        if http_timeout < 1:
            raise ValueError()
        raise ValueError("WORKER_HTTP_TIMEOUT must be positive int") from e

    data_filename = os.environ.get("WORKER_DATA_FILENAME", "data")

    http_client = AsyncClient(timeout=http_timeout)

    basedir = "data/"
    filename = f"{data_filename}.csv"
    lockfile = "data.lock"

    if not os.path.exists(basedir):
        os.makedirs(basedir)

    path_to_file = os.path.join(basedir, filename)
    path_to_lock = os.path.join(basedir, lockfile)

    if not os.path.exists(path_to_lock):
        os.mknod(path_to_lock)
    while 1:
        with open(path_to_lock) as f:
            fcntl.flock(f, fcntl.LOCK_EX)

            gt_date = get_last_date(path_to_file)
            data = await fetch_data(client=http_client, url=url, gt_date=gt_date, limit=limit)
            write_new_data(path_to_file, data)

            fcntl.flock(f, fcntl.LOCK_UN)

        await asyncio.sleep(delay_s)


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
