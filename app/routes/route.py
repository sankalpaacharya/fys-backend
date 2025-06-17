from fastapi import APIRouter, Form, File, UploadFile,HTTPException
from fastapi.responses import JSONResponse
from app.services.llm import chat_with_stream,upload_snap_to_ai
from app.core.models import ChatRequest
from fastapi.responses import StreamingResponse
from uuid import UUID
from app.core.models import ChatRequest
import json

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

@router.post("/upload-snap")
async def upload_image(user_id: str = Form(...), image: UploadFile = File(...)):
    if image.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    result = await upload_snap_to_ai(image=image) 
    result = json.loads(result)
    return JSONResponse(content=result)
    
