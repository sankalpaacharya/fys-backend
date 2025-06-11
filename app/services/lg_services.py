# LangGraph imports
from typing import List,Dict,Any
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
from typing_extensions import Annotated, TypedDict

# LangGraph State Definition
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    finance_data: str
    character: str
    
class ChatMemoryService:
    def __init__(self):
        # Initialize memory saver
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(State)
        
        # Add nodes
        workflow.add_node("process_query", self._process_query_node)
        workflow.add_node("generate_response", self._generate_response_node)
        
        # Add edges
        workflow.add_edge(START, "process_query")
        workflow.add_edge("process_query", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Compile with checkpointer for memory
        return workflow.compile(checkpointer=self.memory)
    
    async def _process_query_node(self, state: State) -> Dict[str, Any]:
        """Process the incoming query and prepare context"""
        human_message = HumanMessage(content=state["query"])
        return {
            "messages": [human_message],
            "query": state["query"],
            "finance_data": state["finance_data"],
            "character": state["character"]
        }
    
    async def _generate_response_node(self, state: State) -> Dict[str, Any]:
        """Generate AI response using LLM"""
        # This would be called by the main chat function
        # For now, we just prepare the state
        return state
    
# Global memory service instance
chat_memory_service = ChatMemoryService()