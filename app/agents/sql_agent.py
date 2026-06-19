import json
import logging

from app.agents.base_agent import BaseAgent
from app.database.connection import db
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah asisten database PostgreSQL yang ahli. Tugasmu:
1. Mengubah pertanyaan bahasa natural menjadi SQL query yang akurat
2. Menjelaskan hasil query dengan bahasa yang mudah dipahami
3. Memberikan insight dari data yang ditemukan

Bahasa: Gunakan bahasa Indonesia, kecuali untuk SQL query (tetap bahasa Inggris).

Aturan:
- Hanya gunakan fungsi execute_sql untuk query SELECT
- Selalu tambahkan LIMIT {max_rows} jika user tidak menyebutkan jumlahnya
- Jangan pernah menjalankan INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE
- Jika query error, coba perbaiki dan jalankan ulang
- Jelaskan hasilnya dalam bahasa Indonesia yang natural
""".format(max_rows=settings.max_rows)


class SQLAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=SYSTEM_PROMPT)

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql",
                    "description": "Jalankan SQL query SELECT ke database. Gunakan untuk menjawab pertanyaan user tentang data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query SELECT yang akan dijalankan",
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Penjelasan singkat tentang apa yang dilakukan query ini",
                            },
                        },
                        "required": ["query", "explanation"],
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
                return json.dumps({"error": f"Query {keyword} tidak diizinkan. Hanya SELECT yang diperbolehkan."})

        if not query_stripped.startswith("SELECT"):
            return json.dumps({"error": "Hanya query SELECT yang diperbolehkan."})

        try:
            results = await db.execute_query(query)
            return json.dumps({"results": results, "row_count": len(results)}, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})
