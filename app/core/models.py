from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # For memory persistence
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's my current balance?",
                "session_id": "user_123_session",
            }
        }
    
# Response models for the new endpoints
class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, str]]

class ClearHistoryResponse(BaseModel):
    session_id: str
    cleared: bool
    message: str