import os
import signal
from httpx import Client, ConnectError

from logging import INFO
import random
import threading

from src.logger import logger
from src.string_gen import gen_string

def make_requests(client: Client, url: str, max_delay_ms: int, stop: threading.Event):
    while not stop.is_set():
        payload = gen_string()

        try:
            r = client.post(url=url, json={"log": payload})
        except ConnectError as e: 
            stop.wait(2)
        finally:
            logger.log(
                INFO,
                f'{threading.current_thread().name} "{payload}" {r.status_code}',
            )

            stop.wait(random.uniform(0, max_delay_ms) / 1000)



def start(client: Client, url: str, workers: int, max_delay_ms: int):

    stop = threading.Event()
    for signal_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, signal_name, None)
        if sig is not None:
            signal.signal(sig, lambda _, __: stop.set())

    tr = [
        threading.Thread(
            target=make_requests, args=(client, url, max_delay_ms, stop)
        )
        for _ in range(workers)
    ]

    for t in tr:
        t.start()
    for t in tr:
        t.join()


if __name__ == "__main__":

    url = os.environ.get("CLIENT_REQUESTS_URL")
    if not url:
        raise ValueError("CLIENT_REQUESTS_URL not provided")

    workers = int(os.environ.get("CLIENT_WORKERS", 2))
    if workers <= 0:
        raise ValueError("CLIENT_WORKERS must be a positive integer")

    max_delay_ms = int(os.environ.get("CLIENT_MAX_DELAY_MS", 1000))
    if max_delay_ms < 0:
        raise ValueError("CLIENT_MAX_DELAY_MS must be non-negative integer")

    http_timeout = float(os.environ.get("CLIENT_HTTP_TIMEOUT", 2.0))
    if http_timeout <= 0:
        raise ValueError("CLIENT_HTTP_TIMEOUT must be non-negative float")

    http_client = Client(timeout=http_timeout)

    start(http_client, url, workers, max_delay_ms)
