from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TickerResponse(BaseModel):
    """Pydantic model for a standardized Ticker response."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    timestamp: Optional[int] = Field(None, description="Unix timestamp in milliseconds")
    datetime: Optional[str] = Field(None, description="ISO 8601 datetime string")
    high: Optional[float] = Field(None, description="Highest price in 24h")
    low: Optional[float] = Field(None, description="Lowest price in 24h")
    bid: Optional[float] = Field(None, description="Best current bid price")
    bidVolume: Optional[float] = Field(None, description="Bid volume")
    ask: Optional[float] = Field(None, description="Best current ask price")
    askVolume: Optional[float] = Field(None, description="Ask volume")
    vwap: Optional[float] = Field(None, description="Volume weighted average price")
    open: Optional[float] = Field(None, description="Opening price")
    close: Optional[float] = Field(None, description="Closing price")
    last: Optional[float] = Field(None, description="Last traded price")
    previousClose: Optional[float] = Field(None, description="Previous closing price")
    change: Optional[float] = Field(None, description="Absolute price change")
    percentage: Optional[float] = Field(None, description="Percentage price change")
    average: Optional[float] = Field(None, description="Average price")
    baseVolume: Optional[float] = Field(None, description="Volume in base currency")
    quoteVolume: Optional[float] = Field(None, description="Volume in quote currency")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "last": 45000.50,
                "bid": 45000.00,
                "ask": 45001.00,
                "high": 46000.00,
                "low": 44000.00,
                "volume": 1500.25
            }
        }


class OHLCV(BaseModel):
    """Pydantic model for a single OHLCV candle."""
    
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Trading volume")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1678838400000,
                "open": 45000.00,
                "high": 45500.00,
                "low": 44800.00,
                "close": 45200.00,
                "volume": 123.45
            }
        }


class ExchangeInfo(BaseModel):
    """Information about a supported exchange."""
    
    id: str = Field(..., description="Exchange identifier")
    name: str = Field(..., description="Exchange full name")
    has_ticker: bool = Field(..., description="Supports ticker data")
    has_ohlcv: bool = Field(..., description="Supports OHLCV data")
    timeframes: List[str] = Field(..., description="Supported timeframes")
    rate_limit: Optional[int] = Field(None, description="Rate limit in ms")


class HealthCheck(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    cache_stats: Optional[Dict[str, Any]] = Field(None, description="Cache statistics")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")
