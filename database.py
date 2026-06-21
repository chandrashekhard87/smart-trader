"""
SQLite Database Management for Trading Bot
Tracks orders and option chain summaries
"""

import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class TradingDatabase:
    """SQLite database for trading data"""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.connection = None
        self.initialize_database()
    
    def connect(self):
        """Create database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
    
    def initialize_database(self):
        """Create tables if they don't exist"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    option_entry_price REAL,
                    underlying_price REAL,
                    stop_loss REAL NOT NULL,
                    target REAL NOT NULL,
                    status TEXT DEFAULT 'PLACED',
                    exit_price REAL,
                    option_exit_price REAL,
                    pnl REAL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    closed_at TIMESTAMP
                )
            ''')
            
            # Option chain summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_chain_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL,
                    interval_minutes INTEGER NOT NULL,
                    trend TEXT,
                    confidence REAL,
                    current_price REAL,
                    sma_9 REAL,
                    sma_20 REAL,
                    sma_50 REAL,
                    rsi REAL,
                    macd REAL,
                    signal_line REAL,
                    bb_upper REAL,
                    bb_middle REAL,
                    bb_lower REAL,
                    atr REAL,
                    bullish_signals INTEGER,
                    bearish_signals INTEGER,
                    created_at TIMESTAMP
                )
            ''')
            
            # Trading signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL,
                    signal_type TEXT,
                    signal_strength REAL,
                    bullish_count INTEGER,
                    bearish_count INTEGER,
                    neutral_count INTEGER,
                    details TEXT,
                    created_at TIMESTAMP
                )
            ''')
            
            # Daily summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trading_date DATE UNIQUE,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    roi REAL DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def insert_order(self, order_data: Dict) -> Optional[int]:
        """Insert order into database"""
        try:
            cursor = self.connection.cursor()
            # Use IST for created_at/updated_at
            ist = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).isoformat()

            cursor.execute('''
                INSERT INTO orders 
                (order_id, symbol, side, quantity, entry_price, option_entry_price, underlying_price, stop_loss, target, status, exit_price, option_exit_price, pnl, closed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_data.get('order_id'),
                order_data.get('symbol'),
                order_data.get('side'),
                order_data.get('quantity'),
                order_data.get('entry_price'),
                order_data.get('option_entry_price'),
                order_data.get('underlying_price'),
                order_data.get('stop_loss'),
                order_data.get('target'),
                order_data.get('status', 'PLACED'),
                order_data.get('exit_price'),
                order_data.get('option_exit_price'),
                order_data.get('pnl'),
                order_data.get('closed_at'),
                ist,
                ist
            ))
            
            self.connection.commit()
            logger.info(f"Order inserted: {order_data.get('order_id')}")
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error inserting order: {str(e)}")
            return None
    
    def update_order(self, order_id: str, update_data: Dict) -> bool:
        """Update order status and details"""
        try:
            cursor = self.connection.cursor()
            
            updates = []
            values = []
            
            for key, value in update_data.items():
                if key in ['status', 'exit_price', 'option_exit_price', 'option_entry_price', 'pnl', 'closed_at']:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            # Set updated_at in IST
            ist = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).isoformat()
            updates.append("updated_at = ?")
            values.append(ist)
            values.append(order_id)
            
            query = f"UPDATE orders SET {', '.join(updates)} WHERE order_id = ?"
            cursor.execute(query, values)
            
            self.connection.commit()
            logger.info(f"Order updated: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating order: {str(e)}")
            return False

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Fetch a single order by order_id"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching order by id: {str(e)}")
            return None

    def close_order(self, order_id: str, exit_price: float, option_exit_price: float = None) -> bool:
        """Record order exit price (underlying), option exit price, pnl and update daily summary"""
        try:
            order = self.get_order_by_id(order_id)
            if not order:
                logger.warning(f"Order not found for closing: {order_id}")
                return False
            
            quantity = order.get('quantity', 1)
            side = order.get('side', 'BUY')
            entry_price = order.get('entry_price', 0.0)
            
            if side.upper() == 'BUY':
                pnl = (exit_price - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price) * quantity
            
            closed_at = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).isoformat()
            update_payload = {
                'status': 'CLOSED',
                'exit_price': exit_price,
                'pnl': round(pnl, 2),
                'closed_at': closed_at
            }
            if option_exit_price is not None:
                update_payload['option_exit_price'] = option_exit_price

            success = self.update_order(order_id, update_payload)
            
            if success:
                self.update_daily_summary(round(pnl, 2), pnl > 0)
            
            return success
        except Exception as e:
            logger.error(f"Error closing order: {str(e)}")
            return False

    def get_order_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get aggregate order summary for a date range"""
        try:
            cursor = self.connection.cursor()
            params = []
            query = '''
                SELECT
                    COUNT(*) AS total_orders,
                    SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) AS closed_orders,
                    SUM(CASE WHEN status IN ('PLACED', 'PARTIAL') THEN 1 ELSE 0 END) AS open_orders,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS winning_orders,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) AS losing_orders,
                    SUM(pnl) AS total_pnl
                FROM orders
            '''
            if start_date and end_date:
                query += ' WHERE DATE(created_at) BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            elif start_date:
                query += ' WHERE DATE(created_at) >= ?'
                params.append(start_date)
            elif end_date:
                query += ' WHERE DATE(created_at) <= ?'
                params.append(end_date)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row:
                return {
                    'total_orders': 0,
                    'closed_orders': 0,
                    'open_orders': 0,
                    'winning_orders': 0,
                    'losing_orders': 0,
                    'total_pnl': 0.0
                }
            
            return {
                'total_orders': row['total_orders'] or 0,
                'closed_orders': row['closed_orders'] or 0,
                'open_orders': row['open_orders'] or 0,
                'winning_orders': row['winning_orders'] or 0,
                'losing_orders': row['losing_orders'] or 0,
                'total_pnl': round(row['total_pnl'] or 0.0, 2)
            }
        except Exception as e:
            logger.error(f"Error fetching order summary: {str(e)}")
            return {
                'total_orders': 0,
                'closed_orders': 0,
                'open_orders': 0,
                'winning_orders': 0,
                'losing_orders': 0,
                'total_pnl': 0.0
            }
    
    def insert_option_chain_summary(self, summary_data: Dict) -> Optional[int]:
        """Insert option chain analysis summary"""
        try:
            cursor = self.connection.cursor()
            # created_at in IST
            ist = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).isoformat()
            
            cursor.execute('''
                INSERT INTO option_chain_summary 
                (index_name, interval_minutes, trend, confidence, current_price, 
                 sma_9, sma_20, sma_50, rsi, macd, signal_line, 
                 bb_upper, bb_middle, bb_lower, atr, bullish_signals, bearish_signals, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                summary_data.get('index_name'),
                summary_data.get('interval_minutes'),
                summary_data.get('trend'),
                summary_data.get('confidence'),
                summary_data.get('current_price'),
                summary_data.get('sma_9'),
                summary_data.get('sma_20'),
                summary_data.get('sma_50'),
                summary_data.get('rsi'),
                summary_data.get('macd'),
                summary_data.get('signal_line'),
                summary_data.get('bb_upper'),
                summary_data.get('bb_middle'),
                summary_data.get('bb_lower'),
                summary_data.get('atr'),
                summary_data.get('bullish_signals'),
                summary_data.get('bearish_signals'),
                ist
            ))
            
            self.connection.commit()
            logger.info(f"Option chain summary inserted: {summary_data.get('index_name')} {summary_data.get('interval_minutes')}min")
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error inserting option chain summary: {str(e)}")
            return None
    
    def insert_trading_signal(self, signal_data: Dict) -> Optional[int]:
        """Insert trading signal"""
        try:
            cursor = self.connection.cursor()
            ist = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).isoformat()

            cursor.execute('''
                INSERT INTO trading_signals 
                (index_name, signal_type, signal_strength, bullish_count, bearish_count, neutral_count, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_data.get('index_name'),
                signal_data.get('signal_type'),
                signal_data.get('signal_strength'),
                signal_data.get('bullish_count'),
                signal_data.get('bearish_count'),
                signal_data.get('neutral_count'),
                json.dumps(signal_data.get('details', {})),
                ist
            ))
            
            self.connection.commit()
            logger.info(f"Trading signal inserted: {signal_data.get('index_name')}")
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error inserting trading signal: {str(e)}")
            return None
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM orders WHERE status IN ('PLACED', 'PARTIAL')")
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error fetching active orders: {str(e)}")
            return []
    
    def get_today_orders(self) -> List[Dict]:
        """Get today's orders"""
        try:
            cursor = self.connection.cursor()
            # Compute today's date in IST and query by that date
            ist_today = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT * FROM orders 
                WHERE DATE(created_at) = ?
                ORDER BY created_at DESC
            ''', (ist_today,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error fetching today's orders: {str(e)}")
            return []
    
    def get_today_summary(self) -> Dict:
        """Get today's trading summary"""
        try:
            cursor = self.connection.cursor()
            
            # Use IST date for daily summary
            today = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT * FROM daily_summary 
                WHERE trading_date = ?
            ''', (today,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0,
                'roi': 0
            }
            
        except Exception as e:
            logger.error(f"Error fetching today's summary: {str(e)}")
            return {}
    
    def update_daily_summary(self, pnl: float, is_win: bool) -> bool:
        """Update daily summary with new trade"""
        try:
            cursor = self.connection.cursor()
            # Use IST date
            today = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d')
            
            # Check if record exists
            cursor.execute("SELECT id FROM daily_summary WHERE trading_date = ?", (today,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE daily_summary 
                    SET total_trades = total_trades + 1,
                        winning_trades = winning_trades + ?,
                        losing_trades = losing_trades + ?,
                        total_pnl = total_pnl + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE trading_date = ?
                ''', (1 if is_win else 0, 0 if is_win else 1, pnl, today))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO daily_summary (trading_date, total_trades, winning_trades, losing_trades, total_pnl)
                    VALUES (?, 1, ?, ?, ?)
                ''', (today, 1 if is_win else 0, 0 if is_win else 1, pnl))
            
            self.connection.commit()
            logger.info(f"Daily summary updated: {pnl}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating daily summary: {str(e)}")
            return False
    
    def get_option_chain_history(self, index: str, interval: int, limit: int = 50) -> List[Dict]:
        """Get option chain history for an index and interval"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM option_chain_summary 
                WHERE index_name = ? AND interval_minutes = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (index, interval, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error fetching option chain history: {str(e)}")
            return []
    
    def close(self):
        """Close database connection"""
        try:
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {str(e)}")
    
    def export_to_csv(self, table_name: str, filename: str = None) -> bool:
        """Export table to CSV"""
        try:
            import pandas as pd
            # Ensure export folder exists: data/exports/<table_name>/
            base_dir = f"data/exports/{table_name}"
            import os
            os.makedirs(base_dir, exist_ok=True)

            if not filename:
                filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            out_path = os.path.join(base_dir, filename)

            cursor = self.connection.cursor()
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.connection)
            df.to_csv(out_path, index=False)

            logger.info(f"Data exported to {out_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test database
    db = TradingDatabase()
    
    # Insert sample order
    order = db.insert_order({
        'order_id': 'TEST123',
        'symbol': 'NIFTY05MAY2411000CE',
        'side': 'BUY',
        'quantity': 1,
        'entry_price': 150.00,
        'stop_loss': 148.50,
        'target': 152.00,
        'status': 'PLACED'
    })
    
    print(f"Order inserted with ID: {order}")
    
    # Insert sample summary
    summary = db.insert_option_chain_summary({
        'index_name': 'NIFTY',
        'interval_minutes': 5,
        'trend': 'BULLISH',
        'confidence': 75.5,
        'current_price': 50000,
        'sma_9': 49950,
        'sma_20': 49900,
        'sma_50': 49850,
        'rsi': 65.5,
        'macd': 0.05,
        'signal_line': 0.03,
        'bb_upper': 50100,
        'bb_middle': 50000,
        'bb_lower': 49900,
        'atr': 150,
        'bullish_signals': 4,
        'bearish_signals': 1
    })
    
    print(f"Summary inserted with ID: {summary}")
    
    db.close()
