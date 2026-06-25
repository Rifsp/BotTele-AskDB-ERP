import asyncpg
from app.config import settings


class DatabasePool:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def create_pool(self, dsn: str | None = None):
        self.pool = await asyncpg.create_pool(
            dsn=dsn or settings.database_url,
            min_size=2,
            max_size=10,
            command_timeout=settings.query_timeout,
        )

    async def close_pool(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute_query(self, query: str, params: list | None = None) -> list[dict]:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.pool.acquire() as conn:
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)

            return [dict(row) for row in rows]


db = DatabasePool()
