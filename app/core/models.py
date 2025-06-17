from typing import Any,Dict
from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str
    query : str
    
class ChatPrompt(BaseModel):
    filename:str = "chat_prompt.md"
    finance_data : Dict[str, Any]
    query : str
