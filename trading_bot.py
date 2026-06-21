import logging
import schedule
import time
import urllib.request
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
import json
from collections import defaultdict

from config import (
    ACCESS_TOKEN, INDICES, OPTION_CHAIN_INTERVALS, TRADING_START_TIME, TRADING_END_TIME,
    MAX_TRADES_PER_DAY, USE_SANDBOX, SL_PERCENTAGE, TARGET_PERCENTAGE, SEND_ORDERS_TO_API
)
from upstox_api import UpstoxAPI
from trend_analyzer import TrendAnalyzer, Trend
from order_manager import OrderManager
from database import TradingDatabase
from importlib import import_module

# Configure logging
import sys
import io

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console handler: wrap stdout with UTF-8 to avoid Windows cp1252 encode errors for unicode symbols
try:
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    console_handler = logging.StreamHandler(stream=utf8_stdout)
except Exception:
    console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# Rotating file handler
try:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('trading_bot.log', maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
except Exception:
    # Fallback to basicConfig if RotatingFileHandler unavailable
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_public_ip(timeout: int = 10) -> Optional[str]:
    """Return the current public IP address or None if unavailable."""
    try:
        with urllib.request.urlopen('https://api.ipify.org', timeout=timeout) as response:
            return response.read().decode('utf-8').strip()
    except Exception as exc:
        logger.warning(f"Could not determine public IP: {exc}")
        return None


class OptionChainTradingBot:
    """Main trading bot for NSE option chain"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        use_sandbox: bool = True,
        base_url: str = None,
    ):
        self.upstox_api = UpstoxAPI(
            api_key,
            api_secret,
            access_token,
            use_sandbox=use_sandbox,
            base_url=base_url,
        )
        self.database = TradingDatabase()
        self.order_manager = OrderManager(self.upstox_api, database=self.database)
        self.market_data = defaultdict(dict)
        self.trend_history = defaultdict(list)
        self.trades_today = 0
        self.last_trade_time = {}
        self.last_signal_time = {}
        # Expose key config values on the bot for strategies
        from config import OPTION_CHAIN_INTERVALS as _OCI, INDICES as _IDX, UPDATE_INTERVAL_SECONDS as _UIS
        self.OPTION_CHAIN_INTERVALS = _OCI
        self.INDICES = _IDX
        self.UPDATE_INTERVAL_SECONDS = _UIS
        
        logger.info("Trading Bot initialized")
        logger.info("Database initialized for tracking orders and option chain summaries")
        
        # Test API connection
        logger.info("Testing API connection...")
        if not self.upstox_api.test_connection():
            logger.error("API connection test failed! Check your API credentials and access token.")
        else:
            logger.info("OK API connection test passed!")

        # Load strategies configured in config. Strategies live under strategies/<name>.py
        self.strategies = []
        from config import STRATEGIES
        for sname in STRATEGIES:
            try:
                mod = import_module(f"strategies.{sname}")
                cls = getattr(mod, ''.join([p.capitalize() for p in sname.split('_')]) + 'Strategy', None)
                if cls:
                    self.strategies.append(cls())
                    logger.info(f"Loaded strategy: {sname}")
                else:
                    logger.warning(f"Strategy class not found in strategies.{sname}")
            except Exception as e:
                logger.error(f"Failed to load strategy {sname}: {e}")
    
    def is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        try:
            current_time = datetime.now().time()
            start_time = datetime.strptime(TRADING_START_TIME, "%H:%M").time()
            end_time = datetime.strptime(TRADING_END_TIME, "%H:%M").time()
            
            return start_time <= current_time <= end_time
        except Exception as e:
            logger.error(f"Error checking trading hours: {str(e)}")
            return False
    
    def can_place_trade(self, symbol: str) -> bool:
        """Check if a trade can be placed"""
        try:
            # Check trading hours
            if not self.is_trading_hours():
                return False
            
            # Check max trades per day
            if self.trades_today >= MAX_TRADES_PER_DAY:
                logger.warning(f"Maximum trades ({MAX_TRADES_PER_DAY}) reached for the day")
                return False
            
            # Check if trade was recently placed for this symbol
            if symbol in self.last_trade_time:
                elapsed = datetime.now() - self.last_trade_time[symbol]
                if elapsed.total_seconds() < 300:  # 5 minutes cooldown
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking trade eligibility: {str(e)}")
            return False
    
    def fetch_market_data(self, index: str, intervals: List[int] = None) -> bool:
        """
        Fetch market data for an index across multiple intervals
        
        Args:
            index: Index name (NIFTY, BANKNIFTY, etc.)
            intervals: List of intervals in minutes
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if intervals is None:
                intervals = OPTION_CHAIN_INTERVALS
            
            index_mapping = {
                # Sandbox: Use NSE_EQ (stocks) since NSE_INDEX not supported
                # If Production: Use NSE_INDEX
                "NIFTY": "NSE_EQ|INE002A01018" if self.upstox_api.use_sandbox else "NSE_INDEX|Nifty 50",  # TCS (Nifty component) for sandbox
                "BANKNIFTY": "NSE_EQ|INE090A01021" if self.upstox_api.use_sandbox else "NSE_INDEX|Nifty Bank",  # HDFC Bank for sandbox
                "FINNIFTY": "NSE_EQ|INE040A01034" if self.upstox_api.use_sandbox else "NSE_INDEX|Nifty Fin Service",  # HDFC for sandbox
                "MIDCPNIFTY": "NSE_EQ|INE467B01029" if self.upstox_api.use_sandbox else "NSE_INDEX|Nifty Midcap 50"  # Bajaj Finance for sandbox
            }
            
            symbol = index_mapping.get(index)
            if not symbol:
                logger.error(f"Unknown index: {index}")
                return False
            
            # Map intervals to Upstox API format
            # SANDBOX v2 only: 1minute, 30minute, day, week, month
            # PRODUCTION v3: 5minute, 15minute, 30minute, 60minute, 240minute, day
            for interval in intervals:
                if self.upstox_api.use_sandbox:
                    # For sandbox, map minutes to supported formats
                    sandbox_interval_mapping = {
                        1: "1minute",
                        5: "1minute",      # 5min -> downgrade to 1min (closest available)
                        15: "30minute",     # 15min -> downgrade to 30min (closest available)
                        30: "30minute",
                        60: "30minute",     # 1hr -> downgrade to 30min
                        240: "30minute",    # 4hr -> downgrade to 30min
                        1440: "day"         # 1day
                    }
                    api_interval = sandbox_interval_mapping.get(interval, "30minute")
                    logger.info(f"Sandbox mode: Mapping {interval}min interval to {api_interval}")
                else:
                    # For production, use exact intervals
                    prod_interval_mapping = {
                        5: "5minute",
                        15: "15minute",
                        30: "30minute",
                        60: "60minute",
                        240: "240minute",
                        1440: "day"
                    }
                    api_interval = prod_interval_mapping.get(interval, "30minute")
                
                if not api_interval:
                    logger.warning(f"Unsupported interval: {interval}")
                    continue
                
                # Fetch OHLC data
                data = self.upstox_api.get_market_data(symbol, api_interval)
                
                if data:
                    # Store the OHLC data for trend analysis
                    self.market_data[index][interval] = {
                        "timestamp": datetime.now().isoformat(),
                        "ohlc": data,  # This is the full OHLC dict with arrays
                        "ltp": data["close"][-1] if data["close"] else 0,  # Last close price
                        "volume": data["volume"][-1] if data["volume"] else 0
                    }
                    logger.info(f"Fetched {index} data for {interval}min interval")
            
            return True
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")

            return False
    
    def analyze_index_trend(self, index: str, interval: int) -> Optional[Dict]:
        """
        Analyze trend for an index at a specific interval
        
        Args:
            index: Index name
            interval: Time interval in minutes
        
        Returns:
            Trend analysis or None on error
        """
        try:
            if index not in self.market_data or interval not in self.market_data[index]:
                logger.warning(f"No market data for {index} at {interval}min interval")
                return None
            
            market_data = self.market_data[index][interval]
            ohlc_data = market_data.get("ohlc", {})
            
            if not ohlc_data:
                return None
            
            # Perform trend analysis
            analysis = TrendAnalyzer.analyze_trend(ohlc_data)
            
            # Store in history
            key = f"{index}_{interval}"
            self.trend_history[key].append({
                "timestamp": market_data["timestamp"],
                "analysis": analysis
            })
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing trend: {str(e)}")
            return None
    
    def get_trading_signal(self, index: str) -> Optional[Dict]:
        """
        Generate trading signal based on multi-timeframe analysis
        
        Args:
            index: Index name
        
        Returns:
            Trading signal or None if no clear signal
        """
        try:
            signals = {
                "bullish": 0,
                "bearish": 0,
                "neutral": 0,
                "details": {}
            }
            
            logger.debug(f"Analyzing signals for {index}...")
            
            # Analyze configured timeframes
            for interval in OPTION_CHAIN_INTERVALS:
                analysis = self.analyze_index_trend(index, interval)
                
                if analysis:
                    signals["details"][f"{interval}min"] = analysis
                    logger.debug(f"{index} [{interval}min] Trend: {analysis['trend']}, Confidence: {analysis['confidence']}%")
                    
                    if analysis["trend"] == Trend.BULLISH.value:
                        signals["bullish"] += analysis["confidence"]
                    elif analysis["trend"] == Trend.BEARISH.value:
                        signals["bearish"] += analysis["confidence"]
                    else:
                        signals["neutral"] += 1
            
            logger.debug(f"{index} - Bullish: {signals['bullish']:.2f}, Bearish: {signals['bearish']:.2f}, Neutral: {signals['neutral']}")

            # Compute average confidence across analyzed intervals
            intervals_evaluated = len(signals["details"]) if signals["details"] else 0
            if intervals_evaluated == 0:
                return None

            if signals["bullish"] > signals["bearish"]:
                avg_strength = signals["bullish"] / intervals_evaluated
                return {
                    "signal": "BUY",
                    "strength": round(avg_strength, 2),
                    "details": signals["details"]
                }
            elif signals["bearish"] > signals["bullish"]:
                avg_strength = signals["bearish"] / intervals_evaluated
                return {
                    "signal": "SELL",
                    "strength": round(avg_strength, 2),
                    "details": signals["details"]
                }
            else:
                logger.debug(f"{index} - No clear signal (bullish and bearish equal)")
                return None
        except Exception as e:
            logger.error(f"Error generating trading signal: {str(e)}")
            return None

    def normalize_option_instrument_key(self, option_symbol: str) -> List[str]:
        """Return candidate Upstox instrument keys for an option symbol."""
        candidates = []
        if "|" in option_symbol:
            candidates.append(option_symbol)
        else:
            candidates.append(f"NFO|{option_symbol}")
            candidates.append(f"NSE_FO|{option_symbol}")
        return candidates

    def get_option_entry_price(self, option_symbol: str) -> Optional[float]:
        """Fetch the latest option LTP for the option symbol."""
        try:
            for candidate in self.normalize_option_instrument_key(option_symbol):
                logger.debug(f"Trying option instrument key: {candidate}")
                option_market = self.upstox_api.get_market_data(candidate, "1minute")
                if option_market and option_market.get("close"):
                    try:
                        return float(option_market["close"][-1])
                    except Exception:
                        continue
            logger.warning(f"No close data returned for option market data: {option_symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching option entry price for {option_symbol}: {str(e)}")
            return None

    def place_option_trade(self, index: str, option_type: str = "CE", expiry_days: int = 0) -> bool:
        """
        Place an options trade based on signals
        
        Args:
            index: Index name (NIFTY, BANKNIFTY, etc.)
            option_type: CE (Call) or PE (Put)
            expiry_days: Days to expiry (0 = same day, 1 = next day)
        
        Returns:
            True if trade placed, False otherwise
        """
        try:
            # Check if trade can be placed
            if not self.can_place_trade(index):
                logger.debug(f"Cannot place trade for {index} - Trade eligibility check failed")
                return False
            
            # Get trading signal
            signal = self.get_trading_signal(index)
            
            if not signal:
                logger.debug(f"No clear signal for {index}")
                return False
            
            logger.info(f"OK Signal found for {index}: {signal['signal']} (Strength: {signal['strength']:.2f})")
            
            # If signal is SELL, use PE options by default
            try:
                if signal["signal"] == "SELL":
                    option_type = "PE"
            except Exception:
                pass

            # Check signal strength threshold
            # signal['strength'] is the average confidence across intervals (0-100)
            if signal["strength"] < 50.0:
                logger.info(f"Signal strength too low for {index}: {signal['strength']:.2f} (Need >= 50.0)")
                return False
            
            # Get current price
            if index not in self.market_data or 5 not in self.market_data[index]:
                logger.warning(f"No current price data for {index}")
                return False
            
            current_price = self.market_data[index][5]["ltp"]
            
            # Determine strike price (simplified logic)
            strike_diff = 100 if index in ["NIFTY", "MIDCPNIFTY"] else 200
            strike = round(current_price / strike_diff) * strike_diff
            
            # Adjust strike based on signal
            if signal["signal"] == "BUY":
                if option_type == "CE":
                    strike = strike + strike_diff
                else:
                    strike = strike - strike_diff
            else:
                if option_type == "CE":
                    strike = strike - strike_diff
                else:
                    strike = strike + strike_diff
            
            # Create option symbol (simplified - actual format may vary)
            today = datetime.now()
            expiry_date = today.strftime("%d%b%y").upper()
            
            option_symbol = f"{index}{expiry_date}{int(strike)}{option_type}"
            
            # Determine option entry price by fetching option market LTP if possible
            option_ltp = self.get_option_entry_price(option_symbol)
            if option_ltp is None:
                # If we're in DB-only mode, allow using mock data to record trades for testing
                if not SEND_ORDERS_TO_API:
                    try:
                        from mock_data import get_mock_market_data
                        mock = get_mock_market_data(option_symbol, "1minute", days=1)
                        if mock and mock.get('close'):
                            option_ltp = float(mock['close'][-1])
                            logger.warning(f"Using mock LTP for {option_symbol} in DB-only mode: {option_ltp}")
                        else:
                            logger.warning(f"Mock data unavailable for {option_symbol}; aborting trade")
                            return False
                    except Exception as e:
                        logger.error(f"Error obtaining mock LTP for {option_symbol}: {e}")
                        return False
                else:
                    logger.warning(f"Could not fetch option LTP for {option_symbol}; aborting trade to avoid invalid option price")
                    return False

            entry_price = option_ltp
            if signal["signal"] == "BUY":
                sl_price = entry_price * (1 - SL_PERCENTAGE / 100)
                target_price = entry_price * (1 + TARGET_PERCENTAGE / 100)
            else:
                sl_price = entry_price * (1 + SL_PERCENTAGE / 100)
                target_price = entry_price * (1 - TARGET_PERCENTAGE / 100)

            risk = abs(entry_price - sl_price)
            reward = abs(target_price - entry_price)
            ratio = reward / risk if risk else 0
            
            # ========== PLACE ACTUAL ORDER IN SANDBOX MODE ==========
            logger.info("=" * 80)
            logger.info("PLACING TRADE ORDER IN SANDBOX MODE")
            logger.info("=" * 80)
            logger.info(f"Index: {index}")
            logger.info(f"Symbol: {option_symbol}")
            logger.info(f"Side: {signal['signal']}")
            logger.info(f"Signal Strength: {signal['strength']:.2f}")
            logger.info(f"Entry Price: {entry_price:.2f}")
            logger.info(f"Stop Loss: {sl_price:.2f}")
            logger.info(f"Target: {target_price:.2f}")
            logger.info(f"Risk: {risk:.2f}")
            logger.info(f"Reward: {reward:.2f}")
            logger.info(f"Risk:Reward Ratio: 1:{ratio:.2f}")
            logger.info("=" * 80)
            
            # Attempt to place real order
            order = self.order_manager.place_trade(
                symbol=option_symbol,
                quantity=1,
                side=signal["signal"],
                entry_price=entry_price
            )
            
            if order:
                order_id = order.get('order_id', f"ORD_{index}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
                
                # Save to database
                order_data = {
                    'order_id': order_id,
                    'symbol': option_symbol,
                    'side': signal['signal'],
                    'quantity': 1,
                    'entry_price': entry_price,
                    'underlying_price': current_price,
                    'option_entry_price': entry_price,
                    'stop_loss': sl_price,
                    'target': target_price,
                    'status': 'PLACED'
                }
                
                db_id = self.database.insert_order(order_data)
                if db_id:
                    logger.info(f"OK Order saved to database with ID: {db_id}")
                    logger.info(f"Order ID: {order_id}")
                
                self.trades_today += 1
                self.last_trade_time[index] = datetime.now()
                logger.info(f"OK Trade placed for {index}: {signal['signal']} {option_symbol} @ {entry_price:.2f}")
                logger.info(f"Order Response: {order}")
                return True
            else:
                logger.error(f"ERROR Failed to place order for {index}")
                return False
                
        except Exception as e:
            logger.error(f"Error placing option trade: {str(e)}")
            return False
    
    def run_analysis_cycle(self):
        """Run one complete analysis and trading cycle"""
        try:
            logger.info("="*80)
            logger.info(f"Starting analysis cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*80)
            
            # Run each configured strategy for each index
            for index in INDICES:
                logger.info(f"\nAnalyzing {index}...")
                for strat in self.strategies:
                    try:
                        strat.analyze_and_trade(self, index)
                    except Exception as e:
                        logger.error(f"Error running strategy {strat.name()} for {index}: {e}")

                # Update trade P&L (use latest 5min LTP if available)
                try:
                    current_ltp = self.market_data[index][5]["ltp"] if 5 in self.market_data.get(index, {}) else None
                    if current_ltp is not None:
                        current_prices = {index: current_ltp}
                        self.order_manager.update_trade_pnl(current_prices)
                except Exception:
                    pass
            
            # Print trade summary
            summary = self.order_manager.get_trade_summary()
            logger.info(f"Trade Summary: {summary}")
            
        except Exception as e:
            logger.error(f"Error in analysis cycle: {str(e)}")
    
    def start(self, update_interval: int = 60):
        """
        Start the trading bot
        
        Args:
            update_interval: Update interval in seconds
        """
        try:
            logger.info(f"Starting trading bot with {update_interval}s update interval")
            
            # Schedule analysis cycles
            schedule.every(update_interval).seconds.do(self.run_analysis_cycle)
            
            # Run scheduler
            while True:
                schedule.run_pending()
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Trading bot stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error in bot execution: {str(e)}")
    
    def stop(self):
        """Stop the trading bot and save trade history"""
        try:
            logger.info("Stopping trading bot...")
            
            # Export trade history
            self.order_manager.export_trades("trades_history.json")
            
            # Print final summary
            summary = self.order_manager.get_trade_summary()
            logger.info(f"Final Summary: {summary}")
            
            # Get active orders from database
            active_orders = self.database.get_active_orders()
            logger.info(f"Active orders in database: {len(active_orders)}")
            
            # Get today's summary from database
            today_summary = self.database.get_today_summary()
            logger.info(f"Today's database summary: {today_summary}")
            
            # Export database tables to CSV (optional) into data/exports/<table>/
            logger.info("Exporting database tables to data/exports/...")
            self.database.export_to_csv("orders")
            self.database.export_to_csv("option_chain_summary")
            self.database.export_to_csv("trading_signals")

            # Close database connection
            self.database.close()

            # Save summary to file under data/exports/summary/
            import os
            os.makedirs("data/exports/summary", exist_ok=True)
            with open(f"data/exports/summary/trading_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                json.dump(summary, f, indent=2)

            logger.info("Trading bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")


def main():
    """Main function to run the trading bot"""
    try:
        # Get API credentials (from environment or config)
        from config import UPSTOX_API_KEY, UPSTOX_API_SECRET, UPSTOX_API_BASE_URL
        
        # Get access token (you need to implement OAuth flow to get this)
        # For now, this is a placeholder
        access_token = ACCESS_TOKEN
        logger.info(f"API Base URL: {UPSTOX_API_BASE_URL or ('sandbox' if USE_SANDBOX else 'production')}")
        
        logger.info("="*80)
        logger.info("UPSTOX TRADING BOT - STARTUP")
        logger.info("="*80)
        logger.info(f"API Key (last 8 chars): ...{UPSTOX_API_KEY[-8:]}")
        logger.info(f"Access Token (first 20 chars): {access_token[:20]}...")
        logger.info(f"Use Sandbox: {USE_SANDBOX}")
        if not USE_SANDBOX:
            public_ip = get_public_ip()
            if public_ip:
                logger.info(f"Live mode public IP: {public_ip}")
            else:
                logger.warning("Live mode public IP could not be determined")
        logger.info("="*80)
        
        # if not access_token or access_token == ACCESS_TOKEN:
        #     logger.error("Please set a valid access token")
        #     return
        
        # Initialize and start bot with sandbox mode from config
        bot = OptionChainTradingBot(
            UPSTOX_API_KEY,
            UPSTOX_API_SECRET,
            access_token,
            use_sandbox=USE_SANDBOX,
            base_url=UPSTOX_API_BASE_URL,
        )
        logger.info(f"OK Trading Bot initialized in {'SANDBOX' if USE_SANDBOX else 'LIVE'} MODE")
        
        # Run bot using configured update interval (seconds)
        from config import UPDATE_INTERVAL_SECONDS
        bot.start(update_interval=UPDATE_INTERVAL_SECONDS)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
