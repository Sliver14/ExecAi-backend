"""Enhanced Prompt templates for ExecAI LangChain agents."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Improved Intent detection and structured extraction prompt
# Note: This prompt is kept as fallback. Main agent uses tool-calling prompt in core_agent.py

# Action / Response prompt
RESPONSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are ExecAI. Be concise, actionable, and supportive.
Current user context: {user_context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

INTENT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are ExecAI's intent extractor. Extract the intent, entities, confidence level (high/medium/low), and formulate a short professional response.
User context: {user_context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])
