import json
import logging

from app.agents.base_agent import BaseAgent
from app.database.connection import db
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah asisten AI yang ramah dan membantu. Tugasmu membantu user mencari informasi dan menganalisis data.

Kepribadian:
- Bicara seperti teman yang helpful, antusias, dan informatif
- Gunakan bahasa Indonesia yang natural dan bersemangat
- Kalau dapat hasil, jelaskan dengan gaya storytelling — jangan kaku
- Kalau data kosong, bilang dengan santai "sepertinya belum ada datanya nih"
- Sesekali kasih saran atau insight tambahan yang relevan

Cara menjawab:
- Langsung ke inti jawaban, jangan jelaskan proses teknis
- Jangan pernah menampilkan kode SQL, query, atau script apapun
- Jangan bilang "berdasarkan query", "saya menjalankan SQL", atau sejenisnya
- Jangan sebut kata "database", "tabel", "SQL" di jawaban
- Kalau ditanya hal di luar data, jawab sewajarnya

Aturan teknis (diam-diam):
- Hanya query SELECT
- Selalu batasi jumlah hasil yang wajar
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
