from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    bot_token: SecretStr
    admin_id: int

    # Telegram channels for posting
    public_channel_id: int = -1003968872257   # @darkstabspace (публичный)
    private_channel_id: int = -1003948164133  # личный канал «для двоих»

    # Auto-posting (APScheduler)
    autopost_enabled: bool = True
    autopost_hour: int = 10   # час публикации (Europe/Kyiv)
    autopost_minute: int = 0
    
    anthropic_api_key: SecretStr
    openai_api_key: SecretStr
    
    database_url: str = "sqlite+aiosqlite:///database/lia.db"
    redis_url: str = "redis://localhost:6379"
    
    wayforpay_merchant: str = ""
    wayforpay_secret: SecretStr = SecretStr("")
    crypto_wallet_usdt: str = ""
    
    free_daily_limit: int = 10
    premium_lite_daily: int = 50
    premium_pro_daily: int = 200

    # PostHog product analytics
    posthog_enabled: bool = True
    posthog_api_key: SecretStr = SecretStr("")
    posthog_host: str = "https://eu.i.posthog.com"

    # N8N integration
    n8n_url: str = "http://80.89.237.50:5678"
    n8n_api_key: SecretStr = SecretStr("")
    n8n_webhook_token: SecretStr = SecretStr("")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Игнорируем лишние переменные из корневого .env

settings = Settings()