# NSE Option Chain Trading Bot

A comprehensive Python-based automated trading system for NSE (National Stock Exchange) option chain trading using the Upstox API. The bot analyzes trends across multiple timeframes and executes trades with automated stop loss and target placement.

## Features

- **Multi-Timeframe Trend Analysis**: Analyzes trends in 5/15/30-minute and 1/2/4-hour intervals
- **Technical Indicators**: Uses SMA, EMA, RSI, MACD, and Bollinger Bands for trend confirmation
- **Automated Order Placement**: Places bracket orders with automatic stop loss and target calculation
- **Risk Management**: Implements daily trade limits, position tracking, and P&L monitoring
- **Option Chain Support**: Trades across multiple indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY)
- **Backtesting**: Historical strategy testing capabilities
- **Notifications**: Telegram alerts for trade execution and P&L updates
- **Trade Logging**: Comprehensive trade history and performance metrics

## Project Structure

```
stock-market-app/
├── config.py              # Configuration and settings
├── upstox_api.py          # Upstox API integration
├── auth.py                # OAuth authentication
├── trend_analyzer.py      # Technical analysis and trend detection
├── order_manager.py       # Order placement and trade management
├── trading_bot.py         # Main trading bot logic
├── backtest.py            # Backtesting module
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Upstox API credentials (API Key & Secret)

### Setup

1. **Clone the repository**
```bash
cd stock-market-app
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API credentials**

Edit `config.py` and add your Upstox API credentials:
```python
UPSTOX_API_KEY = "YOUR_API_KEY"
UPSTOX_API_SECRET = "YOUR_API_SECRET"
UPSTOX_REDIRECT_URL = "http://localhost:8080/callback"
```

4. **Get Access Token**

Run the authentication script to get an access token:
```bash
python auth.py
```

This will:
- Open your browser for Upstox login
- Generate an authorization code
- Exchange it for an access token
- Save the token to `access_token.txt`

## Usage

### Running the Trading Bot

```bash
python trading_bot.py
```

The bot will:
1. Connect to Upstox API
2. Monitor indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY)
3. Analyze trends across multiple timeframes
4. Place trades when strong signals are detected
5. Manage positions with automatic stop loss and targets
6. Update trade P&L in real-time
7. Log all activities

### Configuration

Edit `config.py` to customize:

```python
# Trading Indices
INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]

# Timeframes (in minutes)
OPTION_CHAIN_INTERVALS = [5, 15, 30, 60, 120, 240]

# Risk Management
SL_PERCENTAGE = 1.0          # Stop loss %
TARGET_PERCENTAGE = 2.0      # Target profit %
MAX_LOSS_PER_TRADE = 1000   # Max loss per trade
MAX_TRADES_PER_DAY = 5       # Daily trade limit

# Trading Hours
TRADING_START_TIME = "09:15"
TRADING_END_TIME = "15:30"

# Notifications
ENABLE_NOTIFICATIONS = True
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
```

### Running Backtest

```bash
python backtest.py
```

Requires a CSV file with historical OHLC data (format: timestamp, open, high, low, close, volume).

## API Reference

### TrendAnalyzer

```python
from trend_analyzer import TrendAnalyzer

# Analyze trend with technical indicators
analysis = TrendAnalyzer.analyze_trend(ohlc_data)

# Get entry, SL, and target prices
prices = TrendAnalyzer.get_entry_exit_points(ohlc_data, risk_reward_ratio=2.0)
```

### OrderManager

```python
from order_manager import OrderManager

# Place a trade with SL and target
order = order_manager.place_trade(
    symbol="NIFTY05MAY2411000CE",
    quantity=1,
    side="BUY",
    entry_price=150.50
)

# Get trade summary
summary = order_manager.get_trade_summary()
```

### UpstoxAPI

```python
from upstox_api import UpstoxAPI

# Get market data
market_data = upstox_api.get_market_data("NSE_INDEX|Nifty 50", "5minute")

# Place bracket order
order = upstox_api.place_bracket_order(
    symbol="NIFTY05MAY2411000CE",
    quantity=1,
    side="BUY",
    price=150.50,
    sl_price=149.00,
    target_price=152.50
)

# Get positions
positions = upstox_api.get_positions()

# Get orders
orders = upstox_api.get_orders()

# Cancel order
upstox_api.cancel_order(order_id)
```

## Technical Indicators

### Implemented Indicators

1. **SMA** (Simple Moving Average): 9, 20, 50 periods
2. **EMA** (Exponential Moving Average): With configurable periods
3. **RSI** (Relative Strength Index): 14 period with overbought (>70) / oversold (<30) levels
4. **MACD**: 12/26/9 configuration with signal line
5. **Bollinger Bands**: 20 period with 2 standard deviations
6. **ATR** (Average True Range): 14 period for volatility measurement

## Trading Logic

### Trend Detection

The bot uses multi-timeframe analysis:
- Analyzes 6 different timeframes (5m, 15m, 30m, 1h, 2h, 4h)
- Combines signals from all timeframes
- Generates BUY/SELL signals when multiple timeframes align
- Calculates confidence score based on signal strength

### Entry & Exit

1. **Entry**: Triggered by strong multi-timeframe trend confirmation
2. **Exit**: Automatic closure at target or stop loss
3. **Risk Management**: Position sizing based on risk parameters

## Risk Management Features

- **Daily Trade Limit**: Maximum 5 trades per day (configurable)
- **Stop Loss**: Automatic SL placement at entry -1% (configurable)
- **Target**: Automatic target at entry +2% (configurable)
- **Trade Cooldown**: 5-minute cooldown between trades on same instrument
- **Trading Hours**: Operates only during market hours (09:15 - 15:30)

## Output Files

The bot generates:

1. **trades_history.json**: Detailed trade execution records
2. **trading_summary.json**: Performance metrics
3. **backtest_results.json**: Backtest analysis results

### Sample Output

```json
{
  "total_trades": 12,
  "active_trades": 1,
  "closed_trades": 11,
  "winning_trades": 8,
  "losing_trades": 3,
  "win_rate": 72.73,
  "total_pnl": 5400.50,
  "active_pnl": 250.00,
  "total_return": 5650.50
}
```

## Notifications

Enable Telegram notifications for trade alerts:

1. Create a Telegram bot and get the bot token
2. Get your Telegram chat ID
3. Update config.py with credentials
4. Bot will send notifications for:
   - Trade placement
   - Trade closure
   - P&L updates

## Troubleshooting

### API Connection Issues
- Verify API credentials in config.py
- Check internet connection
- Ensure access token is valid

### No Signals Generated
- Check if market is open (09:15 - 15:30)
- Verify market data is being fetched
- Adjust confidence threshold in config

### Authentication Failures
- Run `python auth.py` to refresh access token
- Check API key and secret
- Ensure redirect URL matches Upstox settings

## Performance Monitoring

Monitor bot performance using:

```python
# Get trade summary
summary = bot.order_manager.get_trade_summary()

# Export trades
bot.order_manager.export_trades("my_trades.json")

# View active positions
positions = bot.upstox_api.get_positions()
```

## Disclaimer

This trading bot is provided as-is for educational and research purposes. Use at your own risk. 

- Paper trading is recommended before live trading
- Past performance does not guarantee future results
- Always implement proper risk management
- Regularly monitor bot performance
- Be prepared to manually intervene if needed

## Support & Documentation

- Upstox API Docs: https://upstox.com/developer/api/
- Trading Strategy Research: https://school.stockcharts.com/

## License

MIT License - Feel free to modify and distribute

## Author

Created for NSE option chain automated trading
