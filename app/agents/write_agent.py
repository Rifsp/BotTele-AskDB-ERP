import json
import logging
import os

from app.agents.base_agent import BaseAgent
from app.database.connection import db_admin as db
from app.config import settings

logger = logging.getLogger(__name__)

WRITE_SCHEMA_PROMPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "ai_agent_schema_prompt_v2.md",
)

SYSTEM_PROMPT = """Kamu adalah asisten database operasional. Tugasmu membantu operator menganalisis dan merevisi data ERP.

Kamu bisa:
1. Membaca data (SELECT) untuk verifikasi
2. Membuat perubahan data (INSERT, UPDATE, DELETE) yang diminta user
3. Mengecek trigger, constraint, dan FK sebelum mengubah data

Aturan:
- SELALU backup data dulu sebelum UPDATE/DELETE: backup pakai SELECT ke tx_backup_*
- Jangan pernah DROP, ALTER, CREATE, TRUNCATE tabel
- Jangan pernah GRANT/REVOKE
- Gunakan f_*_cancel = true untuk soft-delete, jangan DELETE baris transaksi langsung
- Kalau ragu, tanyakan konfirmasi ke user sebelum eksekusi
- Jika query error, coba perbaiki dan jalankan ulang
- Jelaskan apa yang diubah dan efek sampingnya (trigger yang akan jalan)

Bahasa: Indonesia."""


class WriteAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=SYSTEM_PROMPT,
            schema_prompt_path=WRITE_SCHEMA_PROMPT,
        )

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql",
                    "description": "Jalankan SQL query (SELECT/INSERT/UPDATE/DELETE). Backup dulu sebelum perubahan data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query yang akan dijalankan",
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
        query_upper = query.strip().upper()

        forbidden = ["DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]
        for keyword in forbidden:
            if query_upper.startswith(keyword):
                return json.dumps({"error": f"Query {keyword} tidak diizinkan."})

        try:
            if query_upper.startswith("SELECT"):
                results = await db.execute_query(query)
                return json.dumps({"results": results, "row_count": len(results)}, default=str)
            else:
                await db.execute_query(query)
                return json.dumps({"status": "success", "message": "Query berhasil dijalankan."})
        except Exception as e:
            return json.dumps({"error": str(e)})
