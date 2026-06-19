import json
import logging
import os
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SCHEMA_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "ai_agent_readonly_schema_prompt.md",
)

_schema_prompt_cache: str | None = None


def _load_schema_prompt() -> str:
    global _schema_prompt_cache
    if _schema_prompt_cache is not None:
        return _schema_prompt_cache
    try:
        if os.path.exists(SCHEMA_PROMPT_PATH):
            with open(SCHEMA_PROMPT_PATH, encoding="utf-8") as f:
                _schema_prompt_cache = f.read()
                logger.info("Schema prompt loaded from %s", SCHEMA_PROMPT_PATH)
                return _schema_prompt_cache
    except Exception as e:
        logger.warning("Failed to load schema prompt: %s", e)
    _schema_prompt_cache = ""
    return _schema_prompt_cache


def _message_to_dict(msg) -> dict:
    d = {"role": msg.role, "content": msg.content}
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
    def __init__(self, system_prompt: str):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model
        schema = _load_schema_prompt()
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

        for _ in range(5):
            ai_message = await self.call_openai(messages)

            if ai_message.tool_calls:
                messages.append(_message_to_dict(ai_message))
                for tool_call in ai_message.tool_calls:
                    logger.info("Tool called: %s", tool_call.function.name)
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
                return {"response": response_text, "context": saved_context[-6:]}

        saved_context = [m for m in messages if m.get("role") != "system"]
        return {"response": "Data berhasil diambil. Silakan periksa hasil query di atas.", "context": saved_context[-6:]}
