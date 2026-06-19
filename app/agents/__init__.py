from app.agents.sql_agent import SQLAgent
from app.agents.schema_agent import SchemaAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.report_agent import ReportAgent
from app.agents.chat_agent import ChatAgent

_sql_agent = SQLAgent()
_schema_agent = SchemaAgent()
_analysis_agent = AnalysisAgent()
_report_agent = ReportAgent()
_chat_agent = ChatAgent()

INTENT_KEYWORDS = {
    "schema": ["skema", "struktur", "tabel", "kolom", "relasi", "index", "foreign key", "schema", "table", "column"],
    "analysis": ["analisis", "analisa", "anomali", "outlier", "pola", "tren", "trend", "pattern", "aggregate"],
    "report": ["laporan", "report", "ringkasan", "rangkuman", "summary", "buatkan laporan"],
}


def detect_intent(message: str) -> str:
    msg_lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                return intent
    return "chat"


async def route_message(message: str, context: list[dict] | None = None) -> dict:
    intent = detect_intent(message)

    if intent == "schema":
        return await _schema_agent.run(message, context)
    elif intent == "analysis":
        return await _analysis_agent.run(message, context)
    elif intent == "report":
        return await _report_agent.run(message, context)
    else:
        return await _chat_agent.run(message, context)
