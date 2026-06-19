import json
import logging

from app.agents.base_agent import BaseAgent
from app.database.connection import db

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah asisten yang ahli dalam membuat laporan terstruktur dari data database.
Tugasmu:
1. Membuat laporan ringkas dan informatif dari data
2. Menyajikan data dalam format yang mudah dibaca
3. Memberikan insight dan rekomendasi berdasarkan data
4. Membuat ringkasan eksekutif

Gunakan bahasa Indonesia. Format laporan rapi dengan bullet points atau tabel."""


class ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=SYSTEM_PROMPT)

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql",
                    "description": "Jalankan SQL query untuk mengumpulkan data laporan",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query SELECT untuk data laporan",
                            },
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

    async def handle_tool_call(self, tool_call) -> str:
        args = json.loads(tool_call.function.arguments)
        query = args["query"]
        return await self._validate_and_execute(query)

    async def _validate_and_execute(self, query: str) -> str:
        query_stripped = query.strip().upper()
        forbidden = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
            "CREATE", "TRUNCATE", "GRANT", "REVOKE",
        ]
        for keyword in forbidden:
            if query_stripped.startswith(keyword):
                return json.dumps({"error": f"Query {keyword} tidak diizinkan."})

        if not query_stripped.startswith("SELECT"):
            return json.dumps({"error": "Hanya SELECT diperbolehkan."})

        try:
            results = await db.execute_query(query)
            return json.dumps({"results": results, "row_count": len(results)}, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})
