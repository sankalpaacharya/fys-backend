from fastapi import APIRouter,Form,UploadFile,HTTPException,File
from app.services.llm import chat_with_stream
from app.core.models import ChatRequest
from fastapi.responses import StreamingResponse,JSONResponse
from uuid import UUID
from app.core.models import ChatRequest
import json
from app.services.llm import upload_snap_to_ai

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