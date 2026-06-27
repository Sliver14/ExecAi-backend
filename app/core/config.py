from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "ExecAI"
    VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # WhatsApp Business API
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_WEBHOOK_SECRET: Optional[str] = None  # For verifying webhook payload signatures if needed
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None  # For webhook verification challenge
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()


