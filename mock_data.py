"""
Mock Market Data Generator for Testing
Simulates realistic OHLC data for testing trading bot logic without API access
"""

import random
from datetime import datetime, timedelta


def generate_mock_candles(symbol="TCS", num_candles=20, start_price=3500, volatility=2):
    """
    Generate realistic mock OHLC candles for testing
    
    Args:
        symbol: Instrument symbol
        num_candles: Number of candles to generate
        start_price: Starting price for the data
        volatility: Price volatility percentage
    
    Returns:
        dict with structure: {
            "candles": [
                {"open": 3500, "high": 3550, "low": 3480, "close": 3520, "volume": 100000},
                ...
            ],
            "timestamp": [datetime1, datetime2, ...],
            "symbol": "TCS"
        }
    """
    candles = []
    timestamps = []
    current_price = start_price
    current_time = datetime.now() - timedelta(minutes=num_candles * 5)  # 5-min candles
    
    for i in range(num_candles):
        # Simulate price movement
        change = current_price * (random.uniform(-volatility, volatility) / 100)
        open_price = current_price
        close_price = current_price + change
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.5) / 100)
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.5) / 100)
        volume = random.randint(50000, 500000)
        
        candles.append({
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        
        timestamps.append(current_time)
        current_price = close_price
        current_time += timedelta(minutes=5)
    
    return {
        "candles": candles,
        "timestamp": timestamps,
        "symbol": symbol
    }


def get_mock_market_data(instrument_key, interval, days=2):
    """
    Mock replacement for UpstoxAPI.get_market_data()
    
    Returns data in the same format as the real API
    """
    symbol = instrument_key.split("|")[-1][:3] if "|" in instrument_key else "NIFTY"
    
    # Simulate different volatility for different instruments
    volatility = 2.5 if "NIFTY" in symbol else 1.8
    
    # Generate candles based on interval
    if interval == "1minute":
        num_candles = 60 * days
    elif interval == "5minute":
        num_candles = 12 * 6 * days  # 72 per day
    elif interval == "15minute":
        num_candles = 24 * days
    elif interval == "30minute":
        num_candles = 12 * days
    elif interval == "60minute" or interval == "1hour":
        num_candles = 6 * days
    elif interval == "day":
        num_candles = 20  # 20 days of data
    else:
        num_candles = 20
    
    # Generate base price depending on instrument
    if "NIFTY" in symbol:
        base_price = 24000
    elif "BANKNIFTY" in symbol:
        base_price = 52000
    else:
        base_price = 3500
    
    data = generate_mock_candles(symbol, num_candles, base_price, volatility)
    
    # Format as list of OHLC values (matching real API format)
    return {
        "open": [c["open"] for c in data["candles"]],
        "high": [c["high"] for c in data["candles"]],
        "low": [c["low"] for c in data["candles"]],
        "close": [c["close"] for c in data["candles"]],
        "volume": [c["volume"] for c in data["candles"]],
        "timestamps": data["timestamp"],
        "symbol": data["symbol"]
    }


if __name__ == "__main__":
    # Test the mock data generator
    print("Testing Mock Data Generator\n")
    
    # Test 1: Nifty 50 5-minute candles
    print("=" * 50)
    print("NIFTY 50 - 5-minute candles")
    print("=" * 50)
    data = get_mock_market_data("NSE_INDEX|Nifty 50", "5minute", days=1)
    print(f"Generated {len(data['close'])} candles")
    print(f"Price range: {min(data['low']):.2f} - {max(data['high']):.2f}")
    print(f"Last 5 closes: {data['close'][-5:]}")
    print()
    
    # Test 2: TCS 15-minute candles
    print("=" * 50)
    print("TCS - 15-minute candles")
    print("=" * 50)
    data = get_mock_market_data("NSE_EQ|INE002A01018", "15minute", days=1)
    print(f"Generated {len(data['close'])} candles")
    print(f"Price range: {min(data['low']):.2f} - {max(data['high']):.2f}")
    print(f"Last 5 closes: {data['close'][-5:]}")
    print()
    
    # Test 3: INFY Daily candles
    print("=" * 50)
    print("INFY - Daily candles")
    print("=" * 50)
    data = get_mock_market_data("NSE_EQ|INE009A01021", "day", days=20)
    print(f"Generated {len(data['close'])} candles")
    print(f"Price range: {min(data['low']):.2f} - {max(data['high']):.2f}")
    print(f"Last 5 closes: {data['close'][-5:]}")
