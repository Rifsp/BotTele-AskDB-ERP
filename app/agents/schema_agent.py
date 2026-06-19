import json
import logging

from app.agents.base_agent import BaseAgent
from app.database import schema

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah asisten analis database yang ahli dalam memahami struktur database.
Tugasmu:
1. Menganalisis skema database: tabel, kolom, tipe data, relasi, indexing
2. Menjelaskan hubungan antar tabel (foreign keys)
3. Memberikan rekomendasi optimasi skema
4. Menjelaskan arti setiap kolom dan tabel

Gunakan bahasa Indonesia dalam menjelaskan."""


class SchemaAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=SYSTEM_PROMPT)

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_schema_overview",
                    "description": "Dapatkan daftar semua tabel dalam database",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_details",
                    "description": "Dapatkan detail kolom, foreign keys, dan indexes dari sebuah tabel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_schema": {
                                "type": "string",
                                "description": "Schema database (default: public)",
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Nama tabel",
                            },
                        },
                        "required": ["table_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_full_schema",
                    "description": "Dapatkan skema lengkap database (semua tabel, kolom, relasi, indexes)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ]

    async def handle_tool_call(self, tool_call) -> str:
        args = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "get_schema_overview":
            tables = await schema.get_tables()
            return json.dumps(tables, default=str)

        elif tool_call.function.name == "get_table_details":
            table_schema = args.get("table_schema", "public")
            table_name = args["table_name"]
            columns = await schema.get_columns(table_schema, table_name)
            fks = await schema.get_foreign_keys(table_schema, table_name)
            indexes = await schema.get_indexes(table_schema, table_name)
            return json.dumps({
                "columns": columns,
                "foreign_keys": fks,
                "indexes": indexes,
            }, default=str)

        elif tool_call.function.name == "get_full_schema":
            full = await schema.get_full_schema()
            return json.dumps(full, default=str)

        return json.dumps({"error": "Unknown function"})
