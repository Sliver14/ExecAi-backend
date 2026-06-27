from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
import logging

from app.db.base import get_db
from app.core.config import get_settings
from app.dependencies.current_user import get_or_create_user
from app.agents.core_agent import ExecAIAgent
from app.utils.whatsapp_client import send_whatsapp_message

logger = logging.getLogger("execai.whatsapp")

router = APIRouter()

# -------------------------
# WhatsApp Webhook Verification
# -------------------------
@router.get("")
async def verify_webhook(request: Request):
    settings = get_settings()

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully.")
        return PlainTextResponse(content=challenge)

    logger.warning("Invalid WhatsApp webhook verification attempt.")
    raise HTTPException(
        status_code=403,
        detail="Invalid verification token",
    )


# -------------------------
# Receive WhatsApp Messages
# -------------------------
@router.post("")
@router.post("/")
async def webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        payload = await request.json()

        logger.info("Incoming WhatsApp payload received.")

        entry = payload.get("entry", [])
        if not entry:
            return {"status": "ignored"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "ignored"}

        value = changes[0].get("value", {})

        messages = value.get("messages", [])
        if not messages:
            logger.info("Webhook event contained no message.")
            return {"status": "ignored"}

        message = messages[0]
        from_phone = message.get("from")
        
        # Check if this is an interactive button reply
        is_button_reply = False
        button_id = None
        text = ""

        if message.get("type") == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                is_button_reply = True
                button_reply = interactive.get("button_reply", {})
                button_id = button_reply.get("id")
                text = button_reply.get("title", "")
        elif message.get("type") == "text":
            text = message.get("text", {}).get("body", "")

        if not from_phone or not text:
            logger.warning("Invalid WhatsApp payload.")
            return {"status": "ignored"}

        logger.info(
            "Received message from %s (button_reply: %s): %s",
            from_phone,
            is_button_reply,
            text,
        )

        user = get_or_create_user(db, from_phone)

        # ---------------------------------
        # Handle Interactive Button Callbacks
        # ---------------------------------
        from app.models.confirmation import PendingConfirmation
        from datetime import datetime, timezone as dt_timezone
        
        if is_button_reply and button_id:
            # Format expected: confirm_delete_task:<id> or cancel_delete_task:<id>
            parts = button_id.split(":")
            action_type = parts[0]
            resource_id = parts[1] if len(parts) > 1 else None
            
            # Find matching pending confirmation
            pending = db.query(PendingConfirmation).filter(
                PendingConfirmation.whatsapp_phone == from_phone,
                PendingConfirmation.resource_id == resource_id
            ).first()
            
            if not pending:
                await send_whatsapp_message(from_phone, "This confirmation request has expired or is invalid.")
                return {"status": "processed"}
                
            # Verify expiry
            if datetime.now(dt_timezone.utc) > pending.expires_at.replace(tzinfo=dt_timezone.utc):
                db.delete(pending)
                db.commit()
                await send_whatsapp_message(from_phone, "This confirmation request has expired (10 minute limit).")
                return {"status": "processed"}
                
            if "confirm_" in action_type:
                # Execute the tool
                from app.agents.tools import delete_task_tool, delete_event_tool
                if pending.action == "delete_task":
                    result_msg = await delete_task_tool._run(user_id=user.id, task_identifier=resource_id)
                elif pending.action == "delete_event":
                    result_msg = await delete_event_tool._run(user_id=user.id, event_identifier=resource_id)
                else:
                    result_msg = "Unknown action confirmed."
                    
                db.delete(pending)
                db.commit()
                await send_whatsapp_message(from_phone, result_msg)
                return {"status": "processed"}
            else:
                # Cancelled! Discard action
                db.delete(pending)
                db.commit()
                await send_whatsapp_message(from_phone, "Okay, I won't delete it.")
                return {"status": "processed"}

        # ---------------------------------
        # AI Agent Pipeline
        # ---------------------------------
        agent = ExecAIAgent()

        user_context = {
            "user_id": str(user.id),
            "whatsapp_phone": from_phone,
            "name": user.name,
            "role": user.role,
            "timezone": user.timezone,
            "work_hours": (
                f"{user.work_start_time} - {user.work_end_time}"
                if user.work_start_time
                else None
            ),
            "top_priorities": user.top_priorities,
        }

        result = await agent.process_message(
            text,
            user_context,
            user.id,
        )

        response_text = result.get(
            "response",
            "Understood. How else can I assist you today?",
        )

        logger.info("AI Response: %s", response_text)

        # ---------------------------------
        # Send WhatsApp Reply
        # ---------------------------------
        if result.get("confirmation_required") and "[CONFIRMATION_REQUIRED]" in response_text:
            # Parse interception details: Action: delete_task | ID: <id> | Title: <title>
            parts = response_text.replace("[CONFIRMATION_REQUIRED] ", "").split(" | ")
            action_tag = parts[0].split(": ")[1]
            resource_id = parts[1].split(": ")[1]
            resource_title = parts[2].split(": ")[1]
            
            body_text = f"Delete \"{resource_title}\"?"
            
            buttons = [
                {
                    "type": "reply",
                    "reply": {
                        "id": f"confirm_{action_tag}:{resource_id}",
                        "title": "Yes"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": f"cancel_{action_tag}:{resource_id}",
                        "title": "Cancel"
                    }
                }
            ]
            from app.utils.whatsapp_client import send_whatsapp_interactive_buttons
            await send_whatsapp_interactive_buttons(from_phone, body_text, buttons)
        else:
            success = await send_whatsapp_message(
                from_phone,
                response_text,
            )

            if success:
                logger.info(
                    "WhatsApp reply successfully sent to %s",
                    from_phone,
                )
            else:
                logger.error(
                    "Failed sending WhatsApp reply to %s",
                    from_phone,
                )

        return {"status": "processed"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )