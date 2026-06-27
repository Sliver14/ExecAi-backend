from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.core.config import get_settings
from app.dependencies.current_user import get_or_create_user
from app.agents.core_agent import ExecAIAgent
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.services.event_service import EventService
import json
from typing import Dict

router = APIRouter()

@router.get("/")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    settings = get_settings()  # TODO: import properly
    
    if mode == "subscribe" and token == settings.WHATSAPP_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Invalid verification token")

@router.post("/")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Handle incoming WhatsApp messages"""
    try:
        data = await request.json()
        
        # Extract WhatsApp message (standard Cloud API format)
        messages = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
        
        if not messages:
            return {"status": "ignored"}
        
        message = messages[0]
        from_phone = message.get("from")
        text = message.get("text", {}).get("body", "")
        
        if not from_phone or not text:
            return {"status": "ignored"}
        
        # Get or create user
        user = get_or_create_user(db, from_phone)
        
        # Prepare services
        services = {
            "task": TaskService(db),
            "project": ProjectService(db),
            "event": EventService(db),
        }
        
        # Initialize agent
        agent = ExecAIAgent()
        
        # Get user context
        user_context = {
            "user_id": str(user.id),
            "name": user.name,
            "role": user.role,
            "work_hours": f"{user.work_start_time} - {user.work_end_time}" if user.work_start_time else None,
            "top_priorities": user.top_priorities,
        }
        
        # Process with new Tool Calling Agent
        result = await agent.process_message(
            text, 
            user_context, 
            user.id
        )
        
        response_text = result.get("response", "Understood. How else can I assist you today?")
        
        # Send response back via WhatsApp (placeholder)
        from app.utils.whatsapp_client import send_whatsapp_message
        send_whatsapp_message(from_phone, response_text)
        
        # Save conversation history (TODO: add service)
        print(f"Processed message from {from_phone}: {text[:100]}")
        
        return {"status": "processed"}
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
