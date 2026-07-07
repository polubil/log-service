import os
import signal
from threading import Thread
from httpx import Client, ConnectError

from logging import INFO
import random
import threading

from src.logger import logger
from src.string_gen import gen_string

def make_requests(client: Client, max_delay_ms: int, stop: threading.Event):
    while not stop.is_set():
        payload = gen_string()
        
        try:
            r = client.post(url="/api/data", json={"log": payload})
        except ConnectError as e: 
            stop.wait(2)


        logger.log(
            INFO,
            f'{threading.current_thread().name} "{payload}" {r.status_code}',
        )

        stop.wait(random.uniform(0, max_delay_ms) / 1000)

def start(client, workers, max_delay_ms):

    stop = threading.Event()
    for signal_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, signal_name, None)
        if sig is not None:
            signal.signal(sig, lambda _, __: stop.set())

    tr = [
        threading.Thread(
            target=make_requests, args=(client, max_delay_ms, stop)
        )
        for _ in range(workers)
    ]

    for t in tr:
        t.start()
    for t in tr:
        t.join()


if __name__ == "__main__":

    base_url = os.environ.get("BASE_URL")
    if not base_url:
        raise ValueError("BASE_URL not provided")

    workers = int(os.environ.get("WORKERS", 2))
    if workers <= 0:
        raise ValueError("WORKERS must be a positive integer")

    max_delay_ms = int(os.environ.get("MAX_DELAY_MS", 1000))
    if max_delay_ms < 0:
        raise ValueError("MAX_DELAY_MS must be non-negative integer")

    http_timeout = float(os.environ.get("HTTP_TIMEOUT", 2.0))
    if http_timeout <= 0:
        raise ValueError("HTTP_TIMEOUT must be non-negative float")

    http_client = Client(base_url=base_url, timeout=http_timeout)

    start(http_client, workers, max_delay_ms)
