import asyncio
import csv
from datetime import datetime
from io import TextIOWrapper
from httpx import AsyncClient, ConnectError
import os
import fcntl


"""
Идея заключается в том, что когда в csv записываем новые данные, они упорядочены по возрастанию даты.
Нам нужна первая строка, поэтому читаем файл с конца и забираем первую (с конца) строку.
"""
def reverse_readlines(fd: int, buf_size: int = 4096, encoding: str = "utf-8"):
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

async def fetch_data(client: AsyncClient, gt_date: datetime | None, retries: int = 3):
    try:
        data = await client.get("/api/data", params={
            "gt": gt_date
        } if gt_date else {})
        print(data)
        return data.json()
    except ConnectError as e:
        if retries > 0:
            await asyncio.sleep((4-retries)**2)
            return await fetch_data(client, gt_date, retries-1)

def get_last_date(filename: str) -> datetime | None:
    header = ["id", "created", "ip", "method", "uri", "status_code"]
    exists = os.path.exists(filename)
    print(exists)
    if not exists:
        with open(filename, "x", encoding="UTF-8") as f:
            writer = csv.writer(f)
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
            writer.writerow([d["id"], d["created"], log["ip"], log["method"], log["uri"], log["status_code"]])

async def start():
    delay_s = 5.0 # from env
    http_client = AsyncClient(base_url="http://api:8000") # from env
    limit = int(os.environ.get("limit", 100))
    basedir = "data/"
    filename = "data.csv" # from env
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
            data = await fetch_data(client=http_client, gt_date=gt_date, limit=limit)
            write_new_data(path_to_file, data)
            print(data)

            fcntl.flock(f, fcntl.LOCK_UN)

        await asyncio.sleep(delay_s)

def main():
    asyncio.run(start())

if __name__ == "__main__":
    main()