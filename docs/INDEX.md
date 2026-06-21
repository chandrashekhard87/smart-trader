# NSE Option Chain Trading Bot - Project Index

## 📚 Documentation Files

### Quick References
- **[QUICKSTART.md](QUICKSTART.md)** - Start here! 5-minute setup guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview
- **[README.md](README.md)** - Comprehensive documentation

### Technical References
- **[API_INTEGRATION.md](API_INTEGRATION.md)** - Upstox API guide & reference

## 🐍 Python Modules

### Core Trading Logic
| Module | Purpose | Key Classes |
|--------|---------|-------------|
| [trading_bot.py](trading_bot.py) | Main bot logic | `OptionChainTradingBot` |
| [trend_analyzer.py](trend_analyzer.py) | Technical analysis | `TrendAnalyzer`, `Trend` |
| [order_manager.py](order_manager.py) | Order management | `OrderManager` |
| [upstox_api.py](upstox_api.py) | API integration | `UpstoxAPI` |

### Utilities
| Module | Purpose | Key Functions |
|--------|---------|-------------|
| [auth.py](auth.py) | Authentication | `UpstoxAuth`, `get_upstox_access_token()` |
| [config.py](config.py) | Configuration | Settings & parameters |
| [backtest.py](backtest.py) | Backtesting | `Backtest` class |

### Examples & Demos
| Module | Purpose | Shows |
|--------|---------|--------|
| [examples.py](examples.py) | Code examples | Technical indicators, trends |
| [practical_example.py](practical_example.py) | Real scenarios | Trading session simulation |
| [setup_validation.py](setup_validation.py) | Setup checker | Environment validation |

## 🚀 Getting Started

```bash
# 1. Setup
python setup_validation.py

# 2. Install
pip install -r requirements.txt

# 3. Configure
# Edit config.py with your API credentials

# 4. Authenticate
python auth.py

# 5. Test
python examples.py
python practical_example.py

# 6. Trade
python trading_bot.py
```

## 📋 Configuration

Edit [config.py](config.py) to customize:

```python
# API Credentials
UPSTOX_API_KEY = "your_key"
UPSTOX_API_SECRET = "your_secret"

# Indices
INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]

# Intervals
OPTION_CHAIN_INTERVALS = [5, 15, 30, 60, 120, 240]  # minutes

# Risk Settings
SL_PERCENTAGE = 1.0
TARGET_PERCENTAGE = 2.0
MAX_TRADES_PER_DAY = 5

# Trading Hours
TRADING_START_TIME = "09:15"
TRADING_END_TIME = "15:30"
```

## 💻 Code Examples

### Start Trading Bot
```python
from trading_bot import OptionChainTradingBot
from config import UPSTOX_API_KEY, UPSTOX_API_SECRET

bot = OptionChainTradingBot(
    UPSTOX_API_KEY,
    UPSTOX_API_SECRET,
    access_token="your_token"
)
bot.start(update_interval=60)  # Updates every 60 seconds
```

### Analyze Trends
```python
from trend_analyzer import TrendAnalyzer

analysis = TrendAnalyzer.analyze_trend(ohlc_data)
print(f"Trend: {analysis['trend']}")
print(f"Confidence: {analysis['confidence']}%")
```

### Place Trade
```python
from order_manager import OrderManager
from upstox_api import UpstoxAPI

api = UpstoxAPI(key, secret, token)
mgr = OrderManager(api)

order = mgr.place_trade(
    symbol="NIFTY05MAY2411000CE",
    quantity=1,
    side="BUY",
    entry_price=150.00
)
```

### Backtest Strategy
```python
from backtest import Backtest

backtest = Backtest(initial_capital=100000)
df = backtest.load_historical_data("data.csv")
signals = backtest.generate_signals(df)
results = backtest.backtest_strategy(signals)
```

## 🎯 Key Features

### ✅ Multi-Timeframe Analysis
- 6 different timeframes (5m, 15m, 30m, 1h, 2h, 4h)
- Combines signals from all timeframes
- Confidence scoring

### ✅ Technical Indicators
- SMA (9, 20, 50 periods)
- EMA
- RSI (14 period)
- MACD
- Bollinger Bands
- ATR

### ✅ Automated Trading
- Bracket order placement
- Automatic SL & TP calculation
- P&L tracking
- Position management

### ✅ Risk Management
- Daily trade limits
- Max loss per trade
- Trade cooldown periods
- Trading hours enforcement

### ✅ Reporting
- Trade history export
- Performance metrics
- P&L summaries
- Backtesting results

## 📊 Trend Analysis Algorithm

1. **Data Fetching**: Get OHLC data for multiple timeframes
2. **Indicators**: Calculate SMA, EMA, RSI, MACD, BB, ATR
3. **Signal Generation**: Create signals per timeframe
4. **Signal Combining**: Merge multi-timeframe signals
5. **Confidence Scoring**: Rate signal strength
6. **Order Placement**: Execute trade if conditions met

## 🔄 Order Flow

```
Market Signal
    ↓
Trend Analysis (6 timeframes)
    ↓
Signal Confirmation
    ↓
Entry Price Calculation
    ↓
SL & TP Calculation
    ↓
Place Bracket Order
    ↓
Monitor Position
    ↓
Exit (SL/TP/Time)
    ↓
Record Trade
    ↓
Update Summary
```

## 📈 Trend Detection Rules

### BULLISH Signal
- SMA(9) > SMA(20)
- SMA(20) > SMA(50)
- RSI > 50
- MACD > Signal
- Price > Lower BB

### BEARISH Signal
- SMA(9) < SMA(20)
- SMA(20) < SMA(50)
- RSI < 50
- MACD < Signal
- Price < Upper BB

## 🧪 Testing

### Run Examples
```bash
python examples.py
```
Shows technical indicators, trend analysis, entry/exit points

### Run Practical Examples
```bash
python practical_example.py
```
Demonstrates trading session simulation

### Run Backtest
```bash
python backtest.py
```
Historical strategy testing

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| No market data | Check trading hours (09:15-15:30) |
| API errors | Verify API credentials in config.py |
| Token expired | Run `python auth.py` |
| No signals | Check confidence threshold |
| Import errors | Run `python setup_validation.py` |

## 📱 Notifications

Enable Telegram alerts by configuring:
```python
ENABLE_NOTIFICATIONS = True
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
```

## 🔐 Security

- Store credentials in environment variables
- Use `.env` file (not in git)
- OAuth for API authentication
- Tokens auto-refresh every 24 hours
- Never hardcode secrets

## 📈 Performance Metrics

Track these KPIs:
- **Win Rate**: % of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **ROI**: Return on Investment %
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest loss from peak

## 🎓 Learning Path

1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run [setup_validation.py](setup_validation.py)
3. Study [examples.py](examples.py)
4. Review [trend_analyzer.py](trend_analyzer.py)
5. Test with [practical_example.py](practical_example.py)
6. Start [trading_bot.py](trading_bot.py)

## 📞 Resources

- **Upstox API**: https://upstox.com/developer/api/
- **Technical Analysis**: https://school.stockcharts.com/
- **Trading Community**: https://community.upstox.com/

## 🎯 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Validate setup: `python setup_validation.py`
3. ✅ Get API credentials from Upstox
4. ✅ Update config.py with credentials
5. ✅ Authenticate: `python auth.py`
6. ✅ Test examples: `python examples.py`
7. ✅ Backtest: `python backtest.py`
8. ✅ Paper trade first!
9. ✅ Start live trading: `python trading_bot.py`
10. ✅ Monitor & optimize

## 📝 Project Files Reference

```
stock-market-app/
│
├── 📄 Core Modules (Trading Logic)
│   ├── trading_bot.py          [Main bot]
│   ├── trend_analyzer.py       [Analysis]
│   ├── order_manager.py        [Orders]
│   └── upstox_api.py          [API]
│
├── 🔐 Auth & Config
│   ├── auth.py                 [OAuth]
│   └── config.py               [Settings]
│
├── 🧪 Testing & Examples
│   ├── examples.py             [Code examples]
│   ├── practical_example.py    [Real scenarios]
│   ├── backtest.py            [Historical test]
│   └── setup_validation.py    [Validation]
│
├── 📚 Documentation
│   ├── README.md              [Full docs]
│   ├── QUICKSTART.md          [Quick setup]
│   ├── PROJECT_SUMMARY.md     [Overview]
│   ├── API_INTEGRATION.md     [API guide]
│   └── INDEX.md               [This file]
│
└── ⚙️ Configuration
    ├── requirements.txt        [Dependencies]
    ├── .gitignore             [Git ignore]
    └── .env.example           [Env template]
```

## ⚠️ Important Disclaimers

- Options trading carries high risk
- Past performance ≠ future results
- Use proper risk management
- Test thoroughly before live trading
- Always monitor active positions
- Be ready for manual intervention

## 🎉 Ready to Trade?

1. Complete setup with [QUICKSTART.md](QUICKSTART.md)
2. Run validation: `python setup_validation.py`
3. Start trading: `python trading_bot.py`

Good luck! 📈

---

**Project**: NSE Option Chain Automated Trading Bot
**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: May 5, 2026
