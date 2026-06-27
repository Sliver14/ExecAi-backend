"""Core LangChain Agent for ExecAI with full Tool Calling."""

from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.agents.tools import ALL_TOOLS
from app.agents.prompts import INTENT_EXTRACTION_PROMPT
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("execai.agent")

class ExecAIAgent:
    def __init__(self):
        # Configure ChatOpenAI with retry logic on LLM failures
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,  # Lower for more deterministic actions
            api_key=settings.OPENAI_API_KEY,
            max_retries=3,
        )
        
        self.tools = ALL_TOOLS
        
        # Correctly import MessagesPlaceholder and define modern chat prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are ExecAI, a professional AI executive assistant.\n\n"
                    "Be concise.\n"
                    "Always use tools whenever appropriate.\n"
                    "Always use the supplied user_id when invoking tools.\n"
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True,
            handle_parsing_errors=True,
        )

    async def process_message(self, message: str, user_context: Dict[str, Any], 
                            user_id: UUID, conversation_history: List = None) -> Dict[str, Any]:
        """Process message with full tool calling support."""
        if conversation_history is None:
            conversation_history = []
        
        # Prepare user id as context string
        context_str = json.dumps(user_context, default=str)
        
        # Format input data
        input_data = {
            "input": f"User context: {context_str}\nUser ID: {user_id}\n\nMessage: {message}",
            "chat_history": conversation_history
        }
        
        try:
            # Run agent with tools
            result = await self.agent_executor.ainvoke(input_data)
            final_output = result.get("output", str(result))
            
            return {
                "response": final_output,
                "action_taken": "tool" in str(result).lower() or "created" in final_output.lower(),
                "raw_result": result
            }
            
        except Exception as e:
            logger.error(f"Error in AgentExecutor: {e}. Attempting fallback structure extraction.", exc_info=True)
            try:
                # Fallback to structured extraction if tool calling fails
                fallback = await self._fallback_structured(message, user_context, conversation_history)
                return {
                    "response": fallback.get("response", "Sorry, I encountered an issue. Please try again."),
                    "action_taken": False,
                    "error": str(e)
                }
            except Exception as fe:
                logger.error(f"Fallback extraction failed: {fe}", exc_info=True)
                return {
                    "response": "I encountered an error while trying to process your request. Please try again later.",
                    "action_taken": False,
                    "error": f"Original: {e}, Fallback: {fe}"
                }

    async def _fallback_structured(self, message: str, user_context: Dict, history: List) -> Dict:
        """Fallback method using structured output."""
        chain = INTENT_EXTRACTION_PROMPT | self.llm.with_structured_output({
            "name": "IntentExtraction",
            "description": "Extraction of intent and professional response.",
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