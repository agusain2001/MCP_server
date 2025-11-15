# MCP Server (Crypto Market Data Provider)

This project delivers a unified API layer for cryptocurrency market data using FastAPI and ccxt. It provides both REST and WebSocket interfaces, supports over 100 exchanges, and is designed for performance, clarity, and resilience.

## Core Features

### FastAPI Backend

* Fully asynchronous.
* High-performance endpoints for real-time usage.

### Unified CCXT Integration

* A single `MarketDataProvider` class handles all ccxt logic.
* Dynamically creates exchange instances only when needed.

### REST API

* Health checks
* Exchange list
* Real-time tickers
* Historical OHLCV data

### WebSocket API

* Near real-time ticker updates
* Uses internal polling loop
* Works seamlessly with existing caching

### Dynamic Caching

* Custom `SimpleTTLCache`
* Applied mainly to high-frequency ticker requests
* TTL-based in-memory storage with max-size control

### IP-Based Rate Limiting

* Custom token bucket implementation
* Per-client IP buckets
* Configurable via environment variables

### Structured Logging

* JSON and text formats
* Supports production or development use

### Centralized Configuration

* All settings managed via `pydantic-settings`
* Supports `.env` or environment variables
* All keys must be prefixed with `MCP_`

---

## Project Architecture

The server is built on a clean separation between API routes and business logic.

### 1. Core Logic (data_provider.py)

* `MarketDataProvider` is the central component.
* Created once in `main.py` and reused.
* Builds ccxt exchange instances on demand.
* Handles validation, caching, and data normalization.

### 2. Error Handling

* Catches ccxt exceptions such as `BadSymbol`, `NetworkError`, and `ExchangeError`.
* Converts them into FastAPI `HTTPException` responses.
* Ensures stable and predictable API responses.

### 3. Caching Strategy

* Only real-time tickers are cached.
* Historical OHLCV data is not cached due to variable combinations.
* `SimpleTTLCache` provides TTL expiration and size-based eviction.

### 4. Rate Limiting

* Token bucket algorithm.
* Per-IP counters.
* In-memory storage.
* Prevents abuse and protects upstream exchanges.

### 5. WebSocket Strategy

* Polls the provider on an interval for ticker updates.
* Pushes updates to connected clients.
* Simpler and more predictable than direct exchange WebSockets.

### 6. Configuration

* Managed by `config.py` via `pydantic-settings`.
* Supports loading from `.env`.
* All config keys start with `MCP_`.

### 7. Logging

* Defined in `logger.py`.
* JSON logs for production, text logs for development.

---

## Assumptions & Limitations

### Single-Worker Deployment

* Cache and rate limiter live in memory.
* Multi-worker setups require Redis or similar external storage.

### IP as Identifier

* Assumes valid client IPs.
* Behind proxies, must enable `--proxy-headers` and configure forwarding.

### WebSocket Polling

* Near real-time, not true streaming.
* Minimum 1-second interval.
* Suitable for dashboards, not HFT.

---

## Setup & Installation

### Clone the Repository

```
git clone https://github.com/your-username/mcp_server.git
cd mcp_server
```

### Create and Activate Virtual Environment

```
python -m venv venv
source venv/bin/activate     # Linux/Mac
venv\Scripts\activate        # Windows
```

### Install Dependencies

```
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file or export variables.
All must be prefixed with `MCP_`.

Example `.env`:

```
MCP_TICKER_CACHE_TTL=15
MCP_RATE_LIMIT_REQUESTS=120
MCP_RATE_LIMIT_PERIOD=60
MCP_LOG_LEVEL=DEBUG
MCP_LOG_FORMAT=text
```

---

## Running the Server

```
uvicorn main:app --reload
```

Access the API docs:

* Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Tests

```
pytest
```
