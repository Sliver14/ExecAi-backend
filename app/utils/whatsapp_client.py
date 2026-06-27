import logging
import httpx

from app.core.config import get_settings

logger = logging.getLogger("execai.whatsapp")

settings = get_settings()

GRAPH_URL = (
    f"https://graph.facebook.com/v23.0/"
    f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
)


async def send_whatsapp_message(to_phone: str, text: str) -> bool:
    """
    Send a WhatsApp message using the WhatsApp Cloud API.
    """

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {
            "body": text,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GRAPH_URL,
                headers=headers,
                json=payload,
            )

        logger.info(
            "WhatsApp API Response %s: %s",
            response.status_code,
            response.text,
        )

        response.raise_for_status()

        return True

    except Exception:
        logger.exception("Failed sending WhatsApp message")
        return False


async def send_whatsapp_interactive_buttons(to_phone: str, body: str, buttons: list) -> bool:
    """
    Send a native WhatsApp Interactive Button message using Meta's Cloud API.
    """
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": body,
            },
            "footer": {
                "text": "ExecAI",
            },
            "action": {
                "buttons": buttons,
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GRAPH_URL,
                headers=headers,
                json=payload,
            )

        logger.info(
            "WhatsApp Interactive Response %s: %s",
            response.status_code,
            response.text,
        )
        response.raise_for_status()
        return True

    except Exception:
        logger.exception("Failed sending WhatsApp interactive buttons")
        return False