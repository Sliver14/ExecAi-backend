"""Google Calendar Integration Client for ExecAI."""

import httpx
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
from app.core.config import get_settings
from app.db.base import SessionLocal
from app.models.user import User

logger = logging.getLogger("execai.google_calendar")
settings = get_settings()

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"

def get_auth_url(whatsapp_phone: str) -> str:
    """Generate authorization redirect URL."""
    client_id = settings.GOOGLE_CLIENT_ID or "placeholder_client_id"
    redirect_uri = settings.GOOGLE_REDIRECT_URI or "http://localhost:8000/oauth/google/callback"
    
    # Pass whatsapp_phone in state to link back to user during callback
    state = whatsapp_phone
    
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "scope=https://www.googleapis.com/auth/calendar.events&"
        "access_type=offline&"
        "prompt=consent&"
        f"state={state}"
    )
    return url

async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access and refresh tokens."""
    client_id = settings.GOOGLE_CLIENT_ID or "placeholder_client_id"
    client_secret = settings.GOOGLE_CLIENT_SECRET or "placeholder_client_secret"
    redirect_uri = settings.GOOGLE_REDIRECT_URI or "http://localhost:8000/oauth/google/callback"
    
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(OAUTH_TOKEN_URL, data=payload)
        response.raise_for_status()
        return response.json()

async def get_valid_access_token(user: User) -> Optional[str]:
    """Retrieve or refresh token for Google Calendar interactions."""
    if not user.google_refresh_token:
        return None
        
    client_id = settings.GOOGLE_CLIENT_ID or "placeholder_client_id"
    client_secret = settings.GOOGLE_CLIENT_SECRET or "placeholder_client_secret"
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": user.google_refresh_token,
        "grant_type": "refresh_token",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(OAUTH_TOKEN_URL, data=payload)
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get("access_token")
                
                # Save refreshed access token to DB
                with SessionLocal() as db:
                    db_user = db.query(User).filter(User.id == user.id).first()
                    if db_user and new_access_token:
                        db_user.google_access_token = new_access_token
                        db.commit()
                return new_access_token
            else:
                logger.error(f"Failed to refresh Google token: {response.text}")
                return user.google_access_token
    except Exception as e:
        logger.exception("Error refreshing Google access token")
        return user.google_access_token

async def create_google_calendar_event(user: User, event_data: Dict[str, Any]) -> Optional[str]:
    """Create event on Google Calendar, with support for RRULE list."""
    token = await get_valid_access_token(user)
    if not token:
        logger.warning(f"User {user.id} has no valid Google Calendar tokens.")
        return None
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=15) as client:
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        response = await client.post(url, headers=headers, json=event_data)
        if response.status_code in [200, 201]:
            return response.json().get("id")
        else:
            logger.error(f"Google Calendar Create API error: {response.text}")
            return None

async def delete_google_calendar_event(user: User, gcal_event_id: str) -> bool:
    """Delete event from Google Calendar."""
    token = await get_valid_access_token(user)
    if not token:
        return False
        
    headers = {
        "Authorization": f"Bearer {token}",
    }
    
    async with httpx.AsyncClient(timeout=15) as client:
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{gcal_event_id}"
        response = await client.delete(url, headers=headers)
        if response.status_code in [200, 204]:
            return True
        logger.error(f"Google Calendar Delete API error: {response.text}")
        return False
