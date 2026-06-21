# # Upstox API Configuration Balu
# UPSTOX_API_KEY = "76cdf51c-f973-4bc3-bf95-0b348af4fdef"
# UPSTOX_API_SECRET = "f2qogzzl06"
# UPSTOX_REDIRECT_URL = "http://localhost:8080/callback"
# ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzUEI2QlgiLCJqdGkiOiI2OWZhZTdjMGI4Zjc3ODQwMDk3NTE1ZDYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzc4MDUxMDA4LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3ODA2MTA0MDB9.P0huOUoP-REQMqOR-2qv1SiTavkZ3P-Fx1EnyRs5fHY"


# Upstox API Configuration CD LIVE
UPSTOX_API_KEY = "0cf66f06-dd8e-495e-aec0-49b7b31e4e22"
UPSTOX_API_SECRET = "mannlavip1"
UPSTOX_REDIRECT_URL = "http://localhost:8080/callback"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyVEI0UE4iLCJqdGkiOiI2YTI3OTkxM2IzZGI0NDI4MDMzOTRmZDEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc4MDk3OTk4NywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzgxMDQyNDAwfQ.O9NYcSTvw8zPxUv4DzwuAjhM-dBxGyqf2hyECEL_wA0"

# # Upstox API Configuration CD SB
# UPSTOX_API_KEY = "922e431d-949a-4a3d-b071-aa1f6838e63d"
# UPSTOX_API_SECRET = "e9ko982g19"
# UPSTOX_REDIRECT_URL = "http://localhost:8080/callback"
# ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyVEI0UE4iLCJqdGkiOiI2YTIyNGZhYjc5ZGVkZjY5MDE0ZTY0YWQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzgwNjMzNTE1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3ODMyMDI0MDB9.Etn9_u21z_5C_DgwmFd56iOu-rWVQEiZLOc55N7xy6E"



# Sandbox Mode Configuration
USE_SANDBOX = False  # Set to False for live trading
SANDBOX_MODE = False  # Enable sandbox mode for order placement
UPSTOX_API_SANDBOX_URL = "https://api-sandbox.upstox.com/v2"
UPSTOX_API_PRODUCTION_URL = "https://api.upstox.com/v3"
UPSTOX_API_BASE_URL = None  # Override the base API URL if needed

# Trading Configuration
INDICES = ["NIFTY"] # "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"
OPTION_CHAIN_INTERVALS = [5]  # 5-minute candles (production v3 supports: 5minute, 15minute, 30minute, 60minute, 240minute, day)
# Sandbox v2: 1minute, 30minute, day, week, month
# Production v3: 5minute, 15minute, 30minute, 60minute, 240minute, day

# NOTE: NSE_INDEX (like "NSE_INDEX|Nifty 50") may not work in sandbox
# If getting 404 errors for indices:
# 1. Try using NSE_EQ instrument keys instead
# 2. Check Upstox sandbox documentation for available instruments
# 3. You may need to use specific stock symbols instead of indices in sandbox

# Strategy Configuration
TREND_THRESHOLD = 2  # percentage change threshold for trend confirmation
SL_PERCENTAGE = 1.0  # Stop Loss percentage
TARGET_PERCENTAGE = 2.0  # Target profit percentage

# Active strategies (module paths under `strategies` without .py)
STRATEGIES = [
	"trend_signal"
]

# Order Configuration
ORDER_TYPE = "MIS"  # MIS or CNC
QUANTITY = 1
PRODUCT = "MIS"

# Risk Management
MAX_LOSS_PER_TRADE = 1000  # Maximum loss per trade
MAX_TRADES_PER_DAY = 5  # Maximum trades per day

# Trading Hours
TRADING_START_TIME = "09:15"
TRADING_END_TIME = "15:30"

# Bot update interval in seconds (default 5 minutes)
UPDATE_INTERVAL_SECONDS = 300

# Notification
ENABLE_NOTIFICATIONS = True
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
# Controls whether orders are actually sent to Upstox API. Set to False to record orders to DB only.
SEND_ORDERS_TO_API = False
