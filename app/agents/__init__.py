from app.agents.chat_agent import ChatAgent

_chat_agent = ChatAgent()


async def route_message(
    message: str,
    context: list[dict] | None = None,
    user_id: int = 0,
) -> dict:
    return await _chat_agent.run(message, context)
