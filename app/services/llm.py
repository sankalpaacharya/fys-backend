from openai import AsyncOpenAI
from groq import AsyncGroq
from app.config.settings import settings
from typing import AsyncGenerator
from pydantic import BaseModel
from typing import Optional,List,Dict
from app.utils.prompt_utils import prompt_render
from app.services.supabase_service import get_finance
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from app.services.lg_services import chat_memory_service

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
    
async def chat_with_stream_langgraph(
    provider: str, 
    query: str, 
    session_id: Optional[str] = None,
    character: str = "senku"
) -> AsyncGenerator[str, None]:
    """
    Enhanced chat function with memory support
    
    Args:
        provider: LLM provider ("openai" or "groq")
        query: User query
        session_id: Session ID for memory persistence (generates one if not provided)
        character: Character name for context
    """
    client, model = get_llm_client_and_model(provider)
    finance_data = await get_finance()
    
    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())
    print(session_id)
    # Create thread config for memory
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        # Prepare initial state
        initial_state = {
            "messages": [],
            "query": query,
            "finance_data": str(finance_data["data"]),
            "character": character
        }
        
        # Process through LangGraph (this updates memory)
        result = await chat_memory_service.graph.ainvoke(initial_state, config)
        
        # Get conversation history from memory
        conversation_history = []
        graph_state = chat_memory_service.graph.get_state(config)
        if graph_state and graph_state.values.get("messages"):
            conversation_history = graph_state.values["messages"]
        
        # Build messages for LLM including history
        messages = []
        
        # Add conversation history (limit to last 10 messages to avoid token limits)
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        for msg in recent_history:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        # Create prompt with current query and context
        chat_prompt = prompt_render(
            prompt_obj=ChatPrompt(
                query=query, 
                finance_data=str(finance_data["data"]),
            )
        )
        
        # Add current query if not already in history
        if not messages or messages[-1]["content"] != chat_prompt:
            messages.append({"role": "user", "content": chat_prompt})
        
        # Generate streaming response
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
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
        print(stream_response)
        # Save AI response to memory
        if stream_response:
            ai_message = AIMessage(content=stream_response)
            # Update state with AI response
            update_state = {
                "messages": [ai_message]
            }
            await chat_memory_service.graph.ainvoke(update_state, config)
            
    except Exception as e:
        raise

async def get_conversation_history(session_id: str) -> List[Dict[str, str]]:
    """
    Retrieve conversation history for a session
    
    Args:
        session_id: Session ID to retrieve history for
        
    Returns:
        List of messages in the conversation
    """
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        graph_state = chat_memory_service.graph.get_state(config)
        if not graph_state or not graph_state.values.get("messages"):
            return []
        
        history = []
        for msg in graph_state.values["messages"]:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history
    except Exception as e:
        print(f"Error retrieving conversation history: {e}")
        return []
    
async def clear_conversation_history(session_id: str) -> bool:
    """
    Clear conversation history for a session
    
    Args:
        session_id: Session ID to clear history for
        
    Returns:
        True if successful, False otherwise
    """
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        # Clear the memory for this session
        # Note: MemorySaver doesn't have a direct clear method, 
        # so we'll reset by creating a new empty state
        empty_state = {
            "messages": [],
            "query": "",
            "finance_data": "",
            "character": "senku"
        }
        await chat_memory_service.graph.ainvoke(empty_state, config)
        return True
    except Exception as e:
        print(f"Error clearing conversation history: {e}")
        return False