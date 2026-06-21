"""
Example usage of the trading bot with mock data
"""

import logging
from datetime import datetime, timedelta
import random

from trading_bot import OptionChainTradingBot
from trend_analyzer import TrendAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_mock_ohlc_data(base_price: float = 50000, periods: int = 100) -> dict:
    """Generate mock OHLC data for testing"""
    ohlc = {
        "open": [],
        "high": [],
        "low": [],
        "close": []
    }
    
    current_price = base_price
    for _ in range(periods):
        # Random walk
        change = random.gauss(0, 100)
        open_price = current_price
        close_price = current_price + change
        
        high_price = max(open_price, close_price) + abs(random.gauss(0, 50))
        low_price = min(open_price, close_price) - abs(random.gauss(0, 50))
        
        ohlc["open"].append(open_price)
        ohlc["high"].append(high_price)
        ohlc["low"].append(low_price)
        ohlc["close"].append(close_price)
        
        current_price = close_price
    
    return ohlc


def example_trend_analysis():
    """Example: Analyze trends using mock data"""
    print("\n=== Example 1: Trend Analysis ===\n")
    
    # Generate mock data
    mock_data = generate_mock_ohlc_data(base_price=50000, periods=100)
    
    # Analyze trend
    analysis = TrendAnalyzer.analyze_trend(mock_data)
    
    print(f"Trend: {analysis.get('trend')}")
    print(f"Confidence: {analysis.get('confidence')}%")
    print(f"Current Price: {analysis.get('current_price')}")
    print(f"SMA 9: {analysis.get('sma_9')}")
    print(f"SMA 20: {analysis.get('sma_20')}")
    print(f"RSI: {analysis.get('rsi')}")
    print(f"MACD: {analysis.get('macd')}")


def example_entry_exit_calculation():
    """Example: Calculate entry, SL, and target prices"""
    print("\n=== Example 2: Entry & Exit Points ===\n")
    
    # Generate mock data
    mock_data = generate_mock_ohlc_data(base_price=50000, periods=50)
    
    # Get entry and exit points
    prices = TrendAnalyzer.get_entry_exit_points(mock_data, risk_reward_ratio=2.0)
    
    if prices:
        print(f"Entry Price: {prices.get('entry')}")
        print(f"Stop Loss: {prices.get('stop_loss')}")
        print(f"Target: {prices.get('target')}")
        print(f"ATR: {prices.get('atr')}")
    else:
        print("Could not calculate entry/exit points")


def example_technical_indicators():
    """Example: Calculate various technical indicators"""
    print("\n=== Example 3: Technical Indicators ===\n")
    
    # Generate mock data
    mock_data = generate_mock_ohlc_data(base_price=50000, periods=100)
    close_prices = mock_data["close"]
    
    # SMA
    sma_20 = TrendAnalyzer.calculate_sma(close_prices, 20)
    print(f"SMA(20): {sma_20[-1]:.2f}")
    
    # EMA
    ema_12 = TrendAnalyzer.calculate_ema(close_prices, 12)
    print(f"EMA(12): {ema_12[-1]:.2f}")
    
    # RSI
    rsi = TrendAnalyzer.calculate_rsi(close_prices, 14)
    print(f"RSI(14): {rsi:.2f}")
    
    # MACD
    macd = TrendAnalyzer.calculate_macd(close_prices)
    print(f"MACD Line: {macd['macd']:.4f}")
    print(f"Signal Line: {macd['signal']:.4f}")
    print(f"Histogram: {macd['histogram']:.4f}")
    
    # Bollinger Bands
    bb = TrendAnalyzer.calculate_bollinger_bands(close_prices, 20, 2)
    print(f"BB Upper: {bb['upper']:.2f}")
    print(f"BB Middle: {bb['middle']:.2f}")
    print(f"BB Lower: {bb['lower']:.2f}")
    print(f"Current Price: {bb['current']:.2f}")
    
    # ATR
    atr = TrendAnalyzer.calculate_atr(
        mock_data["high"],
        mock_data["low"],
        close_prices,
        14
    )
    print(f"ATR(14): {atr:.2f}")


def example_order_management():
    """Example: Order management and P&L calculation"""
    print("\n=== Example 4: Order Management ===\n")
    
    from order_manager import OrderManager
    from upstox_api import UpstoxAPI
    
    # Create mock API
    api = UpstoxAPI("mock_key", "mock_secret", "mock_token")
    
    # Create order manager
    order_mgr = OrderManager(api)
    
    # Calculate order prices
    prices = order_mgr.calculate_order_prices(
        entry_price=150.50,
        side="BUY",
        sl_percent=1.0,
        target_percent=2.0
    )
    
    print(f"Entry: {prices['entry']}")
    print(f"Stop Loss: {prices['stop_loss']}")
    print(f"Target: {prices['target']}")
    print(f"Max Risk: {prices['entry'] - prices['stop_loss']:.2f}")
    print(f"Max Reward: {prices['target'] - prices['entry']:.2f}")
    print(f"Risk:Reward Ratio: {(prices['target'] - prices['entry']) / (prices['entry'] - prices['stop_loss']):.2f}")
    
    # Update P&L
    current_prices = {"NIFTY05MAY2411000CE": 152.00}
    order_mgr.update_trade_pnl(current_prices)
    
    print("\nTrade Summary:")
    summary = order_mgr.get_trade_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")


def example_multi_timeframe_analysis():
    """Example: Multi-timeframe trend analysis"""
    print("\n=== Example 5: Multi-Timeframe Analysis ===\n")
    
    intervals = [5, 15, 30, 60, 120, 240]
    
    print("Timeframe | Trend | Confidence | Price")
    print("-" * 45)
    
    for interval in intervals:
        # Generate mock data for each interval
        mock_data = generate_mock_ohlc_data(
            base_price=50000,
            periods=100
        )
        
        analysis = TrendAnalyzer.analyze_trend(mock_data)
        
        trend = analysis.get('trend')
        confidence = analysis.get('confidence')
        price = analysis.get('current_price')
        
        print(f"{interval:3d} min   | {trend:8s} | {confidence:6.2f}%  | {price:8.2f}")


def run_all_examples():
    """Run all examples"""
    try:
        example_technical_indicators()
        example_trend_analysis()
        example_entry_exit_calculation()
        example_order_management()
        example_multi_timeframe_analysis()
        
        print("\n=== All Examples Completed Successfully ===\n")
        
    except Exception as e:
        logger.error(f"Error running examples: {str(e)}")


if __name__ == "__main__":
    run_all_examples()
