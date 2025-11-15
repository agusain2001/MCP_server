import asyncio
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Query,
    HTTPException
)
from .data_provider import MarketDataProvider
from .models import TickerResponse, OHLCV

# Initialize the FastAPI app
app = FastAPI(
    title="MCP Server (Crypto Market Data Provider)",
    description="A server to fetch real-time and historical crypto data using CCXT.",
    version="1.0.0"
)

# Create a single instance of the data provider to share its cache
provider = MarketDataProvider()

@app.get("/")
async def read_root():
    """
    Root endpoint to check if the server is running.
    """
    return {"message": "MCP Server is running. Visit /docs for API documentation."}

@app.get(
    "/price/{exchange_id}/{symbol}",
    response_model=TickerResponse,
    summary="Get Real-time Price Ticker"
)
async def get_price(exchange_id: str, symbol: str):
    """
    Retrieves the latest ticker information (price, bid, ask, volume, etc.)
    for a given trading symbol on a specific exchange.

    - **exchange_id**: The ID of the exchange (e.g., `binance`, `coinbase`).
    - **symbol**: The trading symbol (e.g., `BTC/USDT`, `ETH/USD`).
    """
    # The provider handles caching and error exceptions
    return await provider.get_ticker(exchange_id, symbol)

@app.get(
    "/historical/{exchange_id}/{symbol}",
    response_model=list[OHLCV],
    summary="Get Historical OHLCV Data"
)
async def get_historical_data(
    exchange_id: str,
    symbol: str,
    timeframe: str = Query(
        '1d',
        description="Timeframe for candles (e.g., '1m', '5m', '1h', '1d')"
    ),
    since: int | None = Query(
        None,
        description="Start time as a Unix timestamp in milliseconds"
    ),
    limit: int | None = Query(
        100,
        description="Number of candles to retrieve"
    )
):
    """
    Retrieves historical OHLCV (Open, High, Low, Close, Volume) candle data
    for a given symbol on a specific exchange.
    """
    # The provider handles validation and error exceptions
    return await provider.get_historical(exchange_id, symbol, timeframe, since, limit)

@app.websocket("/ws/{exchange_id}/{symbol}")
async def websocket_endpoint(
    websocket: WebSocket,
    exchange_id: str,
    symbol: str,
    poll_interval: int = Query(
        5,
        description="Polling interval in seconds",
        ge=1
    )
):
    """
    Provides real-time ticker updates for a symbol via WebSocket.
    The server polls the exchange at the specified `poll_interval`.
    """
    await websocket.accept()
    print(f"WebSocket connection accepted for {exchange_id}/{symbol}")

    try:
        while True:
            try:
                # Fetch data using the same provider (benefits from caching)
                ticker_data = await provider.get_ticker(exchange_id, symbol)
                
                # Send data to the client as JSON
                await websocket.send_json(ticker_data.dict())
                
                # Wait for the specified polling interval
                await asyncio.sleep(poll_interval)
                
            except HTTPException as e:
                # If the provider raises an error (e.g., 404), send it and break
                await websocket.send_json({"error": e.detail, "status_code": e.status_code})
                print(f"Error for {exchange_id}/{symbol}: {e.detail}")
                break
            except Exception as e:
                # Handle other unexpected errors
                await websocket.send_json({"error": str(e), "status_code": 500})
                print(f"Unexpected error for {exchange_id}/{symbol}: {e}")
                break
                
    except WebSocketDisconnect:
        print(f"Client disconnected from {exchange_id}/{symbol}")
    except Exception as e:
        # Handle connection errors
        print(f"WebSocket Error: {e}")
        await websocket.close(code=1011) # Internal error