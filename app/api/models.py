from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    context: list[dict] | None = None


class ChatResponse(BaseModel):
    response: str
    context: list[dict]


class SchemaResponse(BaseModel):
    tables: list
