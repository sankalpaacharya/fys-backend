from fastapi import APIRouter, HTTPException
from app.services.llm import chat_with_stream, chat_with_stream_langgraph, get_conversation_history, clear_conversation_history
from app.core.models import ChatRequest
from fastapi.responses import StreamingResponse
from app.core.models import ChatRequest, ConversationHistoryResponse, ClearHistoryResponse

router = APIRouter(tags=["Chat"])

@router.post("/chat-stream")
async def chat_stream(body: ChatRequest):
    try:
        return StreamingResponse(
            chat_with_stream(provider="groq", query=body.query),
            media_type="text/event-stream"
        )
    except Exception as e:
        return str(e)
    
@router.post("/chat-stream-langgraph")
async def chat_stream_langgraph(body: ChatRequest):
    """
    Stream chat responses with memory support
    """
    try:
        # Extract session_id and character from the request if available
        session_id = getattr(body, 'session_id', None)
        character = getattr(body, 'character', 'senku')
        
        return StreamingResponse(
            chat_with_stream_langgraph(
                provider="groq", 
                query=body.query,
                session_id=session_id,
                character=character
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/conversation-history/{session_id}")
async def get_chat_history(session_id: str) -> ConversationHistoryResponse:
    """
    Get conversation history for a specific session
    """
    try:
        messages = await get_conversation_history(session_id)
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=messages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")

@router.delete("/conversation-history/{session_id}")
async def clear_chat_history(session_id: str) -> ClearHistoryResponse:
    """
    Clear conversation history for a specific session
    """
    try:
        success = await clear_conversation_history(session_id)
        return ClearHistoryResponse(
            session_id=session_id,
            cleared=success,
            message="Conversation history cleared successfully" if success else "Failed to clear conversation history"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation history: {str(e)}")