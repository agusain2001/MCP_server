from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server Configuration
    app_name: str = "MCP Crypto Market Data Server"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Cache Configuration
    ticker_cache_ttl: int = 10  # seconds
    ohlcv_cache_ttl: int = 60   # seconds
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # WebSocket Configuration
    ws_poll_interval_min: int = 1
    ws_poll_interval_max: int = 60
    ws_poll_interval_default: int = 5
    
    # CCXT Configuration
    ccxt_enable_rate_limit: bool = True
    ccxt_timeout: int = 30000  # milliseconds
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    class Config:
        env_file = ".env"
        env_prefix = "MCP_"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
