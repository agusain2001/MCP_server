import pytest
from .data_provider import MarketDataProvider
from .models import TickerResponse, OHLCV
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
import ccxt.async_support as ccxt
import time

# --- Sample Data ---

RAW_TICKER_DATA = {
    'symbol': 'BTC/USDT',
    'timestamp': 1678886400000,
    'datetime': '2023-03-15T12:00:00.000Z',
    'high': 30000.0,
    'low': 29000.0,
    'bid': 29500.0,
    'ask': 29501.0,
    'last': 29500.5,
    'volume': 1000.0,
    'info': {} # ccxt includes this
}

RAW_OHLCV_DATA = [
    [1678838400000, 29000.0, 29100.0, 28900.0, 29050.0, 100.0],
    [1678842000000, 29050.0, 29200.0, 29000.0, 29150.0, 120.0]
]

# --- Fixtures ---

@pytest.fixture
def provider() -> MarketDataProvider:
    """Returns a new MarketDataProvider instance for each test."""
    return MarketDataProvider(ticker_ttl_seconds=10)

@pytest.fixture
def mock_exchange() -> AsyncMock:
    """Creates a mock CCXT exchange instance."""
    exchange = AsyncMock(spec=ccxt.Exchange)
    exchange.fetch_ticker.return_value = RAW_TICKER_DATA
    exchange.fetch_ohlcv.return_value = RAW_OHLCV_DATA
    exchange.has = {'fetchOHLCV': True}
    exchange.timeframes = {'1h': '1h', '1d': '1d'}
    exchange.close = AsyncMock()
    return exchange

# --- Tests ---

@pytest.mark.asyncio
async def test_get_exchange_instance_success(provider: MarketDataProvider):
    """Test successful creation of an exchange instance."""
    # We patch getattr to return a mock class
    with patch('ccxt.async_support.getattr', return_value=MagicMock(return_value="Instance")) as mock_getattr:
        instance = await provider._get_exchange_instance("binance")
        mock_getattr.assert_called_with(ccxt, "binance")
        assert instance == "Instance"

@pytest.mark.asyncio
async def test_get_exchange_instance_not_found(provider: MarketDataProvider):
    """Test failure when an exchange ID doesn't exist."""
    with pytest.raises(HTTPException) as e:
        await provider._get_exchange_instance("fake_exchange")
    assert e.value.status_code == 404
    assert "not found" in e.value.detail

@pytest.mark.asyncio
async def test_get_ticker_success(provider: MarketDataProvider, mock_exchange: AsyncMock):
    """Test successful fetching of a ticker."""
    # Patch the internal method that creates the exchange
    with patch.object(provider, '_get_exchange_instance', return_value=mock_exchange):
        result = await provider.get_ticker("binance", "BTC/USDT")
        
        assert isinstance(result, TickerResponse)
        assert result.symbol == "BTC/USDT"
        assert result.last == 29500.5
        mock_exchange.fetch_ticker.assert_called_with("BTC/USDT")
        mock_exchange.close.assert_called_once()

@pytest.mark.asyncio
async def test_get_ticker_caching(provider: MarketDataProvider, mock_exchange: AsyncMock):
    """Test that the ticker cache is used."""
    with patch.object(provider, '_get_exchange_instance', return_value=mock_exchange):
        # Call twice
        await provider.get_ticker("binance", "BTC/USDT")
        await provider.get_ticker("binance", "BTC/USDT")
        
        # Should only be fetched once
        mock_exchange.fetch_ticker.assert_called_once()
        # Connection should only be opened and closed once
        mock_exchange.close.assert_called_once()

@pytest.mark.asyncio
async def test_get_ticker_cache_expiry(mock_exchange: AsyncMock):
    """Test that the cache expires after the TTL."""
    # Use a very short TTL for the test
    provider = MarketDataProvider(ticker_ttl_seconds=1)
    
    with patch.object(provider, '_get_exchange_instance', return_value=mock_exchange):
        # Call, this will cache
        await provider.get_ticker("binance", "BTC/USDT")
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Call again, should fetch again
        await provider.get_ticker("binance", "BTC/USDT")
        
        # Should be fetched twice
        assert mock_exchange.fetch_ticker.call_count == 2
        assert mock_exchange.close.call_count == 2

@pytest.mark.asyncio
async def test_get_ticker_bad_symbol(provider: MarketDataProvider, mock_exchange: AsyncMock):
    """Test handling of ccxt.BadSymbol exception."""
    mock_exchange.fetch_ticker.side_effect = ccxt.BadSymbol("Symbol not found")
    
    with patch.object(provider, '_get_exchange_instance', return_value=mock_exchange):
        with pytest.raises(HTTPException) as e:
            await provider.get_ticker("binance", "BAD/SYMBOL")
        
        assert e.value.status_code == 404
        assert "Symbol 'BAD/SYMBOL' not found" in e.value.detail

@pytest.mark.asyncio
async def test_get_historical_success(provider: MarketDataProvider, mock_exchange: AsyncMock):
    """Test successful fetching of historical data."""
    with patch.object(provider, '_get_exchange_instance', return_value=mock_exchange):
        result = await provider.get_historical("binance", "BTC/USDT", "1h", 123456, 100)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], OHLCV)
        assert result[0].timestamp == 1678838400000
        mock_exchange.fetch_ohlcv.assert_called_with("BTC/USDT", "1h", since=123456, limit=100)
        mock_exchange.close.assert_called_once()

@pytest.mark.asyncio
async def test_get_historical_unsupported(provider: MarketDataProvider, mock_exchange: AsyncMock):
    """Test historical fetch on an exchange that doesn't support it."""
    mock_exchange.has['fetchOHLCV'] = False
    
    with patch.object(provider, '_get_exchange_instance', return_value=mock_exchange):
        with pytest.raises(HTTPException) as e:
            await provider.get_historical("binance", "BTC/USDT", "1d", None, None)
        
        assert e.value.status_code == 400
        assert "does not support fetching OHLCV" in e.value.detail

@pytest.mark.asyncio
async def test_get_historical_bad_timeframe(provider: MarketDataProvider, mock_exchange: AsyncMock):
    """Test historical fetch with an unsupported timeframe."""
    with patch.object(provider, '_get_exchange_instance', return_value=mock_exchange):
        with pytest.raises(HTTPException) as e:
            await provider.get_historical("binance", "BTC/USDT", "1y", None, None)
        
        assert e.value.status_code == 400
        assert "Timeframe '1y' not supported" in e.value.detail