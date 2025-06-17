import asyncio
from typing import List, Annotated, TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from app.core.models import ChatRequest, ChatPrompt
from app.services.supabase_service import get_finance
from app.utils.prompt_utils import prompt_render
from openai import AsyncOpenAI
from groq import AsyncGroq
from app.config.settings import settings

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    finance_data: Dict[str, Any]
    provider: str
    model: str
    chat: ChatRequest
    system_prompt: str

def setup_provider(state: State):
    if state["provider"] == "openai":
        state['model'] = "gpt-4o"
    elif state["provider"] == "groq":
        state['model'] = "llama3-8b-8192"
    else:
        error_msg = f"Unsupported LLM provider: {state['provider']}"
        raise ValueError(error_msg)
    return state

async def get_finance_data(state: State):
    try: 
        finance_raw = await get_finance(state['chat'].user_id)
        state['finance_data'] = finance_raw if finance_raw else {}
        print(f"Finance data retrieved: {state['finance_data']}")
        return state
    except Exception as e:
        print(f"Error getting finance data: {e}")
        state['finance_data'] = {"error": "Could not retrieve finance data"}
        return state

def render_system_prompt(state: State):
    try:
        prompt_obj = ChatPrompt(
            query=state['chat'].query,
            finance_data=state['finance_data'],
        )
        state['system_prompt'] = prompt_render(prompt_obj)
        print(f"Rendered system prompt: {state['system_prompt'][:200]}...")  # Log first 200 chars
        return state
    except Exception as e:
        print(f"Error rendering prompt: {e}")
        return state

def prepare_messages(state: State):
    """Prepare messages with the rendered system prompt"""
    system_msg = SystemMessage(content=state['system_prompt'])
    user_msg = HumanMessage(content=state['chat'].query)
    
    messages = state['messages'].copy()
    messages.insert(0, system_msg)
    messages.append(user_msg)
    
    state['messages'] = messages
    return state

# async def answer_query(state: State):
#     provider = state['provider']
#     model = state['model']
    
#     messages_for_api = []
#     for msg in state['messages']:
#         if isinstance(msg, SystemMessage):
#             messages_for_api.append({"role": "system", "content": msg.content})
#         elif isinstance(msg, HumanMessage):
#             messages_for_api.append({"role": "user", "content": msg.content})
#         elif isinstance(msg, AIMessage):
#             messages_for_api.append({"role": "assistant", "content": msg.content})
    
#     try:
#         if provider == "openai":
#             async with AsyncOpenAI(api_key=settings.OPENAI_API_KEY) as client:
#                 response = await client.chat.completions.create(
#                     model=model,
#                     messages=messages_for_api,
#                     temperature=0.7,
#                     stream=True
#                 )
#                 ai_response = AIMessage(content=response.choices[0].message.content)
#                 state['messages'].append(ai_response)
#                 return state
#         elif provider == "groq":
#             async with AsyncGroq(api_key=settings.GROQ_API_KEY) as client:
#                 response = await client.chat.completions.create(
#                     model=model,
#                     messages=messages_for_api,
#                     temperature=0.7,
#                     stream=True
#                 )
#                 ai_response = AIMessage(content=response.choices[0].message.content)
#                 state['messages'].append(ai_response)
#                 return state
#         else:
#             raise ValueError(f"Unsupported LLM provider: {provider}")
#     except Exception as e:
#         print(f"Error generating response: {str(e)}")
#         return state
async def answer_query_streaming_collect(state: State):
    provider = state['provider']
    model = state['model']
    
    messages_for_api = []
    for msg in state['messages']:
        if isinstance(msg, SystemMessage):
            messages_for_api.append({"role": "system", "content": msg.content})
        elif isinstance(msg, HumanMessage):
            messages_for_api.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages_for_api.append({"role": "assistant", "content": msg.content})
    
    try:
        full_response = ""
        
        if provider == "openai":
            async with AsyncOpenAI(api_key=settings.OPENAI_API_KEY) as client:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages_for_api,
                    temperature=0.7,
                    stream=True
                )
                
                async for chunk in response:
                    if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                        content = chunk.choices[0].delta.content
                        if content:
                            full_response += content
                            
        elif provider == "groq":
            async with AsyncGroq(api_key=settings.GROQ_API_KEY) as client:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages_for_api,
                    temperature=0.7,
                    stream=True
                )
                
                async for chunk in response:
                    if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                        content = chunk.choices[0].delta.content
                        if content:
                            full_response += content
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        # Add the complete response to state
        ai_response = AIMessage(content=full_response)
        state['messages'].append(ai_response)
        return state
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        error_response = AIMessage(content=f"Error: {str(e)}")
        state['messages'].append(error_response)
        return state

graph = StateGraph(State)
graph.add_node("setup_provider", setup_provider)
graph.add_node("get_finance", get_finance_data)
graph.add_node("render_prompt", render_system_prompt)
graph.add_node("prepare_messages", prepare_messages)
graph.add_node("answer_query", answer_query_streaming_collect)

graph.add_edge(START, "setup_provider")
graph.add_edge("setup_provider", "get_finance")
graph.add_edge("get_finance", "render_prompt")
graph.add_edge("render_prompt", "prepare_messages")
graph.add_edge("prepare_messages", "answer_query")
graph.add_edge("answer_query", END)

agent = graph.compile()

# async def main():
#     result = await agent.ainvoke({
#         "messages": [],
#         "finance_data": {},
#         "provider": "groq",
#         "model": "",
#         "chat": ChatRequest(user_id="12345", query="What's my current financial status?"),
#         "system_prompt": ""
#     })
    
#     # Get the last AI message
#     ai_messages = [msg for msg in result['messages'] if isinstance(msg, AIMessage)]
#     if ai_messages:
#         print("AI Response:", ai_messages[-1].content)
#     else:
#         print("No AI response found")
    
#     return result

# if __name__ == "__main__":
#     result = asyncio.run(main())