from pydantic import BaseModel, Field

class TickerResponse(BaseModel):
    """
    Pydantic model for a standardized Ticker response.
    This validates and structures the data from ccxt.fetch_ticker.
    """
    symbol: str
    timestamp: int | None = Field(None, description="Unix timestamp in milliseconds")
    datetime: str | None = Field(None, description="ISO 8601 datetime string")
    high: float | None = Field(None, description="Highest price in 24h")
    low: float | None = Field(None, description="Lowest price in 24h")
    bid: float | None = Field(None, description="Best current bid price")
    ask: float | None = Field(None, description="Best current ask price")
    last: float | None = Field(None, description="Last traded price")
    volume: float | None = Field(None, description="Volume traded in 24h")
    
    # Allows model to be created from arbitrary class instances
    class Config:
        orm_mode = True 
        # Pydantic v2
        # from_attributes = True 

class OHLCV(BaseModel):
    """
    Pydantic model for a single OHLCV candle.
    """
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    class Config:
        orm_mode = True
        # Pydantic v2
        # from_attributes = True