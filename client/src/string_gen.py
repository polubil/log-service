import random

METHODS = ["GET", "POST", "OPTIONS", "DELETE", "PUT", "PATCH", "HEAD"]
STATUS_CODES = [
    "100",
    "101",
    "200",
    "201",
    "301",
    "302",
    "303",
    "304",
    "400",
    "401",
    "402",
    "403",
    "404",
    "408",
    "409",
    "419",
    "422",
    "500",
]
URIS=["/api/users", "/api/auth", "/login", "/logout", "/api/list"]


def gen_string():
    ip = ".".join([str(random.randint(0, 255)) for _ in range(4)])
    method = random.choice(METHODS)
    status_code = random.choice(STATUS_CODES)
    uri = random.choice(URIS)

    return " ".join([ip, method, uri, status_code])
