import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Trend(Enum):
    """Trend direction"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class TrendAnalyzer:
    """Analyze market trends using technical indicators"""
    
    @staticmethod
    def calculate_sma(data: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        return pd.Series(data).rolling(window=period).mean().tolist()
    
    @staticmethod
    def calculate_ema(data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        return pd.Series(data).ewm(span=period, adjust=False).mean().tolist()
    
    @staticmethod
    def calculate_rsi(data: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index
        
        Args:
            data: List of closing prices
            period: RSI period (default 14)
        
        Returns:
            RSI value (0-100)
        """
        if len(data) < period:
            return None
        
        deltas = np.diff(data)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        for d in deltas[period+1:]:
            if d >= 0:
                up = (up * (period - 1) + d) / period
                down = (down * (period - 1)) / period
            else:
                up = (up * (period - 1)) / period
                down = (down * (period - 1) - d) / period
            
            rs = up / down if down != 0 else 0
            rsi = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Returns:
            Dictionary with MACD line, signal line, and histogram
        """
        series = pd.Series(data)
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line.iloc[-1],
            "signal": signal_line.iloc[-1],
            "histogram": histogram.iloc[-1]
        }
    
    @staticmethod
    def calculate_bollinger_bands(data: List[float], period: int = 20, std_dev: int = 2) -> Dict:
        """
        Calculate Bollinger Bands
        
        Returns:
            Dictionary with upper, middle, and lower bands
        """
        series = pd.Series(data)
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            "upper": upper_band.iloc[-1],
            "middle": sma.iloc[-1],
            "lower": lower_band.iloc[-1],
            "current": data[-1]
        }
    
    @staticmethod
    def calculate_atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> float:
        """
        Calculate Average True Range
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of closing prices
            period: ATR period
        
        Returns:
            ATR value
        """
        if len(close) < period:
            return None
        
        high_low = np.array(high) - np.array(low)
        high_close = np.abs(np.array(high) - np.array(close[:-1]))
        low_close = np.abs(np.array(low) - np.array(close[:-1]))
        
        tr = np.maximum(high_low[1:], high_close, low_close)
        atr = np.mean(tr[-period:])
        
        return atr
    
    @staticmethod
    def analyze_trend(ohlc_data: Dict, threshold: float = 2.0) -> Dict:
        """
        Analyze trend based on multiple indicators
        
        Args:
            ohlc_data: Dictionary with open, high, low, close prices
            threshold: Percentage threshold for trend confirmation
        
        Returns:
            Dictionary with trend analysis results
        """
        try:
            close_prices = ohlc_data.get("close", [])
            
            if not close_prices or len(close_prices) < 26:
                return {
                    "trend": Trend.NEUTRAL.value,
                    "confidence": 0,
                    "reason": "Insufficient data"
                }
            
            # Calculate indicators
            sma_9 = TrendAnalyzer.calculate_sma(close_prices, 9)[-1]
            sma_20 = TrendAnalyzer.calculate_sma(close_prices, 20)[-1]
            sma_50 = TrendAnalyzer.calculate_sma(close_prices, 50) if len(close_prices) >= 50 else [None]
            sma_50 = sma_50[-1] if sma_50[-1] is not None else sma_20
            
            rsi = TrendAnalyzer.calculate_rsi(close_prices, 14)
            macd = TrendAnalyzer.calculate_macd(close_prices)
            
            current_price = close_prices[-1]
            
            # Determine trend
            trend_signals = 0
            bullish_signals = 0
            bearish_signals = 0
            
            # SMA signals
            if sma_9 > sma_20:
                bullish_signals += 1
                trend_signals += 1
            elif sma_9 < sma_20:
                bearish_signals += 1
                trend_signals += 1
            
            if sma_20 > sma_50:
                bullish_signals += 1
                trend_signals += 1
            elif sma_20 < sma_50:
                bearish_signals += 1
                trend_signals += 1
            
            # RSI signals
            if rsi > 70:
                bearish_signals += 1
                trend_signals += 1
            elif rsi < 30:
                bullish_signals += 1
                trend_signals += 1
            elif rsi > 50:
                bullish_signals += 0.5
            elif rsi < 50:
                bearish_signals += 0.5
            
            # MACD signals
            if macd["macd"] > macd["signal"]:
                bullish_signals += 1
                trend_signals += 1
            else:
                bearish_signals += 1
                trend_signals += 1
            
            # Determine final trend
            if bullish_signals > bearish_signals:
                trend = Trend.BULLISH.value
            elif bearish_signals > bullish_signals:
                trend = Trend.BEARISH.value
            else:
                trend = Trend.NEUTRAL.value
            
            confidence = min(100, (abs(bullish_signals - bearish_signals) / trend_signals) * 100) if trend_signals > 0 else 0
            
            return {
                "trend": trend,
                "confidence": round(confidence, 2),
                "current_price": current_price,
                "sma_9": round(sma_9, 2),
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "rsi": round(rsi, 2),
                "macd": round(macd["macd"], 4),
                "signal": round(macd["signal"], 4),
                "bullish_signals": bullish_signals,
                "bearish_signals": bearish_signals
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_trend: {str(e)}")
            return {
                "trend": Trend.NEUTRAL.value,
                "confidence": 0,
                "error": str(e)
            }
    
    @staticmethod
    def get_entry_exit_points(ohlc_data: Dict, risk_reward_ratio: float = 2.0) -> Dict:
        """
        Get entry, stop loss, and target prices based on technical analysis
        
        Args:
            ohlc_data: Dictionary with OHLC data
            risk_reward_ratio: Risk to reward ratio for targets
        
        Returns:
            Dictionary with entry, SL, and target prices
        """
        try:
            close_prices = ohlc_data.get("close", [])
            high_prices = ohlc_data.get("high", [])
            low_prices = ohlc_data.get("low", [])
            
            if not close_prices or len(close_prices) < 14:
                return None
            
            current_price = close_prices[-1]
            
            # Calculate ATR for volatility
            atr = TrendAnalyzer.calculate_atr(high_prices, low_prices, close_prices, 14)
            
            # Calculate Bollinger Bands for support/resistance
            bb = TrendAnalyzer.calculate_bollinger_bands(close_prices, 20, 2)
            
            # Determine entry, SL, and target based on trend
            analysis = TrendAnalyzer.analyze_trend(ohlc_data)
            trend = analysis["trend"]
            
            if trend == Trend.BULLISH.value:
                entry_price = current_price
                sl_price = current_price - (atr * 1.5)
                risk = entry_price - sl_price
                target_price = entry_price + (risk * risk_reward_ratio)
            elif trend == Trend.BEARISH.value:
                entry_price = current_price
                sl_price = current_price + (atr * 1.5)
                risk = sl_price - entry_price
                target_price = entry_price - (risk * risk_reward_ratio)
            else:
                return None
            
            return {
                "entry": round(entry_price, 2),
                "stop_loss": round(sl_price, 2),
                "target": round(target_price, 2),
                "atr": round(atr, 2),
                "bb_upper": round(bb["upper"], 2),
                "bb_lower": round(bb["lower"], 2)
            }
            
        except Exception as e:
            logger.error(f"Error in get_entry_exit_points: {str(e)}")
            return None
