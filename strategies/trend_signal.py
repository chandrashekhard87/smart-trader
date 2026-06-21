from .base import StrategyBase
import logging
from datetime import datetime
from config import UPDATE_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

class TrendSignalStrategy(StrategyBase):
    def name(self) -> str:
        return "trend_signal"

    def analyze_and_trade(self, bot, index: str) -> None:
        """Wraps existing trend analysis and trading logic for a single index."""
        # Fetch latest market data
        if not bot.fetch_market_data(index):
            logger.warning(f"Strategy {self.name()}: failed to fetch market data for {index}")
            return

        # Save summaries per interval
        for interval in bot.OPTION_CHAIN_INTERVALS:
            analysis = bot.analyze_index_trend(index, interval)
            if analysis:
                summary_data = {
                    'index_name': index,
                    'interval_minutes': interval,
                    'trend': analysis.get('trend'),
                    'confidence': analysis.get('confidence'),
                    'current_price': analysis.get('current_price'),
                    'sma_9': analysis.get('sma_9'),
                    'sma_20': analysis.get('sma_20'),
                    'sma_50': analysis.get('sma_50'),
                    'rsi': analysis.get('rsi'),
                    'macd': analysis.get('macd'),
                    'signal_line': analysis.get('signal'),
                    'bullish_signals': analysis.get('bullish_signals'),
                    'bearish_signals': analysis.get('bearish_signals')
                }
                bot.database.insert_option_chain_summary(summary_data)

        # Overall trading signal
        signal = bot.get_trading_signal(index)
        if signal:
            logger.info(f"Strategy {self.name()} - {index} Signal: {signal['signal']} (Strength: {signal['strength']:.2f})")
            now = datetime.now()
            last = bot.last_signal_time.get(index)
            allow_insert = False
            if last is None:
                allow_insert = True
            else:
                elapsed = (now - last).total_seconds()
                if elapsed >= UPDATE_INTERVAL_SECONDS:
                    allow_insert = True

            if allow_insert:
                signal_data = {
                    'index_name': index,
                    'signal_type': signal['signal'],
                    'signal_strength': signal['strength'],
                    'bullish_count': signal['details'].get('5min', {}).get('bullish_signals', 0),
                    'bearish_count': signal['details'].get('5min', {}).get('bearish_signals', 0),
                    'neutral_count': 0,
                    'details': signal
                }
                bot.database.insert_trading_signal(signal_data)
                bot.last_signal_time[index] = now

                # Place trade if strength threshold met
                if signal['strength'] >= 50.0:
                    bot.place_option_trade(index, option_type='CE')
        else:
            logger.debug(f"Strategy {self.name()} - No clear signal for {index}")
