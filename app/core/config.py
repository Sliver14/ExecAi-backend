from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "ExecAI"
    VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = "sqlite:///./execai.db"
    
    # OpenAI
    OPENAI_API_KEY: str = "placeholder_openai_key"
    
    # WhatsApp Business API
    WHATSAPP_ACCESS_TOKEN: str = "placeholder_access_token"
    WHATSAPP_PHONE_NUMBER_ID: str = "placeholder_phone_id"
    WHATSAPP_WEBHOOK_SECRET: str = "placeholder_webhook_secret"  # For verifying webhooks
    WHATSAPP_TOKEN: str = "placeholder_verify_token"  # For webhook verification challenge
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

