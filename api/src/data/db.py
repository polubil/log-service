from datetime import datetime
import asyncpg

from src.data.models import Log


class DB:

    def __init__(self, url: str):
        self.url = url

    async def connect(self):
        self.pool: asyncpg.Pool = await asyncpg.pool.create_pool(self.url)

    async def disconnect(self):
        await self.pool.close()

    async def create_tables(self):
        async with self.pool.acquire() as p:
            await p.execute(
                """
                CREATE TABLE IF NOT EXISTS logs(
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    ip inet,
                    method VARCHAR(7),
                    uri VARCHAR(512),
                    status_code INTEGER CHECK (status_code BETWEEN 100 AND 599),
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await p.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_created_id ON logs (created, id)"
            )

    async def insert(self, log: Log):
        query = (
            "INSERT INTO logs (ip, method, uri, status_code) VALUES ($1, $2, $3, $4)"
        )
        async with self.pool.acquire() as p:
            await p.execute(query, log.ip, log.method, log.uri, log.status_code)

    async def fetch(
        self,
        method: list[str],
        status_code: list[int],
        lt: datetime,
        gt: datetime,
        limit: int,
        offset: int,
    ):

        query = "SELECT * FROM logs WHERE 1=1"
        params = []
        if method:
            params.append([m.value for m in method])
            query += f" AND method = ANY(${len(params)}::text[])"

        if status_code:
            params.append(status_code)
            query += f" AND status_code = ANY(${len(params)}::int[])"

        if lt is not None:
            params.append(lt)
            query += f" AND created < ${len(params)}"

        if gt is not None:
            params.append(gt)
            query += f" AND created > ${len(params)}"

        params.append(limit)
        query += f" LIMIT ${len(params)}"

        params.append(offset)
        query += f" OFFSET ${len(params)}"
        print(query)
        async with self.pool.acquire() as p:
            logs = await p.fetch(query, *params)
            return [Log(**log) for log in logs]

    async def get_stats(self, agg_by, lt, gt):

        query = f"SELECT {agg_by}, COUNT(*) FROM logs WHERE 1=1"

        params = []
        if lt is not None:
            params.append(lt)
            query += f" AND created < ${len(params)}"

        if gt is not None:
            params.append(gt)
            query += f" AND created > ${len(params)}"

        query += f" GROUP BY {agg_by} ORDER BY COUNT(*) DESC"
        print(query)

        async with self.pool.acquire() as p:
            res = await p.fetch(query, *params)
            return dict(res)
