"""
Configuration management using environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    Create a .env file with these values:
    
    GROQ_API_KEY=gsk_...
    HUBSPOT_API_KEY=your-hubspot-api-key
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
    HOT_LEAD_OWNER_ID=user-id-1
    WARM_LEAD_OWNER_ID=user-id-2
    COLD_LEAD_OWNER_ID=user-id-3
    """
    
    # API Keys
    GROQ_API_KEY: str = "your-groq-api-key"
    HUBSPOT_API_KEY: str = "your-hubspot-api-key"
    SLACK_WEBHOOK_URL: str = "your-slack-webhook-url"
    
    # HubSpot Configuration
    HUBSPOT_PORTAL_ID: Optional[str] = None  # Your HubSpot portal/account ID
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = "your-telegram-bot-token"
    TELEGRAM_CHAT_ID: str = "your-telegram-chat-id"
    
    # Company Information
    COMPANY_NAME: str = "The One'z and Zero"
    COMPANY_EMAIL: str = "theonesnzeros@gmail.com"
    GMAIL_APP_PASSWORD: str = "your-gmail-app-password"
    
    # Lead Routing Configuration
    HOT_LEAD_OWNER_ID: str = "hot-lead-owner-user-id"
    WARM_LEAD_OWNER_ID: str = "warm-lead-owner-user-id"
    COLD_LEAD_OWNER_ID: str = "cold-lead-owner-user-id"
    
    # Application Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # AI Configuration
    AI_MODEL: str = "llama-3.3-70b-versatile"
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

