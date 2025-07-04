from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    query: str
    
class ChatContext(BaseModel):
    pass

class ChatPrompt(BaseModel):
    context: Optional[ChatContext] = None
    query: str
    character: str = "senku"
    finance_data: str
    filename: str = "chat_prompt.md"
    
class ImagePrompt(BaseModel):
    categories : str
    user_data : str
    filename : str = "image_prompt.md"
    
class NotificationPrompt(BaseModel):
    finance : str
    filename : str = "notification_prompt.md"