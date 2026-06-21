"""
Database Query Utility
Provides helper functions to query and display trading data
"""

import logging
from database import TradingDatabase
from tabulate import tabulate
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseQueryHelper:
    """Helper class to query and display database data"""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db = TradingDatabase(db_path)
    
    def display_today_orders(self):
        """Display all orders from today"""
        try:
            orders = self.db.get_today_orders()
            
            if not orders:
                print("No orders found for today")
                return
            
            print("\n" + "="*120)
            print("TODAY'S ORDERS")
            print("="*120)
            
            # Prepare data for table
            table_data = []
            for order in orders:
                table_data.append([
                    order['order_id'],
                    order['symbol'],
                    order['side'],
                    order['quantity'],
                    f"INR{order['entry_price']:.2f}",
                    f"INR{order['stop_loss']:.2f}",
                    f"INR{order['target']:.2f}",
                    order['status'],
                    f"INR{order['pnl']:.2f}" if order['pnl'] else "N/A",
                    order['created_at']
                ])
            
            headers = ["Order ID", "Symbol", "Side", "Qty", "Entry", "SL", "Target", "Status", "P&L", "Created"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print(f"\nTotal Orders Today: {len(orders)}")
            
        except Exception as e:
            logger.error(f"Error displaying today's orders: {str(e)}")
    
    def display_active_orders(self):
        """Display all active orders"""
        try:
            orders = self.db.get_active_orders()
            
            if not orders:
                print("No active orders")
                return
            
            print("\n" + "="*120)
            print("ACTIVE ORDERS")
            print("="*120)
            
            table_data = []
            for order in orders:
                table_data.append([
                    order['order_id'],
                    order['symbol'],
                    order['side'],
                    order['quantity'],
                    f"INR{order['entry_price']:.2f}",
                    f"INR{order['stop_loss']:.2f}",
                    f"INR{order['target']:.2f}",
                    order['status'],
                    order['created_at']
                ])
            
            headers = ["Order ID", "Symbol", "Side", "Qty", "Entry", "SL", "Target", "Status", "Created"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print(f"\nActive Orders: {len(orders)}")
            
        except Exception as e:
            logger.error(f"Error displaying active orders: {str(e)}")
    
    def display_option_chain_history(self, index: str, interval: int, limit: int = 10):
        """Display option chain history for an index and interval"""
        try:
            history = self.db.get_option_chain_history(index, interval, limit)
            
            if not history:
                print(f"No history found for {index} {interval}min")
                return
            
            print("\n" + "="*140)
            print(f"OPTION CHAIN HISTORY - {index} ({interval}min)")
            print("="*140)
            
            table_data = []
            for record in history:
                table_data.append([
                    record['created_at'],
                    record['trend'],
                    f"{record['confidence']:.2f}%",
                    f"INR{record['current_price']:.2f}",
                    f"{record['rsi']:.2f}",
                    f"{record['macd']:.4f}",
                    f"{record['bullish_signals']} bullish / {record['bearish_signals']} bearish"
                ])
            
            headers = ["Timestamp", "Trend", "Confidence", "Price", "RSI", "MACD", "Signals"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print(f"\nRecords: {len(history)}")
            
        except Exception as e:
            logger.error(f"Error displaying option chain history: {str(e)}")
    
    def display_trading_signals(self, limit: int = 20):
        """Display recent trading signals"""
        try:
            import sqlite3
            cursor = self.db.connection.cursor()
            
            cursor.execute('''
                SELECT id, index_name, signal_type, signal_strength, created_at 
                FROM trading_signals 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            signals = cursor.fetchall()
            
            if not signals:
                print("No trading signals found")
                return
            
            print("\n" + "="*100)
            print("RECENT TRADING SIGNALS")
            print("="*100)
            
            table_data = []
            for signal in signals:
                table_data.append([
                    signal[0],
                    signal[1],
                    signal[2],
                    f"{signal[3]:.2f}",
                    signal[4]
                ])
            
            headers = ["ID", "Index", "Signal", "Strength", "Timestamp"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print(f"\nTotal Signals: {len(signals)}")
            
        except Exception as e:
            logger.error(f"Error displaying trading signals: {str(e)}")
    
    def display_today_summary(self):
        """Display today's trading summary"""
        try:
            summary = self.db.get_today_summary()
            
            print("\n" + "="*60)
            print("TODAY'S TRADING SUMMARY")
            print("="*60)
            print(f"Total Trades:    {summary.get('total_trades', 0)}")
            print(f"Winning Trades:  {summary.get('winning_trades', 0)}")
            print(f"Losing Trades:   {summary.get('losing_trades', 0)}")
            print(f"Total P&L:       INR{summary.get('total_pnl', 0):.2f}")
            print(f"ROI:             {summary.get('roi', 0):.2f}%")
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"Error displaying today's summary: {str(e)}")
    
    def display_stats(self):
        """Display database statistics"""
        try:
            import sqlite3
            cursor = self.db.connection.cursor()
            
            # Count records in each table
            tables = ['orders', 'option_chain_summary', 'trading_signals', 'daily_summary']
            
            print("\n" + "="*60)
            print("DATABASE STATISTICS")
            print("="*60)
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table:25s}: {count:,} records")
            
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"Error displaying stats: {str(e)}")
    
    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main function to demonstrate database queries"""
    
    print("\n" + "="*120)
    print("TRADING BOT DATABASE QUERY UTILITY")
    print("="*120 + "\n")
    
    try:
        helper = DatabaseQueryHelper()
        
        # Display statistics
        helper.display_stats()
        
        # Display today's summary
        helper.display_today_summary()
        
        # Display today's orders
        helper.display_today_orders()
        
        # Display active orders
        helper.display_active_orders()
        
        # Display recent trading signals
        helper.display_trading_signals(limit=10)
        
        # Display option chain history for NIFTY 5-minute interval
        helper.display_option_chain_history("NIFTY", 5, limit=10)
        
        helper.close()
        
        print("\nQuery completed successfully\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
