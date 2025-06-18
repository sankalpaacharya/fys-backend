from app.services.lg_service import agent, answer_query_streaming_collect
from app.core.models import ChatRequest

async def chat_with_stream(user_id: str, query: str, provider: str = "groq"):
    """
    Function to chat with the LLM using streaming.
    """
    try:
        chat_request = ChatRequest(user_id=user_id, query=query)
        # Run the graph up to just before the answer_query node
        state = await agent.ainvoke({  # Use apreivew or similar if available, or manually run steps
            "messages": [],
            "provider": provider,
            "chat": chat_request,
            "system_prompt": "",
        }, until="prepare_messages")
        # Now stream the answer
        async for chunk in answer_query_streaming_collect(state):
            yield chunk
    except Exception as e:
        yield f"Error: {str(e)}"


