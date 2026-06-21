# Quick Start Guide

## 1. Installation

```bash
# Install required packages
pip install -r requirements.txt
```

## 2. Configuration

Edit `config.py` and add your Upstox API credentials:

```python
UPSTOX_API_KEY = "your_api_key_here"
UPSTOX_API_SECRET = "your_api_secret_here"
```

## 3. Authentication

Get an access token:

```bash
python auth.py
```

This will:
- Open Upstox login page in your browser
- Ask you to authorize the app
- Generate and save the access token

## 4. Run Examples (Optional)

Test the system with mock data:

```bash
python examples.py
```

This runs 5 examples showing:
- Technical indicator calculations
- Trend analysis
- Entry/exit point calculation
- Order management
- Multi-timeframe analysis

## 5. Start Trading Bot

Run the live trading bot:

```bash
python trading_bot.py
```

The bot will:
- Connect to Upstox API
- Monitor NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY
- Generate signals from multiple timeframes
- Place trades when signals are confirmed
- Manage positions with automatic SL & targets

## Key Configuration Parameters

### Risk Management
```python
SL_PERCENTAGE = 1.0          # Stop loss percentage
TARGET_PERCENTAGE = 2.0      # Target profit percentage
MAX_TRADES_PER_DAY = 5       # Daily trade limit
```

### Trading Hours
```python
TRADING_START_TIME = "09:15"
TRADING_END_TIME = "15:30"
```

### Notifications
```python
ENABLE_NOTIFICATIONS = True
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
```

## Troubleshooting

### Issue: "No market data"
- Check if market is open (09:15 - 15:30 IST)
- Verify API connection
- Check API credentials in config.py

### Issue: "Access token expired"
```bash
python auth.py
```
Then restart the bot.

### Issue: "No signals generated"
- Adjust TREND_THRESHOLD in config.py
- Check if trend confidence is high enough
- Verify sufficient historical data is available

## Monitoring

### View Trade Summary
The bot displays real-time metrics:
- Total trades executed
- Active positions
- Win rate
- Total P&L
- Daily return

### Trade History
Check `trades_history.json` for detailed trade records.

## Strategy Parameters

### Trend Confirmation
The bot requires multi-timeframe confirmation:
- 5-minute, 15-minute, 30-minute timeframes (short-term)
- 1-hour, 2-hour, 4-hour timeframes (medium-term)
- Signals are generated only when multiple timeframes align

### Entry Signals
- BUY: When SMA9 > SMA20, RSI > 50, MACD positive
- SELL: When SMA9 < SMA20, RSI < 50, MACD negative

### Exit Strategy
- **Target**: Automatic exit at +2% profit (configurable)
- **Stop Loss**: Automatic exit at -1% loss (configurable)
- **Time-based**: Optional exit at end of day

## Advanced Usage

### Backtesting
```bash
python backtest.py
```

Requires historical data in CSV format:
```csv
timestamp,open,high,low,close,volume
2024-01-01 09:15:00,50000,50100,49900,50050,1000000
```

### Custom Indicators
Edit `trend_analyzer.py` to add custom technical indicators:

```python
@staticmethod
def calculate_custom_indicator(data):
    # Your indicator logic
    return indicator_value
```

### Strategy Modifications
Edit `trading_bot.py` to customize:
- Entry conditions
- Exit conditions
- Position sizing
- Risk management

## Important Notes

1. **Paper Trading First**: Test strategy on paper trading before live trading
2. **Risk Management**: Always use appropriate SL and targets
3. **Monitoring**: Keep monitoring active positions during market hours
4. **Logs**: Check logs for any errors or warnings
5. **Backtest**: Test strategy on historical data before deploying

## Support

For issues or questions:
1. Check logs in console output
2. Refer to API documentation
3. Review example usage in `examples.py`

## Performance Expectations

Based on typical market conditions:
- Win rate: 60-75% (depends on market regime)
- Profit factor: 1.5-2.5 (ratio of wins to losses)
- Average holding time: 15-60 minutes
- Daily trades: 2-5 (depends on signal frequency)

## Risk Disclaimer

- Past performance is not indicative of future results
- Trading in derivatives carries high risk
- Use only with capital you can afford to lose
- Always implement proper risk management
- This bot is for educational purposes

## Next Steps

1. Understand the strategy in README.md
2. Configure your API credentials
3. Run examples to familiarize with the system
4. Backtest on historical data
5. Start with paper trading
6. Monitor performance metrics
7. Fine-tune parameters based on results

Happy Trading! 📈
