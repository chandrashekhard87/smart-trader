#!/usr/bin/env python3
"""
Test script to check Upstox API market data
"""

from upstox_api import UpstoxAPI
from config import UPSTOX_API_KEY, UPSTOX_API_SECRET, ACCESS_TOKEN, UPSTOX_API_BASE_URL

def test_api():
    # Initialize API (sandbox mode)
    api = UpstoxAPI(
        UPSTOX_API_KEY,
        UPSTOX_API_SECRET,
        ACCESS_TOKEN,
        use_sandbox=True,
        base_url=UPSTOX_API_BASE_URL,
    )

    # Test market data fetch
    symbol = "NSE_INDEX|Nifty 50"
    interval = "30minute"  # Sandbox v2 supports: 1minute, 30minute, day, week, month

    print(f"Testing API call for {symbol} with interval {interval}")

    data = api.get_market_data(symbol, interval)

    if data:
        print("SUCCESS: API call returned data")
        print(f"Data keys: {list(data.keys())}")
        print(f"Candles: {len(data['close'])}")
        print(f"Latest OHLC:")
        print(f"  Open:  {data['open'][-1]:.2f}")
        print(f"  High:  {data['high'][-1]:.2f}")
        print(f"  Low:   {data['low'][-1]:.2f}")
        print(f"  Close: {data['close'][-1]:.2f}")
        print(f"  Volume: {data['volume'][-1]}")
        print(f"\nPrice range: {min(data['low']):.2f} - {max(data['high']):.2f}")
    else:
        print("FAILED: API call returned None")

if __name__ == "__main__":
    test_api()