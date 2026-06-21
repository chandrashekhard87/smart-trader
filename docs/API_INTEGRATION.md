# API Integration Guide

## Upstox API Setup

### Step 1: Create Upstox Developer Account

1. Go to [Upstox Developer Portal](https://upstox.com/developer/api/)
2. Sign up with your email
3. Verify your email
4. Complete KYC if required

### Step 2: Create an Application

1. Log in to developer portal
2. Go to "My Apps" section
3. Click "Create New Application"
4. Fill in application details:
   - **App Name**: NSE Option Chain Trading Bot
   - **Purpose**: Automated trading
   - **Redirect URI**: `http://localhost:8080/callback`
5. Accept terms and submit
6. You'll receive:
   - **API Key**
   - **API Secret**

### Step 3: Configure Credentials

Update `config.py`:

```python
UPSTOX_API_KEY = "your_api_key_here"
UPSTOX_API_SECRET = "your_api_secret_here"
UPSTOX_REDIRECT_URL = "http://localhost:8080/callback"
```

### Step 4: Get Access Token

Run authentication script:

```bash
python auth.py
```

This will:
1. Open Upstox login in browser
2. Ask for authorization
3. Generate access token
4. Save to `access_token.txt`

## API Endpoints Reference

### Market Data

```python
# Get OHLC data
market_data = upstox_api.get_market_data(
    instrument_key="NSE_INDEX|Nifty 50",
    interval="5minute"  # 5minute, 15minute, 30minute, 60minute, 240minute, daily
)
```

**Response:**
```json
{
  "data": {
    "ohlc": {
      "open": 50000.00,
      "high": 50100.00,
      "low": 49900.00,
      "close": 50050.00
    },
    "ltp": 50050.00,
    "volume": 1000000
  }
}
```

### Option Chain

```python
# Get option chain data
option_chain = upstox_api.get_option_chain(
    index="NIFTY",
    expiry_date="05MAY23"
)
```

### Order Management

#### Place Regular Order

```python
order = upstox_api.place_order(
    symbol="NIFTY05MAY2411000CE",
    quantity=1,
    side="BUY",
    order_type="MARKET",
    product="MIS"
)
```

#### Place Bracket Order (with SL & Target)

```python
order = upstox_api.place_bracket_order(
    symbol="NIFTY05MAY2411000CE",
    quantity=1,
    side="BUY",
    price=150.00,
    sl_price=148.50,
    target_price=152.00,
    product="MIS"
)
```

**Response:**
```json
{
  "data": {
    "order_id": "12345678",
    "status": "PENDING",
    "exchange": "NFO"
  }
}
```

#### Cancel Order

```python
success = upstox_api.cancel_order(order_id="12345678")
```

### Portfolio

#### Get Positions

```python
positions = upstox_api.get_positions()
```

**Response:**
```json
{
  "data": {
    "positions": [
      {
        "exchange": "NFO",
        "symbol": "NIFTY05MAY2411000CE",
        "quantity": 1,
        "average_price": 150.00,
        "current_price": 151.50,
        "pnl": 150.00
      }
    ]
  }
}
```

#### Get Order History

```python
orders = upstox_api.get_orders()
```

## Instrument Keys Reference

### Index Options

| Index | Instrument Key |
|-------|----------------|
| NIFTY | NSE_INDEX\|Nifty 50 |
| BANKNIFTY | NSE_INDEX\|Nifty Bank |
| FINNIFTY | NSE_INDEX\|Nifty Fin Service |
| MIDCPNIFTY | NSE_INDEX\|Nifty Midcap 50 |

### Option Symbol Format

```
{INDEX}{EXPIRY_DATE}{STRIKE}{TYPE}
```

Example: `NIFTY05MAY2411000CE`
- NIFTY: Index
- 05MAY24: Expiry date (DD MMM YY)
- 11000: Strike price
- CE: Call/Put

## Time Intervals

| Interval | Code |
|----------|------|
| 5 Minutes | 5minute |
| 15 Minutes | 15minute |
| 30 Minutes | 30minute |
| 1 Hour | 60minute |
| 2 Hours | 120minute |
| 4 Hours | 240minute |
| Daily | daily |

## Order Types

```python
# Market Order
order_type = "MARKET"
price = None  # Not required

# Limit Order
order_type = "LIMIT"
price = 150.00  # Required
```

## Product Types

```python
product = "MIS"   # Margin Intraday Square Off
product = "CNC"   # Cash & Carry (for delivery)
```

## Error Handling

```python
import logging

logger = logging.getLogger(__name__)

try:
    market_data = upstox_api.get_market_data("NSE_INDEX|Nifty 50")
    if not market_data:
        logger.error("Failed to fetch market data")
except Exception as e:
    logger.error(f"API Error: {str(e)}")
```

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Unauthorized | Check API credentials |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check instrument key |
| 429 | Rate Limited | Wait before making more requests |
| 500 | Server Error | Retry after delay |

## Rate Limiting

- API rate limit: ~1000 requests per minute
- Implement backoff strategy for rate limit errors
- Space out API calls appropriately

## Best Practices

### 1. Error Handling

```python
def safe_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        return None
```

### 2. Caching

```python
from datetime import datetime, timedelta

last_fetch = None
cached_data = None
cache_duration = 5  # minutes

def get_market_data_cached(symbol):
    global last_fetch, cached_data
    
    if cached_data and (datetime.now() - last_fetch).seconds < cache_duration * 60:
        return cached_data
    
    cached_data = upstox_api.get_market_data(symbol)
    last_fetch = datetime.now()
    return cached_data
```

### 3. Token Refresh

```python
from datetime import datetime, timedelta

token_created = datetime.now()
token_expiry = 24  # hours

if (datetime.now() - token_created).seconds > token_expiry * 3600:
    # Refresh token
    new_token = auth.get_access_token(auth_code)
    upstox_api.set_access_token(new_token)
```

## Testing API Connection

```python
from upstox_api import UpstoxAPI

# Initialize API
api = UpstoxAPI(api_key, api_secret, access_token)

# Test connection
try:
    data = api.get_market_data("NSE_INDEX|Nifty 50")
    if data:
        print("✓ API connection successful")
    else:
        print("✗ API connection failed")
except Exception as e:
    print(f"✗ Error: {str(e)}")
```

## Webhook Integration (Optional)

For real-time trade confirmations, implement webhooks:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/trade-update', methods=['POST'])
def trade_update():
    data = request.json
    # Process trade update
    logger.info(f"Trade Update: {data}")
    return {'status': 'success'}

if __name__ == '__main__':
    app.run(port=8080)
```

## Security Best Practices

1. **Never hardcode credentials**
   ```python
   # Bad ❌
   UPSTOX_API_KEY = "abc123"
   
   # Good ✓
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   UPSTOX_API_KEY = os.getenv("UPSTOX_API_KEY")
   ```

2. **Use environment variables**
   ```bash
   # .env file
   UPSTOX_API_KEY=your_key_here
   UPSTOX_API_SECRET=your_secret_here
   UPSTOX_ACCESS_TOKEN=your_token_here
   ```

3. **Regenerate tokens periodically**
   - Access tokens expire after 24 hours
   - Implement automatic refresh mechanism

4. **Enable two-factor authentication** on Upstox account

5. **IP whitelist** in Upstox settings

## Monitoring API Performance

```python
import time

start_time = time.time()
market_data = upstox_api.get_market_data(symbol)
elapsed_time = time.time() - start_time

logger.info(f"API call took {elapsed_time:.2f} seconds")

# Monitor latency
if elapsed_time > 1.0:
    logger.warning(f"High latency detected: {elapsed_time:.2f}s")
```

## Support & Resources

- **Official Docs**: https://upstox.com/developer/api/
- **Community**: https://community.upstox.com/
- **Support Email**: support@upstox.com
- **Status Page**: https://status.upstox.com/

## Next Steps

1. Get API credentials from Upstox
2. Update config.py with credentials
3. Run auth.py to get access token
4. Test API connection with examples.py
5. Start trading_bot.py for live trading

---

**Last Updated**: May 5, 2026
**API Version**: v2
