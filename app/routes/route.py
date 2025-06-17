from fastapi import APIRouter
from app.services.llm import chat_with_stream
from app.core.models import ChatRequest
from fastapi.responses import StreamingResponse

router = APIRouter(tags=['chat'])

@router.post("/chat-stream")
async def chat_stream(body:ChatRequest):
    try:
        return StreamingResponse(
            chat_with_stream(user_id=body.user_id, query=body.query, provider="groq"),
            media_type="text/event-stream"
        )
    except Exception as e:
        return str(e)