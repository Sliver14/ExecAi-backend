"""Core LangChain Agent for ExecAI with full Tool Calling."""

from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import logging
from datetime import datetime
import pytz
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
from app.db.base import SessionLocal
from app.models.conversation import ConversationHistory

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
        
        # Enforce strict guidelines preventing delete intents from triggering task/event creates
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are ExecAI, a professional AI executive assistant.\n\n"
                    "CRITICAL ROUTING RULES:\n"
                    "1. When the user requests a deletion (e.g. 'delete', 'remove', 'cancel', 'erase') of a task or event, "
                    "you MUST invoke delete_task_tool or delete_event_tool. Never call create_task_tool or create_event_tool "
                    "for deletion intents.\n"
                    "2. Always verify Google Calendar connection status via google_auth_status_tool before creating events. "
                    "If disconnected, prompt user to authorize.\n"
                    "3. For destructive or irreversible operations (e.g. deleting tasks/events, disconnecting calendar, clear/reset memory), "
                    "you must output a confirmation request format: '[CONFIRMATION_REQUIRED] Action: <action_description>'. "
                    "Do NOT call the delete/destructive tools until the user has confirmed with a 'yes' or positive assertion.\n"
                    "4. Always use the supplied user_id and current local time when parsing relative terms.\n"
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

    def _get_local_greeting_and_date(self, user_context: Dict[str, Any], user_id: UUID) -> str:
        """
        Determines timezone and constructs custom welcoming prompts.
        Checks if this is the first interaction of the user's local calendar day.
        """
        from app.models.user import User
        
        tz_name = user_context.get("timezone", "UTC") or "UTC"
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.utc
            
        now_local = datetime.now(tz)
        local_date_str = now_local.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Look up conversation history for the user
        is_first_today = True
        with SessionLocal() as db:
            from datetime import timezone as dt_timezone
            today_start_utc = datetime.now(dt_timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            hist = db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.created_at >= today_start_utc
            ).first()
            if hist:
                is_first_today = False

                
        greeting = ""
        if is_first_today:
            greeting = f"Welcome back! Starting your day on {now_local.strftime('%A, %B %d')}. How can I assist you today?"
        else:
            # Casual warm continuation prompt
            greeting = "Ready to continue where we left off? Let me know what you need next."
            
        return f"Current authoritative local date/time: {local_date_str}.\nConversational greeting advice: {greeting}"

    async def process_message(self, message: str, user_context: Dict[str, Any], 
                            user_id: UUID, conversation_history: List = None) -> Dict[str, Any]:
        """Process message with full tool calling support, local day greetings, and timezone safety."""
        if conversation_history is None:
            conversation_history = []
        
        # Record user message in DB
        with SessionLocal() as db:
            user_msg = ConversationHistory(
                user_id=user_id,
                message_text=message,
                is_from_user=True
            )
            db.add(user_msg)
            db.commit()

        # Handle Confirmation Workflow
        # If user is confirming a pending destructive action
        is_confirmation = False
        lower_msg = message.strip().lower()
        
        # Simple confirmation hook
        # Check if the last assistant message requested confirmation and user answered affirmatively
        last_assistant_msg = ""
        for msg in reversed(conversation_history):
            if isinstance(msg, AIMessage):
                last_assistant_msg = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                last_assistant_msg = msg.get("content", "")
                break
                
        if "[confirmation_required]" in last_assistant_msg.lower() and lower_msg in ["yes", "y", "confirm", "do it", "sure"]:
            # User confirmed the destructive action! Let the agent run standard tool execution now.
            message = f"I confirm the following destructive action. Proceed with: {last_assistant_msg}"
            is_confirmation = True

        # Generate local details info prefix
        local_meta = self._get_local_greeting_and_date(user_context, user_id)
        
        # Prepare context data
        context_str = json.dumps(user_context, default=str)
        
        # -----------------
        # INTERCEPT DESTRUCTIVE ACTIONS BEFORE TOOL INVOCATION
        # If user did not say "yes" confirming it yet, we check the query for delete tasks/events intents
        # and store a PendingConfirmation in the database.
        # -----------------
        from datetime import datetime, timedelta, timezone as dt_timezone
        from app.models.confirmation import PendingConfirmation
        from app.models.task import Task
        from app.models.event import Event
        
        # Simple keywords parsing check to block direct execution
        # Check if user asks to delete a task or calendar event
        has_delete = any(k in lower_msg for k in ["delete", "remove", "cancel", "erase"])
        has_task = "task" in lower_msg
        has_event = any(k in lower_msg for k in ["event", "meeting", "calendar"])
        
        if has_delete and not is_confirmation:
            with SessionLocal() as db:
                action = None
                res_id = None
                res_title = None
                
                if has_task:
                    action = "delete_task"
                    # Try finding a task matching text
                    words = [w for w in message.split() if w.lower() not in ["delete", "my", "task", "remove", "cancel", "erase"]]
                    search_term = " ".join(words)
                    task = db.query(Task).filter(
                        Task.user_id == user_id, 
                        Task.title.ilike(f"%{search_term}%"),
                        Task.deleted_at.is_(None)
                    ).first()
                    if task:
                        res_id = str(task.id)
                        res_title = task.title
                elif has_event:
                    action = "delete_event"
                    words = [w for w in message.split() if w.lower() not in ["delete", "my", "event", "meeting", "calendar", "tomorrow", "tomorrow's"]]
                    search_term = " ".join(words)
                    event = db.query(Event).filter(
                        Event.user_id == user_id,
                        Event.title.ilike(f"%{search_term}%"),
                        Event.deleted_at.is_(None)
                    ).first()
                    if event:
                        res_id = str(event.id)
                        res_title = event.title
                        
                if action and res_id:
                    # Check if there is already a pending confirmation to avoid duplication
                    db.query(PendingConfirmation).filter(
                        PendingConfirmation.whatsapp_phone == user_context.get("whatsapp_phone"),
                        PendingConfirmation.action == action,
                        PendingConfirmation.resource_id == res_id
                    ).delete()
                    
                    pending = PendingConfirmation(
                        whatsapp_phone=user_context.get("whatsapp_phone"),
                        action=action,
                        resource_id=res_id,
                        resource_title=res_title,
                        expires_at=datetime.now(dt_timezone.utc) + timedelta(minutes=10)
                    )
                    db.add(pending)
                    db.commit()
                    
                    output_msg = f"[CONFIRMATION_REQUIRED] Action: {action} | ID: {res_id} | Title: {res_title}"
                    return {
                        "response": output_msg,
                        "action_taken": False,
                        "confirmation_required": True,
                        "raw_result": {"output": output_msg}
                    }

        input_data = {
            "input": f"User context: {context_str}\nUser ID: {user_id}\n{local_meta}\n\nMessage: {message}",
            "chat_history": conversation_history
        }
        
        try:
            # Run agent with tools
            result = await self.agent_executor.ainvoke(input_data)
            final_output = result.get("output", str(result))
            
            # Record assistant reply in DB
            with SessionLocal() as db:
                ai_reply = ConversationHistory(
                    user_id=user_id,
                    message_text=final_output,
                    is_from_user=False
                )
                db.add(ai_reply)
                db.commit()

            # Format Response
            # If confirmation request, structured tag triggers UI modal overlay in downstream channels
            return {
                "response": final_output,
                "action_taken": "tool" in str(result).lower() or "created" in final_output.lower(),
                "confirmation_required": "[CONFIRMATION_REQUIRED]" in final_output,
                "raw_result": result
            }
            
        except Exception as e:
            logger.error(f"Error in AgentExecutor: {e}. Attempting fallback structure extraction.", exc_info=True)
            try:
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