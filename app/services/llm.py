import base64
from openai import AsyncOpenAI
from groq import AsyncGroq
from app.config.settings import settings
from typing import AsyncGenerator
from pydantic import BaseModel
from typing import Optional
from app.utils.prompt_utils import prompt_render
from app.services.supabase_service import get_finance,get_categories
from fastapi import UploadFile


class ChatContext(BaseModel):
    pass

class ChatPrompt(BaseModel):
    context: Optional[ChatContext] = None
    query: str
    character: str = "senku"
    categories:str
    filename: str = "chat_prompt.md"
    
class ImagePrompt(BaseModel):
    finance : str
    filename : str = "image_prompt.md"


def get_llm_client_and_model(provider: str):
    if provider == "openai":
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o-mini"
    elif provider == "groq":
        return AsyncGroq(api_key=settings.GROQ_API_KEY), "meta-llama/llama-4-scout-17b-16e-instruct"
    else:
        error_msg = f"Unsupported LLM provider: {provider}"
        raise ValueError(error_msg)


async def chat_with_stream(provider: str, query: str) -> AsyncGenerator[str, None]:
    client, model = get_llm_client_and_model(provider)
    category_list  = str(await get_categories())
    chat_prompt = prompt_render(prompt_obj=ChatPrompt(query=query,categories=str(category_list)))
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": chat_prompt}],
            stream=True,
        )
        stream_response = ""
        async for chunk in response:
            if hasattr(chunk.choices[0], "delta") and hasattr(
                chunk.choices[0].delta, "content"
            ):
                content = chunk.choices[0].delta.content
                if content:
                    stream_response += content
                    yield f"data: {content}\n\n"
    except Exception as e:
        raise


async def upload_snap_to_ai(image:UploadFile):
    client, model  = get_llm_client_and_model("groq")
    image_bytes = await image.read()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{image.content_type};base64,{encoded_image}"
    finance = str(await (get_categories()))
    image_prompt = prompt_render(ImagePrompt(finance=finance))
    try:
        response =await client.chat.completions.create(model=model, messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": image_prompt},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
            max_tokens=1000,)
        return response.choices[0].message.content
    except Exception as e:
        print(e)
    
