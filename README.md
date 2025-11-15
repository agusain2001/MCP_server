# MCP Server (Crypto Market Data Provider)

Below is an organized and polished version of your project documentation. You can edit or expand it anytime.

---

## Overview

This server provides real-time and historical cryptocurrency market data using FastAPI and CCXT. It is fully asynchronous and built to support high-frequency access from more than 100 major exchanges. The system includes REST endpoints, a WebSocket feed, caching, and a complete test suite.

---

## Key Features

* **FastAPI Backend:** Async-first design with automatic API docs.
* **CCXT Integration:** Unified access to exchanges like Binance, Coinbase, and Kraken.
* **Real-time Price API:** Fetch latest ticker values.
* **Historical OHLCV API:** Retrieve open-high-low-close-volume candles.
* **WebSocket Updates:** Near real-time price streaming through polling.
* **In-memory TTL Caching:** Improves response speed and reduces rate limits.
* **Error Handling:** Clean JSON errors for invalid symbols or network issues.
* **Validated Models:** All data shapes enforced using Pydantic.
* **Test Suite:** Covers both data logic and API behavior.

---

## Architecture & Design

### FastAPI Choice

FastAPI works well for I/O-heavy API calls. It provides validation through Pydantic and comes with interactive docs.

### Data Layer

The `MarketDataProvider` in `data_provider.py` manages CCXT, caching, and error handling. Endpoints remain lightweight.

### Caching

A simple `SimpleTTLCache` stores ticker responses for 10 seconds. This keeps responses fast and avoids triggering exchange rate limits.

### Error Handling

Exchange-specific CCXT errors are converted into relevant HTTP exceptions (400, 404, 503, etc.) to avoid crashes.

### WebSocket Strategy

Instead of handling exchange WebSockets, the server polls ticker data at a selected interval and streams the results.

### Limitations

* Cache is in-memory and not shared across workers.
* WebSocket updates are near real-time, not true streaming.
* No authentication is included by default.

---

## Project Structure

```
.
├── main.py
├── data_provider.py
├── caching.py
├── models.py
├── requirements.txt
├── test_main.py
└── test_data_provider.py
```

---

## Installation

### 1. Clone or create project files

### 2. Create a virtual environment

```
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

---

## Running the Server

Start using uvicorn:

```
uvicorn main:app --reload
```

### API Documentation

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Tests

Run the full test suite:

```
pytest
```

---

## Endpoints

### 1. Real-time Price Ticker

```
GET /price/{exchange_id}/{symbol}
```

Example:

```
http://127.0.0.1:8000/price/binance/BTC/USDT
```

### 2. Historical OHLCV

```
GET /historical/{exchange_id}/{symbol}
```

Query params:

* timeframe: default 1d
* since: start timestamp (ms)
* limit: default 100

Example:

```
http://127.0.0.1:8000/historical/coinbase/ETH/USD?timeframe=1h&limit=50
```

### 3. WebSocket Streaming

```
WS /ws/{exchange_id}/{symbol}
```

Query param:

* poll_interval (default 5s)

Example:

```
ws://127.0.0.1:8000/ws/kraken/XBT/EUR?poll_interval=2
```
