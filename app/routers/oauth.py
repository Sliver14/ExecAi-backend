"""Google OAuth endpoints for ExecAI."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.user import User
from app.utils.google_calendar import get_auth_url, exchange_code_for_tokens
import logging

logger = logging.getLogger("execai.oauth")
router = APIRouter()

@router.get("/login")
def login(whatsapp_phone: str = Query(..., description="The user's registered WhatsApp phone number")):
    """Redirect to Google's OAuth login page."""
    url = get_auth_url(whatsapp_phone)
    return RedirectResponse(url=url)

@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    """Exchange OAuth code and link tokens to the user."""
    whatsapp_phone = state
    user = db.query(User).filter(User.whatsapp_phone == whatsapp_phone).first()
    if not user:
        # Create user if they login via web first
        user = User(whatsapp_phone=whatsapp_phone, name="User", subscription_status="trial")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    try:
        token_data = await exchange_code_for_tokens(code)
        
        user.google_access_token = token_data.get("access_token")
        if "refresh_token" in token_data:
            user.google_refresh_token = token_data.get("refresh_token")
        user.google_calendar_connected = True
        
        db.commit()
        return {"status": "success", "message": "Google Calendar linked successfully! You can close this window."}
    except Exception as e:
        logger.exception("Failed linking Google Calendar OAuth")
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {str(e)}")

@router.get("/disconnect")
def disconnect(whatsapp_phone: str, db: Session = Depends(get_db)):
    """Remove user's Google OAuth credentials."""
    user = db.query(User).filter(User.whatsapp_phone == whatsapp_phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.google_access_token = None
    user.google_refresh_token = None
    user.google_calendar_connected = False
    db.commit()
    
    return {"status": "success", "message": "Google Calendar disconnected."}
