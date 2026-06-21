# 🎯 DATABASE INTEGRATION - QUICK START

## ✅ What Changed

| Item | Before | After |
|------|--------|-------|
| Order Placement | Live API calls | ✏️ Logging only |
| Data Tracking | No database | ✅ SQLite tracking |
| Analysis Storage | Not saved | ✅ Saved per interval |
| Signal Tracking | Not recorded | ✅ All recorded |

---

## 🚀 Getting Started

### Step 1: Run the Bot
```bash
python trading_bot.py
```

**What happens:**
- Database auto-creates on first run
- Each signal is logged to console
- Data saved to SQLite database
- CSV files generated on exit

### Step 2: Monitor in Another Terminal
```bash
python database_query.py
```

**Shows:**
- Today's orders
- Active positions
- Trading signals
- Option chain history
- Performance summary

### Step 3: Review Data
When bot stops, check generated CSV files:
```
orders_20260505_101530.csv
option_chain_summary_20260505_101530.csv
trading_signals_20260505_101530.csv
```

---

## 📊 Sample Output

### Console Output (When Signal Generated):
```
================================================================================
🔔 TRADE SIGNAL GENERATED (NOT PLACED - LOGGING ONLY)
================================================================================
Index: NIFTY
Symbol: NIFTY05MAY2411000CE
Side: BUY
Signal Strength: 3.45
Entry Price: ₹150.00
Stop Loss: ₹148.50
Target: ₹152.00
Risk: ₹1.50
Reward: ₹2.00
Risk:Reward Ratio: 1:1.33
================================================================================
✓ Order saved to database with ID: 1
Order ID: SIM_NIFTY_20260505101530
```

### Database Query Output:
```
╒════════════════════════╤═════════════════════╤═════════════════════╤═════════╤═════════════╤═════════════╤═════════════╤═════════════════╕
│ Order ID               │ Symbol              │ Side                │ Qty     │ Entry       │ SL          │ Target      │ Status          │
╞════════════════════════╪═════════════════════╪═════════════════════╪═════════╪═════════════╪═════════════╪═════════════╪═════════════════╡
│ SIM_NIFTY_20260505...  │ NIFTY05MAY24...     │ BUY                 │ 1       │ ₹150.00     │ ₹148.50     │ ₹152.00     │ LOGGED          │
╘════════════════════════╧═════════════════════╧═════════════════════╧═════════╧═════════════╧═════════════╧═════════════╧═════════════════╛
```

---

## 🗄️ Database Files

### Location:
```
c:\Chandan\GitHub\stock-market-app\trading_bot.db
```

### Tables:
1. **orders** - All logged trade orders
2. **option_chain_summary** - Technical analysis per interval
3. **trading_signals** - Generated signals
4. **daily_summary** - Daily performance

---

## 💡 Key Features

### ✅ Enabled:
- Logging all trade calculations
- Saving to SQLite database
- Storing option chain analysis
- Recording trading signals
- Exporting to CSV

### ⏸️ Paused:
- Real order placement (API calls commented out)

---

## 🔄 Data Flow

```
Market Data (6 intervals)
    ↓
Technical Analysis
    ↓
Save to option_chain_summary ✅
    ↓
Generate Trading Signal
    ↓
Save to trading_signals ✅
    ↓
Log Values to Console ✅
    ↓
Save to orders (LOGGED status) ✅
    ↓
[Real Order Code - COMMENTED OUT]
```

---

## 🎮 Commands

### Start Bot with Database Tracking:
```bash
python trading_bot.py
```

### Query Database (Live):
```bash
python database_query.py
```

### Check Today's Orders:
```python
from database_query import DatabaseQueryHelper
helper = DatabaseQueryHelper()
helper.display_today_orders()
```

### Check Specific Index History:
```python
helper.display_option_chain_history("NIFTY", interval=5, limit=20)
```

---

## 📈 Example Queries

### Get all orders from database:
```python
from database import TradingDatabase
db = TradingDatabase()
orders = db.get_today_orders()
for order in orders:
    print(f"{order['symbol']}: {order['side']} @ {order['entry_price']}")
db.close()
```

### Get option chain history:
```python
history = db.get_option_chain_history("NIFTY", 5, limit=10)
for rec in history:
    print(f"NIFTY 5min: {rec['trend']} ({rec['confidence']:.2f}%)")
```

### Get active orders:
```python
active = db.get_active_orders()
print(f"Active orders: {len(active)}")
```

---

## 🚨 Important Notes

⚠️ **Order placement is DISABLED for safety**
- All trades are logged, not placed
- Database stores all information
- Real orders can be enabled later by uncommenting code

---

## 📋 Status Check

### Is database working?
```bash
python database_query.py
```

### See today's data?
```bash
python database_query.py
# Check the output tables
```

### Export data?
```
# Automatically created when bot stops:
orders_*.csv
option_chain_summary_*.csv
trading_signals_*.csv
```

---

## 🎯 Next Actions

1. ✅ **Start bot**: `python trading_bot.py`
2. ✅ **Monitor**: `python database_query.py`
3. ✅ **Review**: Check console logs
4. ✅ **Verify**: Check CSV exports
5. ⏭️ **Enable Live** (when ready): Uncomment order code

---

## 📞 Quick Help

| Issue | Solution |
|-------|----------|
| Database error | Delete `trading_bot.db` and restart |
| No orders logging | Check console for errors |
| Query fails | Ensure bot is running or DB exists |
| Want live orders | Uncomment code in `place_option_trade()` |

---

**Status**: ✅ Ready
**Database**: SQLite (trading_bot.db)
**Orders**: Logging Only (NOT Placed)
**Data Saved**: Yes (All intervals tracked)

---

🎉 **Ready to use! Start with**: `python trading_bot.py`
