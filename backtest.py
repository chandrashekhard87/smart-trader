"""
Backtesting module for option chain trading strategies
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import pandas as pd
from trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class Backtest:
    """Backtest trading strategies on historical data"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.portfolio_history = []
    
    def load_historical_data(self, filepath: str) -> Optional[pd.DataFrame]:
        """Load historical OHLC data from CSV file"""
        try:
            df = pd.read_csv(filepath)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            return df
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return None
    
    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate trading signals from historical data"""
        signals = []
        
        try:
            for idx in range(50, len(df)):
                close_prices = df['close'].iloc[idx-50:idx].tolist()
                high_prices = df['high'].iloc[idx-50:idx].tolist()
                low_prices = df['low'].iloc[idx-50:idx].tolist()
                
                ohlc_data = {
                    "open": df['open'].iloc[idx-50:idx].tolist(),
                    "high": high_prices,
                    "low": low_prices,
                    "close": close_prices
                }
                
                analysis = TrendAnalyzer.analyze_trend(ohlc_data)
                current_row = df.iloc[idx]
                
                signal = {
                    "timestamp": current_row['timestamp'],
                    "price": current_row['close'],
                    "trend": analysis.get("trend"),
                    "confidence": analysis.get("confidence"),
                    "rsi": analysis.get("rsi")
                }
                
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
        
        return signals
    
    def backtest_strategy(self, signals: List[Dict], sl_percent: float = 1.0,
                         target_percent: float = 2.0) -> Dict:
        """
        Backtest a trading strategy
        
        Args:
            signals: List of trading signals
            sl_percent: Stop loss percentage
            target_percent: Target profit percentage
        
        Returns:
            Backtest results summary
        """
        try:
            self.trades = []
            active_trade = None
            
            for signal in signals:
                current_price = signal['price']
                timestamp = signal['timestamp']
                
                # Close existing trade if target or SL hit
                if active_trade:
                    sl_price = active_trade['entry'] * (1 - sl_percent / 100)
                    target_price = active_trade['entry'] * (1 + target_percent / 100)
                    
                    if current_price <= sl_price:
                        # Stop loss hit
                        pnl = current_price - active_trade['entry']
                        active_trade['exit'] = current_price
                        active_trade['pnl'] = pnl
                        active_trade['exit_reason'] = 'SL'
                        self.capital += pnl
                        self.trades.append(active_trade)
                        active_trade = None
                    
                    elif current_price >= target_price:
                        # Target hit
                        pnl = target_price - active_trade['entry']
                        active_trade['exit'] = target_price
                        active_trade['pnl'] = pnl
                        active_trade['exit_reason'] = 'TARGET'
                        self.capital += pnl
                        self.trades.append(active_trade)
                        active_trade = None
                
                # Open new trade if strong signal
                if not active_trade and signal['confidence'] > 60:
                    if signal['trend'] == 'BULLISH':
                        active_trade = {
                            'entry': current_price,
                            'entry_timestamp': timestamp,
                            'side': 'BUY',
                            'signal_confidence': signal['confidence']
                        }
                    elif signal['trend'] == 'BEARISH':
                        active_trade = {
                            'entry': current_price,
                            'entry_timestamp': timestamp,
                            'side': 'SELL',
                            'signal_confidence': signal['confidence']
                        }
                
                # Record portfolio state
                self.portfolio_history.append({
                    'timestamp': timestamp,
                    'capital': self.capital,
                    'active_trade': active_trade is not None
                })
            
            # Close final trade if open
            if active_trade and signals:
                pnl = signals[-1]['price'] - active_trade['entry']
                active_trade['exit'] = signals[-1]['price']
                active_trade['pnl'] = pnl
                active_trade['exit_reason'] = 'EOD'
                self.capital += pnl
                self.trades.append(active_trade)
            
            return self.get_backtest_summary()
            
        except Exception as e:
            logger.error(f"Error in backtest_strategy: {str(e)}")
            return {}
    
    def get_backtest_summary(self) -> Dict:
        """Get backtest results summary"""
        try:
            total_trades = len(self.trades)
            winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in self.trades if t.get('pnl', 0) < 0])
            
            total_profit = sum(t.get('pnl', 0) for t in self.trades if t.get('pnl', 0) > 0)
            total_loss = sum(t.get('pnl', 0) for t in self.trades if t.get('pnl', 0) < 0)
            net_pnl = total_profit + total_loss
            
            roi = (net_pnl / self.initial_capital) * 100
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            avg_win = total_profit / winning_trades if winning_trades > 0 else 0
            avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
            
            profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_profit': round(total_profit, 2),
                'total_loss': round(total_loss, 2),
                'net_pnl': round(net_pnl, 2),
                'roi': round(roi, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'final_capital': round(self.capital, 2)
            }
        except Exception as e:
            logger.error(f"Error in get_backtest_summary: {str(e)}")
            return {}
    
    def export_results(self, filename: str = "backtest_results.json"):
        """Export backtest results to file"""
        try:
            results = {
                'summary': self.get_backtest_summary(),
                'trades': self.trades
            }
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Backtest results exported to {filename}")
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")


def run_backtest(data_file: str = "historical_data.csv", 
                 sl_percent: float = 1.0, target_percent: float = 2.0):
    """Run a backtest on historical data"""
    try:
        backtest = Backtest(initial_capital=100000)
        
        # Load historical data
        df = backtest.load_historical_data(data_file)
        if df is None:
            return
        
        # Generate signals
        signals = backtest.generate_signals(df)
        logger.info(f"Generated {len(signals)} signals")
        
        # Run backtest
        results = backtest.backtest_strategy(signals, sl_percent, target_percent)
        
        # Print results
        logger.info("Backtest Results:")
        for key, value in results.items():
            logger.info(f"  {key}: {value}")
        
        # Export results
        backtest.export_results()
        
    except Exception as e:
        logger.error(f"Error in run_backtest: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_backtest()
