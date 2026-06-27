"""Core LangChain Agent for ExecAI with full Tool Calling."""

from typing import Dict, Any, List, Optional
from uuid import UUID
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain_core.prompts import ChatPromptTemplate
from app.agents.tools import ALL_TOOLS
from app.agents.prompts import INTENT_EXTRACTION_PROMPT
from app.core.config import get_settings

settings = get_settings()

class ExecAIAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,  # Lower for more deterministic actions
            api_key=settings.OPENAI_API_KEY
        )
        

        
        # Tool calling agent setup
        self.tools = ALL_TOOLS
self.prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are ExecAI, a professional AI executive assistant.

Be concise.
Always use tools whenever appropriate.
Always use the supplied user_id when invoking tools.
""",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def process_message(self, message: str, user_context: Dict[str, Any], 
                            user_id: UUID, conversation_history: List = None) -> Dict[str, Any]:
        """Process message with full tool calling support."""
        if conversation_history is None:
            conversation_history = []
        
        # Add user context to system
        context_str = json.dumps(user_context, default=str)
        
        # Prepare input
        input_data = {
            "input": f"User context: {context_str}\n\nMessage: {message}",
            "chat_history": conversation_history
        }
        
        try:
            # Run agent with tools
            result = await self.agent_executor.ainvoke(input_data)
            
            # Extract final output
            final_output = result.get("output", str(result))
            
            return {
                "response": final_output,
                "action_taken": "tool" in str(result).lower() or "created" in final_output.lower(),
                "raw_result": result
            }
            
        except Exception as e:
            # Fallback to structured extraction if tool calling fails
            fallback = await self._fallback_structured(message, user_context, conversation_history)
            return {
                "response": fallback.get("response", "Sorry, I encountered an issue. Please try again."),
                "action_taken": False,
                "error": str(e)
            }

    async def _fallback_structured(self, message: str, user_context: Dict, history: List) -> Dict:
        """Fallback method using structured output."""
        chain = INTENT_EXTRACTION_PROMPT | self.llm.with_structured_output({
            "title": "IntentExtraction",
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "entities": {"type": "object"},
                "confidence": {"type": "string"},
                "response": {"type": "string"}
            },
            "required": ["intent", "entities", "confidence", "response"]
        })
        
        result = await chain.ainvoke({
            "input": message,
            "user_context": json.dumps(user_context, default=str),
            "history": history
        })
        return result