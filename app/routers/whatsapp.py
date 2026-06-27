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

        # Ignore non-text messages
        if message.get("type") != "text":
            logger.info("Ignoring non-text WhatsApp message.")
            return {"status": "ignored"}

        text = message.get("text", {}).get("body", "")

        if not from_phone or not text:
            logger.warning("Invalid WhatsApp payload.")
            return {"status": "ignored"}

        logger.info(
            "Received message from %s: %s",
            from_phone,
            text,
        )

        # ---------------------------------
        # Load or create user
        # ---------------------------------

        user = get_or_create_user(db, from_phone)

        # ---------------------------------
        # AI Agent
        # ---------------------------------

        agent = ExecAIAgent()

        user_context = {
            "user_id": str(user.id),
            "name": user.name,
            "role": user.role,
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

    # except Exception:
    #     logger.exception("Unhandled error while processing webhook.")

    #     raise HTTPException(
    #         status_code=500,
    #         detail="Internal server error",
    #     )

    except Exception as e:
        import traceback

        traceback.print_exc()

        logger.exception(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )