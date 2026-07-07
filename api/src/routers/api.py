from datetime import datetime
from typing import Annotated
from fastapi import Depends, HTTPException, Query, APIRouter, Request
from fastapi.responses import JSONResponse, Response
from src.data.db import DB
from src.data.models import AggregationResult, LogRequest, Log, Method

router = APIRouter(prefix="/api")


def get_db(request: Request) -> DB:
    return request.app.state.db


def parse_log_line(raw: str) -> Log:
    parts = raw.split(" ")
    if len(parts) != 4:
        raise ValueError("Incorrect data format.")
    ip, method, uri, status_code = parts
    if not uri.startswith("/"):
        raise ValueError("Incorrect Uri format")
    return Log(ip=ip, method=method, uri=uri, status_code=status_code)


@router.post("/data")
async def post(request: LogRequest, db: Annotated[DB, Depends(get_db)]) -> Response:
    try:
        log = parse_log_line(request.log)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Incorrect data format") from e

    res = await db.insert(log)
    return Response("Success", 201)


@router.get("/data")
async def get(
    db: Annotated[DB, Depends(get_db)],
    method: Annotated[list[Method] | None, Query()] = None,
    status_code: Annotated[list[int] | None, Query()] = None,
    lt: datetime | None = None,
    gt: datetime | None = None,
    limit: int = 10,
    offset: int = 0,
):

    logs: list[Log] = await db.fetch(method, status_code, lt, gt, limit, offset)

    response = []
    for log in logs:
        response.append(
            {
                "id": str(log.id),
                "created": log.created.isoformat(),
                "log": {
                    "ip": str(log.ip),
                    "method": log.method,
                    "uri": log.uri,
                    "status_code": log.status_code,
                },
            }
        )

    return JSONResponse(response, 200)


@router.get("/stats")
async def stats(
    lt: datetime | None = None,
    gt: datetime | None = None,
    db: Annotated[DB, Depends(get_db)] = Depends(get_db),
) -> AggregationResult:
    methods = await db.get_stats("method", lt, gt)
    status_codes = await db.get_stats("status_code", lt, gt)
    return AggregationResult(methods=methods, status_codes=status_codes)

@router.get("/health")
async def health():
    return Response("OK", 200)
