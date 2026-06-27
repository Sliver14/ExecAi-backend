import logging

logger = logging.getLogger("execai.whatsapp")

def send_whatsapp_message(to_phone: str, text: str):
    """Placeholder function to simulate sending a WhatsApp message."""
    logger.info(f"Sending WhatsApp message to {to_phone}: {text}")
    print(f"[WhatsApp Mock Send] To: {to_phone} | Message: {text}")
