from fastapi.testclient import TestClient
from .main import app
import pytest
from unittest.mock import patch, AsyncMock
from .models import TickerResponse, OHLCV
from fastapi import HTTPException
import time

# Create a test client instance
client = TestClient(app)

# --- Sample Data ---

MOCK_TICKER = TickerResponse(
    symbol="BTC/USDT",
    timestamp=1678886400000,
    datetime="2023-03-15T12:00:00.000Z",
    high=30000.0,
    low=29000.0,
    bid=29500.0,
    ask=29501.0,
    last=29500.5,
    volume=1000.0
)

MOCK_OHLCV_LIST = [
    OHLCV(timestamp=1678838400000, open=29000, high=29100, low=28900, close=29050, volume=100),
    OHLCV(timestamp=1678842000000, open=29050, high=29200, low=29000, close=29150, volume=120)
]

# --- Tests ---

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "MCP Server is running" in response.json()["message"]

def test_get_price_success():
    """Test the /price endpoint on a successful lookup."""
    # Patch the data_provider.get_ticker method
    with patch('main.provider.get_ticker', new_callable=AsyncMock, return_value=MOCK_TICKER) as mock_fetch:
        response = client.get("/price/binance/BTC/USDT")
        
        assert response.status_code == 200
        assert response.json()["symbol"] == "BTC/USDT"
        assert response.json()["last"] == 29500.5
        mock_fetch.assert_called_with("binance", "BTC/USDT")

def test_get_price_not_found():
    """Test the /price endpoint when the provider raises a 404 error."""
    # Mock the provider to raise an HTTPException
    with patch('main.provider.get_ticker', new_callable=AsyncMock, side_effect=HTTPException(404, "Not Found")):
        response = client.get("/price/binance/BAD/SYMBOL")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Not Found"

def test_get_historical_success():
    """Test the /historical endpoint on a successful lookup."""
    with patch('main.provider.get_historical', new_callable=AsyncMock, return_value=MOCK_OHLCV_LIST) as mock_fetch:
        response = client.get("/historical/coinbase/ETH/USD?timeframe=1h&limit=2")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["open"] == 29000
        mock_fetch.assert_called_with("coinbase", "ETH/USD", "1h", None, 2)

def test_get_historical_bad_request():
    """Test the /historical endpoint when the provider raises a 400 error."""
    with patch('main.provider.get_historical', new_callable=AsyncMock, side_effect=HTTPException(400, "Bad Timeframe")):
        response = client.get("/historical/kraken/XBT/EUR?timeframe=1y")
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Bad Timeframe"

def test_websocket_success():
    """Test the WebSocket endpoint for a successful connection and data receive."""
    # We patch the provider's get_ticker method
    with patch('main.provider.get_ticker', new_callable=AsyncMock, return_value=MOCK_TICKER):
        # We also patch asyncio.sleep to speed up the test and break the loop
        # We'll make it raise an exception after the first call
        class SleepBreaker:
            def __init__(self):
                self.called = False
            async def __call__(self, *args, **kwargs):
                if self.called:
                    raise asyncio.CancelledError("Breaking test loop")
                self.called = True
                await asyncio.sleep(0.01) # sleep a tiny bit

        with patch('asyncio.sleep', new_callable=SleepBreaker) as mock_sleep:
            try:
                with client.websocket_connect("/ws/binance/BTC/USDT?poll_interval=1") as websocket:
                    # Receive the first message
                    data = websocket.receive_json()
                    assert data["symbol"] == "BTC/USDT"
                    assert data["last"] == 29500.5
                    
                    # The loop will run again, call sleep, and raise the exception
                    # We catch the exception which is expected
                    with pytest.raises(Exception):
                         websocket.receive_json()

            except asyncio.CancelledError:
                pass # This is our expected exit
                
            assert mock_sleep.called == True