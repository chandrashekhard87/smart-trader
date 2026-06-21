import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_NOTIFICATIONS,
    SL_PERCENTAGE, TARGET_PERCENTAGE
)
from config import SEND_ORDERS_TO_API

logger = logging.getLogger(__name__)


class OrderManager:
    """Manage order placement and tracking"""
    
    def __init__(self, upstox_api, config: Dict = None, database=None):
        self.upstox_api = upstox_api
        self.config = config or {}
        self.database = database
        self.active_orders = {}
        self.trade_history = []
    
    def calculate_order_prices(self, entry_price: float, side: str = "BUY",
                               sl_percent: float = SL_PERCENTAGE,
                               target_percent: float = TARGET_PERCENTAGE) -> Dict:
        """
        Calculate order prices based on entry and percentages
        
        Args:
            entry_price: Entry price for the trade
            side: BUY or SELL
            sl_percent: Stop loss percentage
            target_percent: Target percentage
        
        Returns:
            Dictionary with entry, SL, and target prices
        """
        try:
            if side.upper() == "BUY":
                sl_price = entry_price * (1 - sl_percent / 100)
                target_price = entry_price * (1 + target_percent / 100)
            else:  # SELL
                sl_price = entry_price * (1 + sl_percent / 100)
                target_price = entry_price * (1 - target_percent / 100)
            
            return {
                "entry": round(entry_price, 2),
                "stop_loss": round(sl_price, 2),
                "target": round(target_price, 2),
                "side": side.upper()
            }
        except Exception as e:
            logger.error(f"Error calculating order prices: {str(e)}")
            return None
    
    def place_trade(self, symbol: str, quantity: int, side: str, entry_price: float,
                   order_type: str = "MARKET", product: str = "MIS") -> Optional[Dict]:
        """
        Place a trade with bracket order (SL and Target)
        
        Args:
            symbol: Option symbol
            quantity: Quantity
            side: BUY or SELL
            entry_price: Entry price
            order_type: MARKET or LIMIT
            product: MIS or CNC
        
        Returns:
            Order details or None on error
        """
        try:
            # Calculate SL and target
            prices = self.calculate_order_prices(entry_price, side)
            
            if not prices:
                return None
            
            # Log order details (commented out for testing)
            order_log = {
                "symbol": symbol,
                "quantity": quantity,
                "side": side,
                "price": entry_price,
                "sl_price": prices["stop_loss"],
                "target_price": prices["target"],
                "product": product
            }
            logger.info(f"[LIVE ORDER WOULD BE PLACED] {json.dumps(order_log, indent=2)}")
            
            # COMMENTED OUT FOR TESTING - Actual order placement disabled
            order_response = None
            if SEND_ORDERS_TO_API:
                # Place a real order via Upstox API
                order_response = self.upstox_api.place_bracket_order(
                    symbol=symbol,
                    quantity=quantity,
                    side=side,
                    price=entry_price,
                    sl_price=prices["stop_loss"],
                    target_price=prices["target"],
                    product=product
                )
            else:
                # DB-only/testing mode: simulate a successful response and do NOT call the live API
                logger.info("SEND_ORDERS_TO_API is False - recording order locally (DB-only mode)")
                order_response = {
                    "data": {
                        "order_id": f"SIM_{datetime.now().timestamp()}"
                    }
                }
            
            if order_response:
                # Store order details
                order_info = {
                    "order_id": order_response.get("data", {}).get("order_id"),
                    "symbol": symbol,
                    "quantity": quantity,
                    "side": side,
                    "entry_price": entry_price,
                    "stop_loss": prices["stop_loss"],
                    "target": prices["target"],
                    "status": "PLACED",
                    "timestamp": datetime.now().isoformat(),
                    "pnl": 0
                }
                
                self.active_orders[order_info["order_id"]] = order_info
                self.trade_history.append(order_info)
                
                logger.info(f"Trade placed: {order_info}")
                self.notify(f"Trade Placed: {symbol} {side} @ {entry_price}\nSL: {prices['stop_loss']}\nTarget: {prices['target']}")
                
                return order_info
            else:
                logger.error(f"Failed to place order for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing trade: {str(e)}")
            return None
    
    def update_trade_pnl(self, current_prices: Dict[str, float]):
        """
        Update P&L for active trades
        
        Args:
            current_prices: Dictionary with symbol: current_price
        """
        try:
            for order_id, order_info in self.active_orders.items():
                symbol = order_info["symbol"]
                
                if symbol in current_prices:
                    current_price = current_prices[symbol]
                    
                    if order_info["side"] == "BUY":
                        pnl = (current_price - order_info["entry_price"]) * order_info["quantity"]
                    else:
                        pnl = (order_info["entry_price"] - current_price) * order_info["quantity"]
                    
                    order_info["pnl"] = round(pnl, 2)
                    order_info["current_price"] = current_price
                    
        except Exception as e:
            logger.error(f"Error updating trade P&L: {str(e)}")
    
    def close_trade(self, order_id: str, current_price: float) -> bool:
        """
        Close an active trade
        
        Args:
            order_id: Order ID to close
            current_price: Current market price
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if order_id in self.active_orders:
                order_info = self.active_orders[order_id]
                
                # Calculate final P&L
                if order_info["side"] == "BUY":
                    final_pnl = (current_price - order_info["entry_price"]) * order_info["quantity"]
                else:
                    final_pnl = (order_info["entry_price"] - current_price) * order_info["quantity"]
                
                order_info["status"] = "CLOSED"
                order_info["exit_price"] = current_price
                order_info["pnl"] = round(final_pnl, 2)
                order_info["close_timestamp"] = datetime.now().isoformat()
                
                # Move to history
                del self.active_orders[order_id]

                # Update database if available
                try:
                    if self.database:
                        # Use database.close_order to set exit_price, option_exit_price, pnl, closed_at and update daily summary
                        self.database.close_order(order_id, exit_price=current_price, option_exit_price=current_price)
                        logger.info(f"Order {order_id} closed in database with option exit price {current_price}")
                except Exception as e:
                    logger.error(f"Error updating DB on close for {order_id}: {e}")

                logger.info(f"Trade closed: {order_info}")
                self.notify(f"Trade Closed: {order_info['symbol']} P&L: {order_info['pnl']}")

                return True
            else:
                logger.warning(f"Order ID not found: {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing trade: {str(e)}")
            return False
    
    def get_trade_summary(self) -> Dict:
        """Get summary of trades"""
        try:
            total_trades = len(self.trade_history)
            active_trades = len(self.active_orders)
            
            closed_trades = [t for t in self.trade_history if t.get("status") == "CLOSED"]
            total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
            
            winning_trades = len([t for t in closed_trades if t.get("pnl", 0) > 0])
            losing_trades = len([t for t in closed_trades if t.get("pnl", 0) < 0])
            
            active_pnl = sum(order["pnl"] for order in self.active_orders.values())
            
            return {
                "total_trades": total_trades,
                "active_trades": active_trades,
                "closed_trades": len(closed_trades),
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(winning_trades / len(closed_trades) * 100, 2) if closed_trades else 0,
                "total_pnl": round(total_pnl, 2),
                "active_pnl": round(active_pnl, 2),
                "total_return": round(total_pnl + active_pnl, 2)
            }
        except Exception as e:
            logger.error(f"Error getting trade summary: {str(e)}")
            return {}
    
    def notify(self, message: str):
        """Send notification"""
        if not ENABLE_NOTIFICATIONS:
            return
        
        try:
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                import requests
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message
                }
                requests.post(url, json=payload, timeout=5)
            else:
                logger.info(f"Notification: {message}")
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
    
    def export_trades(self, filename: str = "trades.json"):
        """Export trade history to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "active_orders": self.active_orders,
                    "trade_history": self.trade_history,
                    "summary": self.get_trade_summary()
                }, f, indent=2)
            logger.info(f"Trades exported to {filename}")
        except Exception as e:
            logger.error(f"Error exporting trades: {str(e)}")
