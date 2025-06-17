from app.services.lg_service import agent
from app.core.models import ChatRequest
from langchain_core.messages import AIMessage

async def chat_with_stream(user_id: str, query: str, provider: str = "groq"):
    """
    Function to chat with the LLM using streaming.
    """
    try:
        chat_request = ChatRequest(user_id=user_id, query=query)
        result = await agent.ainvoke({
            "messages": [],
            "provider": provider,
            "chat": chat_request,
            "system_prompt": "",
        })
        ai_response = [msg for msg in result['messages'] if isinstance(msg, AIMessage)]
        if ai_response:
            yield ai_response[-1].content
        else:
            yield "No response from AI."
    except Exception as e:
        raise
    
                
    