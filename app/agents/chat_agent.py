import json
import logging

from app.agents.base_agent import BaseAgent
from app.database.connection import db
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah asisten database yang ramah dan membantu. Kamu bisa:
1. Menjawab pertanyaan tentang data dalam database
2. Mengingat konteks percakapan sebelumnya
3. Membantu user mengeksplorasi database
4. Menjelaskan hasil query dengan bahasa yang mudah

Gunakan bahasa Indonesia. Jika user bertanya di luar konteks database, arahkan kembali ke topik database.

Aturan:
- Hanya jalankan query SELECT
- Selalu tambahkan LIMIT jika perlu
- Jangan pernah menjalankan query berbahaya (INSERT, UPDATE, DELETE, DROP, dll)
""".format(max_rows=settings.max_rows)


class ChatAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=SYSTEM_PROMPT)

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql",
                    "description": "Jalankan SQL query SELECT ke database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query SELECT yang akan dijalankan",
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
