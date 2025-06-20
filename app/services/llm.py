from openai import AsyncOpenAI
from groq import AsyncGroq
from app.config.settings import settings
from typing import AsyncGenerator
from pydantic import BaseModel
from typing import Optional
from app.utils.prompt_utils import prompt_render
from app.services.supabase_service import get_finance,store_finance,get_categories
import json
import base64
from fastapi import UploadFile

class ChatContext(BaseModel):
    pass

class ChatPrompt(BaseModel):
    context: Optional[ChatContext] = None
    query: str
    character: str = "senku"
    finance_data:str
    filename: str = "chat_prompt.md"
    
class ImagePrompt(BaseModel):
    finance : str
    filename : str = "image_prompt.md"
    
FINANCE_TOOLS = [
    {
    "type":"function",
    "function" : {
        "name":"store_finance",
        "description":"Store data from LLM to supabase",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Data to be stored in supabase"
                }
            },
            "required": ["data"]
        },
    },
    }
]

def get_llm_client_and_model(provider: str):
    if provider == "openai":
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o"
    elif provider == "groq":
        return AsyncGroq(api_key=settings.GROQ_API_KEY), "llama-3.3-70b-versatile"
    else:
        error_msg = f"Unsupported LLM provider: {provider}"
        raise ValueError(error_msg)

async def chat_with_stream(provider: str, query: str) -> AsyncGenerator[str, None]:
    client, model = get_llm_client_and_model(provider)
    finance_data  = await get_finance()
    chat_prompt = prompt_render(prompt_obj=ChatPrompt(query=query,finance_data=str(finance_data)))
    messages = [{"role":"system","content":chat_prompt},{"role": "user", "content": query}]
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=FINANCE_TOOLS,
            tool_choice="auto",
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        if tool_calls:
            available_function = {
                "store_finance": store_finance
            }
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_function.get(function_name)
                function_args = json.loads(tool_call.function.arguments)
                function_response = await function_to_call(
                    data=function_args.get("data", "")
                )
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role":"tool",
                        "name":function_name,
                        "content":function_response['response']
                    }
                )
            final_response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            streamed_response = ""
            async for chunk in final_response:
                if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                    content = chunk.choices[0].delta.content
                    if content:
                        streamed_response += content
                        yield f"data: {content}\n\n"
            print(streamed_response)
        else:
            # No tool calls, stream the regular response
            if response_message.content:
                # Split the content into chunks for streaming effect
                content = response_message.content
                words = content.split()
                for i, word in enumerate(words):
                    if i == 0:
                        yield f"data: {word}\n\n"
                    else:
                        yield f"data:  {word}\n\n"
        print("Final response:", response_message.content)
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