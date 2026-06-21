"""
Practical example: Trading with live market data simulation
"""

import logging
import json
from datetime import datetime
from order_manager import OrderManager
from upstox_api import UpstoxAPI
from trend_analyzer import TrendAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def simulate_trading_session():
    """
    Simulate a complete trading session with order placement and management
    """
    print("\n" + "="*60)
    print("TRADING SESSION SIMULATION")
    print("="*60 + "\n")
    
    # Mock API and order manager
    api = UpstoxAPI("demo_key", "demo_secret", "demo_token")
    order_mgr = OrderManager(api)
    
    # Simulated market data and trading scenarios
    scenarios = [
        {
            "index": "NIFTY",
            "symbol": "NIFTY05MAY2411000CE",
            "entry_price": 150.00,
            "side": "BUY",
            "qty": 1,
            "current_prices": [150.50, 151.00, 151.50, 152.50]  # Price progression
        },
        {
            "index": "BANKNIFTY",
            "symbol": "BN05MAY2445000PE",
            "entry_price": 200.00,
            "side": "SELL",
            "qty": 1,
            "current_prices": [199.50, 199.00, 198.00, 197.50]
        },
        {
            "index": "FINNIFTY",
            "symbol": "FN05MAY2421000CE",
            "entry_price": 175.00,
            "side": "BUY",
            "qty": 1,
            "current_prices": [174.00, 173.00, 172.00]  # Hit SL
        }
    ]
    
    print("SCENARIO 1: Trade at Entry Price (Breakeven)")
    print("-" * 60)
    scenario = scenarios[0]
    
    # Place trade
    order = order_mgr.place_trade(
        symbol=scenario["symbol"],
        quantity=scenario["qty"],
        side=scenario["side"],
        entry_price=scenario["entry_price"]
    )
    
    if order:
        print("Trade Placed:")
        print(f"  Symbol: {order['symbol']}")
        print(f"  Side: {order['side']}")
        print(f"  Entry: INR{order['entry_price']:.2f}")
        print(f"  SL: INR{order['stop_loss']:.2f}")
        print(f"  Target: INR{order['target']:.2f}")
        print(f"  Order ID: {order['order_id']}\n")
    
    # Update P&L
    prices = {scenario["symbol"]: scenario["current_prices"][-1]}
    order_mgr.update_trade_pnl(prices)
    print(f"Current Price: {prices[scenario['symbol']]}")
    print(f"Current P&L: {order['pnl']} (Updated in live trading)\n")
    
    print("\nSCENARIO 2: Trade Hits Target")
    print("-" * 60)
    scenario = scenarios[1]
    
    # Place another trade
    order2 = order_mgr.place_trade(
        symbol=scenario["symbol"],
        quantity=scenario["qty"],
        side=scenario["side"],
        entry_price=scenario["entry_price"]
    )
    
    if order2:
        print("Trade Placed:")
        print(f"  Symbol: {order2['symbol']}")
        print(f"  Side: {order2['side']}")
        print(f"  Entry: INR{order2['entry_price']:.2f}")
        print(f"  Target: INR{order2['target']:.2f}\n")
        
        # Simulate hitting target
        final_price = scenario["current_prices"][-1]
        print(f"Price action: {' -> '.join(str(p) for p in scenario['current_prices'])}")
        print("Result: TARGET HIT\n")
        
        # Close trade
        order_mgr.close_trade(order2['order_id'], final_price)
        
        print(f"Trade Closed at {final_price}")
        print(f"  Final P&L: {order2.get('pnl', 'TBD')}\n")
    
    print("\nSCENARIO 3: Trade Hits Stop Loss")
    print("-" * 60)
    scenario = scenarios[2]
    
    # Place third trade
    order3 = order_mgr.place_trade(
        symbol=scenario["symbol"],
        quantity=scenario["qty"],
        side=scenario["side"],
        entry_price=scenario["entry_price"]
    )
    
    if order3:
        print("Trade Placed:")
        print(f"  Symbol: {order3['symbol']}")
        print(f"  Side: {order3['side']}")
        print(f"  Entry: INR{order3['entry_price']:.2f}")
        print(f"  SL: INR{order3['stop_loss']:.2f}\n")
        
        # Simulate hitting stop loss
        print(f"Price action: {' -> '.join(str(p) for p in scenario['current_prices'])}")
        print("Result: STOP LOSS HIT\n")
        
        # Close trade at SL
        final_price = scenario["current_prices"][-1]
        order_mgr.close_trade(order3['order_id'], final_price)
        
        print(f"Trade Closed at {final_price}")
        print(f"  Final P&L: {order3.get('pnl', 'TBD')}\n")
    
    # Print overall summary
    print("\n" + "="*60)
    print("TRADING SESSION SUMMARY")
    print("="*60 + "\n")
    
    summary = order_mgr.get_trade_summary()
    
    print("Performance Metrics:")
    print("-" * 60)
    for key, value in summary.items():
        if key in ['total_trades', 'winning_trades', 'losing_trades']:
            print(f"  {key:20s}: {value}")
    
    print("\nProfitability:")
    print("-" * 60)
    for key, value in summary.items():
        if key in ['win_rate', 'total_pnl', 'total_return']:
            if key == 'win_rate':
                print(f"  {key:20s}: {value}%")
            else:
                print(f"  {key:20s}: INR{value}")
    
    print("\nRisk Metrics:")
    print("-" * 60)
    for key, value in summary.items():
        if key in ['active_pnl', 'active_trades']:
            if 'pnl' in key:
                print(f"  {key:20s}: INR{value}")
            else:
                print(f"  {key:20s}: {value}")
    
    # Export results
    order_mgr.export_trades("simulation_trades.json")
    print("\nResults exported to 'simulation_trades.json'\n")


def analyze_multiple_timeframes():
    """
    Demonstrate multi-timeframe analysis
    """
    print("\n" + "="*60)
    print("MULTI-TIMEFRAME ANALYSIS EXAMPLE")
    print("="*60 + "\n")
    
    # Sample OHLC data
    import random
    random.seed(42)
    
    base_price = 50000
    periods = 100
    
    close_prices = []
    current = base_price
    for _ in range(periods):
        change = random.gauss(0, 100)
        current += change
        close_prices.append(current)
    
    ohlc_data = {
        "close": close_prices,
        "open": [p - 50 for p in close_prices],
        "high": [p + 100 for p in close_prices],
        "low": [p - 100 for p in close_prices]
    }
    
    # Analyze on different timeframes
    timeframes = {
        "5 min": "Short-term",
        "15 min": "Short-term",
        "30 min": "Short-term",
        "1 hour": "Medium-term",
        "2 hours": "Medium-term",
        "4 hours": "Medium-term"
    }
    
    print("NIFTY 50 - Multi-Timeframe Analysis")
    print("-" * 60)
    print(f"{'Timeframe':<12} {'Period':<15} {'Trend':<10} {'Confidence':<12}")
    print("-" * 60)
    
    bullish_count = 0
    bearish_count = 0
    
    for timeframe, period_type in timeframes.items():
        # Perform trend analysis
        analysis = TrendAnalyzer.analyze_trend(ohlc_data)
        trend = analysis.get('trend')
        confidence = analysis.get('confidence')
        
        trend_symbol = "UP" if trend == "BULLISH" else "DOWN" if trend == "BEARISH" else "NEUTRAL"
        
        print(f"{timeframe:<12} {period_type:<15} {trend:<10} {confidence:>6.2f}% {trend_symbol}")
        
        if trend == "BULLISH":
            bullish_count += 1
        elif trend == "BEARISH":
            bearish_count += 1
    
    print("-" * 60)
    
    # Overall signal
    print("\nOverall Signal Strength:")
    print("-" * 60)
    print(f"  Bullish timeframes: {bullish_count}/6")
    print(f"  Bearish timeframes: {bearish_count}/6")
    
    if bullish_count > bearish_count:
        signal = "STRONG BUY SIGNAL"
    elif bearish_count > bullish_count:
        signal = "STRONG SELL SIGNAL"
    else:
        signal = "NEUTRAL - NO CLEAR SIGNAL"
    
    print(f"\n  {signal}\n")


def demonstrate_risk_management():
    """
    Demonstrate risk management calculations
    """
    print("\n" + "="*60)
    print("RISK MANAGEMENT DEMONSTRATION")
    print("="*60 + "\n")
    
    api = UpstoxAPI("demo_key", "demo_secret", "demo_token")
    order_mgr = OrderManager(api)
    
    # Different entry prices and scenarios
    scenarios = [
        {"entry": 150.00, "side": "BUY", "label": "Scenario 1: BUY at 150"},
        {"entry": 200.00, "side": "BUY", "label": "Scenario 2: BUY at 200"},
        {"entry": 100.00, "side": "SELL", "label": "Scenario 3: SELL at 100"},
    ]
    
    print("Risk-Reward Analysis (SL: 1%, Target: 2%)")
    print("-" * 60)
    
    for scenario in scenarios:
        prices = order_mgr.calculate_order_prices(
            scenario["entry"],
            scenario["side"],
            sl_percent=1.0,
            target_percent=2.0
        )
        
        print(f"\n{scenario['label']}")
        print(f"  Entry:     INR{prices['entry']:.2f}")
        print(f"  Stop Loss: INR{prices['stop_loss']:.2f}")
        print(f"  Target:    INR{prices['target']:.2f}")
        
        if scenario['side'] == 'BUY':
            max_loss = prices['entry'] - prices['stop_loss']
            max_gain = prices['target'] - prices['entry']
        else:
            max_loss = prices['stop_loss'] - prices['entry']
            max_gain = prices['entry'] - prices['target']
        
        print(f"  Max Loss:  INR{max_loss:.2f}")
        print(f"  Max Gain:  INR{max_gain:.2f}")
        print(f"  R:R Ratio: 1:{max_gain/max_loss:.2f}")


def main():
    """Run all practical examples"""
    try:
        # Run simulations
        simulate_trading_session()
        analyze_multiple_timeframes()
        demonstrate_risk_management()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
