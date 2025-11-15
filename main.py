import asyncio
from datetime import datetime
from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect,
    Query, HTTPException, Request, Depends
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from .data_provider import MarketDataProvider
from .models import TickerResponse, OHLCV, ExchangeInfo, HealthCheck, ErrorResponse
from .config import get_settings
from .logger import setup_logger
from .rate_limiter import rate_limiter

# Setup
settings = get_settings()
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A production-ready server to fetch real-time and historical crypto data using CCXT.",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create single instance of data provider
provider = MarketDataProvider()

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            detail=exc.detail,
            status_code=exc.status_code,
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    provider.clear_caches()
    logger.info("Server shutting down")


@app.get("/", tags=["General"])
async def read_root():
    """Root endpoint to check if the server is running."""
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheck, tags=["General"])
async def health_check():
    """
    Health check endpoint with cache statistics.
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        cache_stats=provider.get_cache_stats()
    )


@app.get("/exchanges", response_model=List[ExchangeInfo], tags=["General"])
async def list_exchanges():
    """
    Get list of all supported exchanges with their capabilities.
    """
    return await provider.get_supported_exchanges()


@app.get(
    "/price/{exchange_id}/{symbol}",
    response_model=TickerResponse,
    tags=["Market Data"],
    summary="Get Real-time Price Ticker"
)
async def get_price(
    exchange_id: str,
    symbol: str,
    request: Request
):
    """
    Retrieves the latest ticker information for a trading symbol.

    - **exchange_id**: Exchange ID (e.g., `binance`, `coinbase`)
    - **symbol**: Trading symbol (e.g., `BTC/USDT`, `ETH/USD`)
    """
    await rate_limiter.check_rate_limit(request)
    return await provider.get_ticker(exchange_id, symbol)


@app.get(
    "/historical/{exchange_id}/{symbol}",
    response_model=List[OHLCV],
    tags=["Market Data"],
    summary="Get Historical OHLCV Data"
)
async def get_historical_data(
    exchange_id: str,
    symbol: str,
    request: Request,
    timeframe: str = Query(
        '1d',
        description="Timeframe for candles (e.g., '1m', '5m', '1h', '1d')"
    ),
    since: Optional[int] = Query(
        None,
        description="Start time as Unix timestamp in milliseconds"
    ),
    limit: Optional[int] = Query(
        100,
        description="Number of candles to retrieve",
        ge=1,
        le=1000
    )
):
    """
    Retrieves historical OHLCV candle data for a symbol.
    """
    await rate_limiter.check_rate_limit(request)
    return await provider.get_historical(exchange_id, symbol, timeframe, since, limit)


@app.websocket("/ws/{exchange_id}/{symbol}")
async def websocket_endpoint(
    websocket: WebSocket,
    exchange_id: str,
    symbol: str,
    poll_interval: int = Query(
        settings.ws_poll_interval_default,
        description="Polling interval in seconds",
        ge=settings.ws_poll_interval_min,
        le=settings.ws_poll_interval_max
    )
):
    """
    Provides real-time ticker updates via WebSocket.
    The server polls the exchange at the specified interval.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {exchange_id}/{symbol} (interval: {poll_interval}s)")

    try:
        while True:
            try:
                ticker_data = await provider.get_ticker(exchange_id, symbol)
                await websocket.send_json(ticker_data.dict())
                await asyncio.sleep(poll_interval)
                
            except HTTPException as e:
                await websocket.send_json({
                    "error": e.detail,
                    "status_code": e.status_code
                })
                logger.error(f"WebSocket error: {e.detail}")
                break
            except Exception as e:
                await websocket.send_json({
                    "error": str(e),
                    "status_code": 500
                })
                logger.exception(f"Unexpected WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {exchange_id}/{symbol}")
    except Exception as e:
        logger.exception(f"WebSocket connection error: {e}")
        await websocket.close(code=1011)


@app.post("/admin/clear-cache", tags=["Admin"])
async def clear_cache():
    """Clear all caches (admin endpoint)."""
    provider.clear_caches()
    return {"message": "All caches cleared successfully"}


@app.get("/admin/cache-stats", tags=["Admin"])
async def get_cache_stats():
    """Get detailed cache statistics (admin endpoint)."""
    return provider.get_cache_stats()
