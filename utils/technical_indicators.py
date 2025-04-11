import numpy as np
import pandas as pd
from typing import Tuple

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI) for a given price series.
    
    Args:
        prices: Series of prices
        period: Period for RSI calculation (default: 14)
    
    Returns:
        Series with RSI values
    """
    delta = prices.diff()
    
    # Make two series: one for gains and one for losses
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    
    # First average
    avg_gain = gains.rolling(window=period, min_periods=1).mean()
    avg_loss = losses.rolling(window=period, min_periods=1).mean()
    
    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate the Moving Average Convergence Divergence (MACD) for a given price series.
    
    Args:
        prices: Series of prices
        fast_period: Period for fast EMA (default: 12)
        slow_period: Period for slow EMA (default: 26)
        signal_period: Period for signal line (default: 9)
    
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    # Calculate fast and slow EMAs
    ema_fast = prices.ewm(span=fast_period, min_periods=fast_period).mean()
    ema_slow = prices.ewm(span=slow_period, min_periods=slow_period).mean()
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate Signal line
    signal_line = macd_line.ewm(span=signal_period, min_periods=signal_period).mean()
    
    # Calculate Histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands for a given price series.
    
    Args:
        prices: Series of prices
        period: Period for moving average (default: 20)
        num_std: Number of standard deviations for the bands (default: 2.0)
    
    Returns:
        Tuple of (Upper Band, Middle Band, Lower Band)
    """
    # Calculate middle band (SMA)
    middle_band = prices.rolling(window=period).mean()
    
    # Calculate standard deviation
    std = prices.rolling(window=period).std()
    
    # Calculate upper and lower bands
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    
    return upper_band, middle_band, lower_band

def calculate_moving_averages(prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate multiple Simple Moving Averages for a given price series.
    
    Args:
        prices: Series of prices
    
    Returns:
        Tuple of (SMA20, SMA50, SMA200)
    """
    # Calculate the various SMAs
    sma_20 = prices.rolling(window=20).mean()
    sma_50 = prices.rolling(window=50).mean()
    sma_200 = prices.rolling(window=200).mean()
    
    return sma_20, sma_50, sma_200

def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate the Average True Range (ATR) for a given price data.
    
    Args:
        data: DataFrame with OHLC price data
        period: Period for ATR calculation (default: 14)
    
    Returns:
        Series with ATR values
    """
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    # Calculate True Range
    tr1 = abs(high - low)
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR
    atr = tr.rolling(window=period).mean()
    
    return atr

def calculate_stochastic_oscillator(data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate the Stochastic Oscillator for a given price data.
    
    Args:
        data: DataFrame with OHLC price data
        k_period: Period for %K calculation (default: 14)
        d_period: Period for %D calculation (default: 3)
    
    Returns:
        Tuple of (%K, %D)
    """
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    # Calculate %K
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    
    # Calculate %D (3-day SMA of %K)
    d_percent = k_percent.rolling(window=d_period).mean()
    
    return k_percent, d_percent

def calculate_fibonacci_retracement(data: pd.DataFrame, is_uptrend: bool = True) -> dict:
    """
    Calculate Fibonacci retracement levels based on high and low points.
    
    Args:
        data: DataFrame with OHLC price data
        is_uptrend: If True, calculate for uptrend, otherwise for downtrend
    
    Returns:
        Dictionary with Fibonacci levels
    """
    if is_uptrend:
        # For uptrend: from low to high
        low_price = data['Low'].min()
        high_price = data['High'].max()
    else:
        # For downtrend: from high to low
        high_price = data['High'].max()
        low_price = data['Low'].min()
    
    diff = high_price - low_price
    
    # Calculate the Fibonacci levels
    levels = {
        "0.0": low_price,
        "0.236": low_price + 0.236 * diff,
        "0.382": low_price + 0.382 * diff,
        "0.5": low_price + 0.5 * diff,
        "0.618": low_price + 0.618 * diff,
        "0.786": low_price + 0.786 * diff,
        "1.0": high_price
    }
    
    return levels
