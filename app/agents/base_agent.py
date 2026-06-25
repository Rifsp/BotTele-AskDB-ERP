import json
import logging
import os
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_SCHEMA_PROMPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "ai_agent_readonly_schema_prompt_v2.md",
)

_schema_prompt_cache: dict[str, str] = {}


def _load_schema_prompt(path: str | None = None) -> str:
    path = path or DEFAULT_SCHEMA_PROMPT
    if path in _schema_prompt_cache:
        return _schema_prompt_cache[path]
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                content = f.read()
                _schema_prompt_cache[path] = content
                logger.info("Schema prompt loaded from %s", path)
                return content
    except Exception as e:
        logger.warning("Failed to load schema prompt: %s", e)
    _schema_prompt_cache[path] = ""
    return ""


def _message_to_dict(msg) -> dict:
    d = {"role": msg.role}
    if msg.content is not None:
        d["content"] = msg.content
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return d


class BaseAgent(ABC):
    def __init__(self, system_prompt: str, schema_prompt_path: str | None = None):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model
        schema = _load_schema_prompt(schema_prompt_path)
        self.system_prompt = (
            f"{system_prompt}\n\n---\n\n## DATABASE SCHEMA & BUSINESS RULES\n\n{schema}"
            if schema
            else system_prompt
        )

    @property
    @abstractmethod
    def tools(self) -> list[dict]:
        pass

    async def call_openai(self, messages: list[dict]):
        kwargs = dict(
            model=self.model,
            messages=messages,
        )
        if self.tools:
            kwargs["tools"] = self.tools
            kwargs["tool_choice"] = "auto"
            kwargs["parallel_tool_calls"] = False

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def build_context(
        self, context: list[dict] | None = None
    ) -> list[dict]:
        context = context or []
        return [m for m in context if m.get("role") != "system"]

    def build_messages(
        self, user_message: str, context: list[dict] | None = None
    ) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.build_context(context))
        messages.append({"role": "user", "content": user_message})
        return messages

    @abstractmethod
    async def handle_tool_call(self, tool_call) -> str:
        pass

    async def run(self, message: str, context: list[dict] | None = None) -> dict:
        messages = self.build_messages(message, context)
        sql_queries: list[str] = []

        for _ in range(5):
            ai_message = await self.call_openai(messages)

            if ai_message.tool_calls:
                messages.append(_message_to_dict(ai_message))
                for tool_call in ai_message.tool_calls:
                    logger.info("Tool called: %s", tool_call.function.name)
                    try:
                        args = json.loads(tool_call.function.arguments)
                        if "query" in args:
                            sql_queries.append(args["query"])
                    except Exception:
                        pass
                    result = await self.handle_tool_call(tool_call)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                continue

            response_text = ai_message.content or ""
            if response_text:
                saved_context = [m for m in messages if m.get("role") != "system"]
                return {
                    "response": response_text,
                    "context": saved_context[-6:],
                    "sql": sql_queries,
                }

        saved_context = [m for m in messages if m.get("role") != "system"]
        return {
            "response": "Data berhasil diambil. Silakan periksa hasil query di atas.",
            "context": saved_context[-6:],
            "sql": sql_queries,
        }
