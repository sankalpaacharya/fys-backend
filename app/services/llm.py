from openai import AsyncOpenAI
from groq import AsyncGroq
from app.config.settings import settings
from typing import AsyncGenerator
from pydantic import BaseModel
from typing import Optional
from app.utils.prompt_utils import prompt_render
from app.services.supabase_service import get_finance

class ChatContext(BaseModel):
    pass

class ChatPrompt(BaseModel):
    context: Optional[ChatContext] = None
    query: str
    character: str = "senku"
    finance_data:str
    filename: str = "chat_prompt.md"


def get_llm_client_and_model(provider: str):
    if provider == "openai":
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o"
    elif provider == "groq":
        return AsyncGroq(api_key=settings.GROQ_API_KEY), "llama3-8b-8192"
    else:
        error_msg = f"Unsupported LLM provider: {provider}"
        raise ValueError(error_msg)

async def chat_with_stream(provider: str, query: str) -> AsyncGenerator[str, None]:
    client, model = get_llm_client_and_model(provider)
    finance_data  = await get_finance()
    print(finance_data)
    chat_prompt = prompt_render(prompt_obj=ChatPrompt(query=query,finance_data=str(finance_data["data"])))
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
