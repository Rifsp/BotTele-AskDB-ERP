import logging

from fastapi import APIRouter, HTTPException

from app.api.models import ChatRequest, ChatResponse
from app.agents import route_message
from app.database.schema import get_full_schema
from app.database.connection import db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = await route_message(request.message, request.context)
        return ChatResponse(**result)
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/schema")
async def schema():
    try:
        return await get_full_schema()
    except Exception as e:
        logger.exception("Schema error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/health")
async def health():
    db_ok = db.pool is not None and hasattr(db.pool, "_closed") and not db.pool._closed
    return {"status": "ok", "database": db_ok}
