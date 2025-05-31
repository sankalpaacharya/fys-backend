from fastapi import APIRouter
from app.services.llm import chat_with_stream
from app.core.models import ChatRequest
from fastapi.responses import StreamingResponse
from uuid import UUID
from app.core.models import ChatRequest

router = APIRouter(tags=["Chat"])

@router.post("/chat-stream")
async def chat_stream(body: ChatRequest):
    try:
        return StreamingResponse(
            chat_with_stream(provider="groq", query=body.query),
        )
    except Exception as e:
        return str(e)