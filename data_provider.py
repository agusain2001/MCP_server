import ccxt.async_support as ccxt
from fastapi import HTTPException
from .caching import SimpleTTLCache
from .models import TickerResponse, OHLCV
import time

class MarketDataProvider:
    """
    A class to abstract the data fetching logic from CCXT.
    It handles exchange initialization, error handling, and caching.
    """
    def __init__(self, ticker_ttl_seconds: int = 10):
        """
        Initializes the data provider with a cache for ticker data.
        :param ticker_ttl_seconds: TTL (Time-To-Live) for the ticker cache.
        """
        # A short TTL for real-time ticker data is appropriate
        self.ticker_cache = SimpleTTLCache(ttl_seconds=ticker_ttl_seconds)

    async def _get_exchange_instance(self, exchange_id: str) -> ccxt.Exchange:
        """
        Dynamically creates and returns an async CCXT exchange instance.
        """
        if not hasattr(ccxt, exchange_id):
            raise HTTPException(
                status_code=404,
                detail=f"Exchange '{exchange_id}' not found."
            )
        
        try:
            exchange_class = getattr(ccxt, exchange_id)
            # Enable rate limiting (a CCXT best practice)
            instance = exchange_class({'enableRateLimit': True})
            return instance
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize exchange '{exchange_id}': {e}"
            )

    async def get_ticker(self, exchange_id: str, symbol: str) -> TickerResponse:
        """
        Fetches the latest ticker data for a symbol, using a cache.
        """
        cache_key = f"{exchange_id}_{symbol}"
        
        # Check cache first
        cached_data = self.ticker_cache.get(cache_key)
        if cached_data:
            return cached_data

        # If not in cache, fetch from exchange
        exchange = await self._get_exchange_instance(exchange_id)
        try:
            ticker_data = await exchange.fetch_ticker(symbol)
            
            # Validate and structure the data using Pydantic model
            response = TickerResponse(**ticker_data)
            
            # Store in cache
            self.ticker_cache.set(cache_key, response)
            return response
            
        except ccxt.BadSymbol as e:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{symbol}' not found on {exchange_id}: {e}"
            )
        except ccxt.NetworkError as e:
            raise HTTPException(
                status_code=503, # Service Unavailable
                detail=f"Network error connecting to {exchange_id}: {e}"
            )
        except ccxt.ExchangeError as e:
            raise HTTPException(
                status_code=400, # Bad Request
                detail=f"Exchange error from {exchange_id}: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred: {e}"
            )
        finally:
            # Always close the connection in async mode
            await exchange.close()

    async def get_historical(
        self,
        exchange_id: str,
        symbol: str,
        timeframe: str,
        since: int | None,
        limit: int | None
    ) -> list[OHLCV]:
        """
        Fetches historical OHLCV data. No caching is applied here
        due to the variable nature of `since` and `limit` parameters.
        """
        exchange = await self._get_exchange_instance(exchange_id)
        
        # Check if the exchange supports this feature
        if not exchange.has['fetchOHLCV']:
            await exchange.close()
            raise HTTPException(
                status_code=400,
                detail=f"Exchange '{exchange_id}' does not support fetching OHLCV data."
            )
        
        # Validate timeframe
        if timeframe not in exchange.timeframes:
            await exchange.close()
            raise HTTPException(
                status_code=400,
                detail=f"Timeframe '{timeframe}' not supported by {exchange_id}. Supported: {list(exchange.timeframes.keys())}"
            )

        try:
            # Fetch the raw OHLCV data (list of lists)
            ohlcv_data = await exchange.fetch_ohlcv(
                symbol,
                timeframe,
                since=since,
                limit=limit
            )
            
            # Convert the list of lists into a list of Pydantic models
            response = [
                OHLCV(
                    timestamp=d[0],
                    open=d[1],
                    high=d[2],
                    low=d[3],
                    close=d[4],
                    volume=d[5]
                ) for d in ohlcv_data
            ]
            return response
            
        except ccxt.BadSymbol as e:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{symbol}' not found on {exchange_id}: {e}"
            )
        except ccxt.NetworkError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Network error connecting to {exchange_id}: {e}"
            )
        except ccxt.ExchangeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Exchange error from {exchange_id}: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred: {e}"
            )
        finally:
            await exchange.close()