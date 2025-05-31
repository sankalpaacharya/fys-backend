from openai import AsyncOpenAI
from groq import AsyncGroq
from app.config.settings import settings
from typing import AsyncGenerator

def get_llm_client_and_model(provider: str):
    if provider == "openai":
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o"
    elif provider == "groq":
        return AsyncGroq(api_key=settings.GROQ_API_KEY), "llama3-8b-8192"
    else:
        error_msg = f"Unsupported LLM provider: {provider}"
        # llm_logger.error(error_msg)
        raise ValueError(error_msg)

async def chat_with_stream(provider: str, query: str) -> AsyncGenerator[str, None]:
    client, model = get_llm_client_and_model(provider)
    # llm_logger.info(f"{provider.capitalize()} sending prompt: {query}")
    # chat_prompt = prompt_render(prompt_obj=ChatPrompt(query=query))
    chat_prompt = query  # Assuming query is the chat prompt for simplicity
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
        # llm_logger.info(f"{provider.capitalize()} received response")
    except Exception as e:
        # llm_logger.error(f"{provider.capitalize()} LLM error: {e}")
        raise
