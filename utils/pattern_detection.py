import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from typing import List, Tuple, Union, Dict

def detect_double_bottom(data: pd.DataFrame, sensitivity: int = 5, window: int = 20) -> List[List[int]]:
    """
    Detects double bottom patterns in price data.
    
    Args:
        data: DataFrame with OHLC price data
        sensitivity: Adjusts the sensitivity of detection (1-10, higher is more sensitive)
        window: The size of the window for pattern detection
        
    Returns:
        List of indices where double bottoms are detected
    """
    # Convert sensitivity to parameters
    tolerance = 0.03 * (11 - sensitivity)  # Higher sensitivity = lower tolerance
    min_distance = max(5, int(window * 0.7 * (11 - sensitivity) / 10))
    
    close_prices = data['Close'].values
    lows = data['Low'].values
    
    # Find local minima
    order = max(int(window / 4), 1)
    min_idx = list(argrelextrema(lows, np.less_equal, order=order)[0])
    
    double_bottoms = []
    
    for i in range(len(min_idx) - 1):
        for j in range(i + 1, len(min_idx)):
            idx1, idx2 = min_idx[i], min_idx[j]
            
            # Check if the two bottoms are far enough apart
            if idx2 - idx1 < min_distance:
                continue
            
            # Check if the bottoms are at similar price levels
            price1, price2 = lows[idx1], lows[idx2]
            if abs(price1 - price2) / price1 > tolerance:
                continue
            
            # Check if there's a significant rise between the bottoms
            max_between = np.max(close_prices[idx1:idx2])
            rise1 = (max_between - price1) / price1
            rise2 = (max_between - price2) / price2
            
            if rise1 < 0.02 or rise2 < 0.02:  # Not enough rise between bottoms
                continue
            
            # Confirmation: price should rise after the second bottom
            if idx2 + 5 < len(close_prices):
                confirmation = close_prices[idx2 + 5] > price2
            else:
                confirmation = close_prices[-1] > price2
            
            if confirmation:
                double_bottoms.append([idx1, idx2])
    
    return double_bottoms

def detect_double_top(data: pd.DataFrame, sensitivity: int = 5, window: int = 20) -> List[List[int]]:
    """
    Detects double top patterns in price data.
    
    Args:
        data: DataFrame with OHLC price data
        sensitivity: Adjusts the sensitivity of detection (1-10, higher is more sensitive)
        window: The size of the window for pattern detection
        
    Returns:
        List of indices where double tops are detected
    """
    # Convert sensitivity to parameters
    tolerance = 0.03 * (11 - sensitivity)  # Higher sensitivity = lower tolerance
    min_distance = max(5, int(window * 0.7 * (11 - sensitivity) / 10))
    
    close_prices = data['Close'].values
    highs = data['High'].values
    
    # Find local maxima
    order = max(int(window / 4), 1)
    max_idx = list(argrelextrema(highs, np.greater_equal, order=order)[0])
    
    double_tops = []
    
    for i in range(len(max_idx) - 1):
        for j in range(i + 1, len(max_idx)):
            idx1, idx2 = max_idx[i], max_idx[j]
            
            # Check if the two tops are far enough apart
            if idx2 - idx1 < min_distance:
                continue
            
            # Check if the tops are at similar price levels
            price1, price2 = highs[idx1], highs[idx2]
            if abs(price1 - price2) / price1 > tolerance:
                continue
            
            # Check if there's a significant drop between the tops
            min_between = np.min(close_prices[idx1:idx2])
            drop1 = (price1 - min_between) / price1
            drop2 = (price2 - min_between) / price2
            
            if drop1 < 0.02 or drop2 < 0.02:  # Not enough drop between tops
                continue
            
            # Confirmation: price should drop after the second top
            if idx2 + 5 < len(close_prices):
                confirmation = close_prices[idx2 + 5] < price2
            else:
                confirmation = close_prices[-1] < price2
            
            if confirmation:
                double_tops.append([idx1, idx2])
    
    return double_tops

def detect_head_and_shoulders(data: pd.DataFrame, sensitivity: int = 5, window: int = 30) -> List[List[int]]:
    """
    Detects head and shoulders patterns in price data.
    
    Args:
        data: DataFrame with OHLC price data
        sensitivity: Adjusts the sensitivity of detection (1-10, higher is more sensitive)
        window: The size of the window for pattern detection
        
    Returns:
        List of indices where head and shoulders patterns are detected
    """
    # Convert sensitivity to parameters
    tolerance = 0.05 * (11 - sensitivity)  # Higher sensitivity = lower tolerance
    min_distance = max(3, int(window * 0.2 * (11 - sensitivity) / 10))
    
    highs = data['High'].values
    
    # Find local maxima
    order = max(int(window / 6), 1)
    max_idx = list(argrelextrema(highs, np.greater_equal, order=order)[0])
    
    patterns = []
    
    # Need at least 3 peaks
    if len(max_idx) < 3:
        return patterns
    
    for i in range(len(max_idx) - 2):
        # Get three consecutive peaks
        peak1_idx, peak2_idx, peak3_idx = max_idx[i], max_idx[i+1], max_idx[i+2]
        
        # Check spacing between peaks
        if peak2_idx - peak1_idx < min_distance or peak3_idx - peak2_idx < min_distance:
            continue
        
        # Get the peak prices
        peak1, peak2, peak3 = highs[peak1_idx], highs[peak2_idx], highs[peak3_idx]
        
        # Head should be higher than shoulders
        if peak2 <= peak1 or peak2 <= peak3:
            continue
        
        # Shoulders should be at similar heights
        if abs(peak1 - peak3) / peak1 > tolerance:
            continue
        
        # Find the troughs (neckline)
        trough1_idx = np.argmin(data['Low'].values[peak1_idx:peak2_idx]) + peak1_idx
        trough2_idx = np.argmin(data['Low'].values[peak2_idx:peak3_idx]) + peak2_idx
        
        # Neckline should be relatively flat
        trough1, trough2 = data['Low'].values[trough1_idx], data['Low'].values[trough2_idx]
        if abs(trough1 - trough2) / trough1 > tolerance:
            continue
        
        # Confirmation: check for break below neckline after the pattern
        if peak3_idx + 5 < len(highs):
            # Use the average of the two troughs as the neckline
            neckline = (trough1 + trough2) / 2
            confirmation = data['Close'].values[peak3_idx + 5] < neckline
        else:
            confirmation = data['Close'].values[-1] < data['Close'].values[peak3_idx]
        
        if confirmation:
            patterns.append([peak1_idx, trough1_idx, peak2_idx, trough2_idx, peak3_idx])
    
    return patterns

def detect_inverse_head_and_shoulders(data: pd.DataFrame, sensitivity: int = 5, window: int = 30) -> List[List[int]]:
    """
    Detects inverse head and shoulders patterns in price data.
    
    Args:
        data: DataFrame with OHLC price data
        sensitivity: Adjusts the sensitivity of detection (1-10, higher is more sensitive)
        window: The size of the window for pattern detection
        
    Returns:
        List of indices where inverse head and shoulders patterns are detected
    """
    # Convert sensitivity to parameters
    tolerance = 0.05 * (11 - sensitivity)  # Higher sensitivity = lower tolerance
    min_distance = max(3, int(window * 0.2 * (11 - sensitivity) / 10))
    
    lows = data['Low'].values
    
    # Find local minima
    order = max(int(window / 6), 1)
    min_idx = list(argrelextrema(lows, np.less_equal, order=order)[0])
    
    patterns = []
    
    # Need at least 3 troughs
    if len(min_idx) < 3:
        return patterns
    
    for i in range(len(min_idx) - 2):
        # Get three consecutive troughs
        trough1_idx, trough2_idx, trough3_idx = min_idx[i], min_idx[i+1], min_idx[i+2]
        
        # Check spacing between troughs
        if trough2_idx - trough1_idx < min_distance or trough3_idx - trough2_idx < min_distance:
            continue
        
        # Get the trough prices
        trough1, trough2, trough3 = lows[trough1_idx], lows[trough2_idx], lows[trough3_idx]
        
        # Head should be lower than shoulders
        if trough2 >= trough1 or trough2 >= trough3:
            continue
        
        # Shoulders should be at similar heights
        if abs(trough1 - trough3) / trough1 > tolerance:
            continue
        
        # Find the peaks (neckline)
        peak1_idx = np.argmax(data['High'].values[trough1_idx:trough2_idx]) + trough1_idx
        peak2_idx = np.argmax(data['High'].values[trough2_idx:trough3_idx]) + trough2_idx
        
        # Neckline should be relatively flat
        peak1, peak2 = data['High'].values[peak1_idx], data['High'].values[peak2_idx]
        if abs(peak1 - peak2) / peak1 > tolerance:
            continue
        
        # Confirmation: check for break above neckline after the pattern
        if trough3_idx + 5 < len(lows):
            # Use the average of the two peaks as the neckline
            neckline = (peak1 + peak2) / 2
            confirmation = data['Close'].values[trough3_idx + 5] > neckline
        else:
            confirmation = data['Close'].values[-1] > data['Close'].values[trough3_idx]
        
        if confirmation:
            patterns.append([trough1_idx, peak1_idx, trough2_idx, peak2_idx, trough3_idx])
    
    return patterns

def detect_triangle(data: pd.DataFrame, sensitivity: int = 5, window: int = 40) -> List[Dict]:
    """
    Detects triangle patterns (ascending, descending, symmetric) in price data.
    
    Args:
        data: DataFrame with OHLC price data
        sensitivity: Adjusts the sensitivity of detection (1-10, higher is more sensitive)
        window: The size of the window for pattern detection
        
    Returns:
        List of dictionaries with triangle pattern information
    """
    # Convert sensitivity to parameters
    min_points = 4 + sensitivity  # Higher sensitivity = fewer points needed
    min_duration = max(7, int(window * 0.5 * (11 - sensitivity) / 10))
    
    highs = data['High'].values
    lows = data['Low'].values
    
    # Find local maxima and minima
    order = max(int(window / 8), 1)
    max_idx = list(argrelextrema(highs, np.greater_equal, order=order)[0])
    min_idx = list(argrelextrema(lows, np.less_equal, order=order)[0])
    
    triangles = []
    
    # Need enough points to define a triangle
    if len(max_idx) < 3 or len(min_idx) < 3:
        return triangles
    
    # Check for symmetric triangles
    for i in range(len(max_idx) - 2):
        # Get three consecutive peaks
        peak1_idx, peak2_idx, peak3_idx = max_idx[i], max_idx[i+1], max_idx[i+2]
        
        # Check duration
        if peak3_idx - peak1_idx < min_duration:
            continue
        
        # Check for downward trend in peaks
        peak1, peak2, peak3 = highs[peak1_idx], highs[peak2_idx], highs[peak3_idx]
        if peak1 <= peak2 or peak2 <= peak3:
            continue
        
        # Find corresponding troughs
        troughs = [t for t in min_idx if t > peak1_idx and t < peak3_idx]
        if len(troughs) < 2:
            continue
        
        trough1_idx, trough2_idx = troughs[0], troughs[-1]
        trough1, trough2 = lows[trough1_idx], lows[trough2_idx]
        
        # Check for upward trend in troughs
        if trough1 >= trough2:
            continue
        
        # Calculate convergence point
        peak_slope = (peak3 - peak1) / (peak3_idx - peak1_idx)
        trough_slope = (trough2 - trough1) / (trough2_idx - trough1_idx)
        
        # Slopes should be opposite signs for convergence
        if peak_slope * trough_slope >= 0:
            continue
        
        # Calculate approximate convergence point
        if abs(peak_slope - trough_slope) > 1e-10:  # Avoid division by zero
            x_converge = (trough1 - peak1 - trough_slope * trough1_idx + peak_slope * peak1_idx) / (peak_slope - trough_slope)
            y_converge = peak1 + peak_slope * (x_converge - peak1_idx)
            
            # Convergence point should be reasonably ahead
            if x_converge < peak3_idx or x_converge > peak3_idx + window:
                continue
            
            # Check if price breaks out of the triangle
            if peak3_idx + 5 < len(highs):
                expected_price = peak1 + peak_slope * (peak3_idx + 5 - peak1_idx)
                actual_price = data['Close'].values[peak3_idx + 5]
                breakout = abs(actual_price - expected_price) / expected_price > 0.02
            else:
                breakout = False
            
            triangle_type = "Symmetric"
            triangles.append({
                'type': triangle_type,
                'points': [peak1_idx, trough1_idx, peak2_idx, trough2_idx, peak3_idx],
                'converge_x': int(x_converge),
                'converge_y': y_converge,
                'breakout': breakout
            })
    
    # Check for ascending triangles (horizontal resistance, rising support)
    for i in range(len(max_idx) - 2):
        peaks = max_idx[i:i+3]
        
        # Duration check
        if peaks[-1] - peaks[0] < min_duration:
            continue
        
        # Get peak prices
        peak_prices = highs[peaks]
        
        # Check for horizontal resistance (peaks should be at similar levels)
        if np.std(peak_prices) / np.mean(peak_prices) > 0.03:
            continue
        
        # Find troughs between the peaks
        troughs = [t for t in min_idx if t > peaks[0] and t < peaks[-1]]
        if len(troughs) < 2:
            continue
        
        # Get trough prices
        trough_prices = lows[troughs]
        
        # Check for rising support
        if not all(trough_prices[i] < trough_prices[i+1] for i in range(len(trough_prices)-1)):
            continue
        
        # Confirmation: breakout above resistance
        if peaks[-1] + 5 < len(highs):
            resistance = np.mean(peak_prices)
            breakout = data['Close'].values[peaks[-1] + 5] > resistance
        else:
            breakout = False
        
        triangles.append({
            'type': "Ascending",
            'points': [peaks[0], troughs[0], peaks[1], troughs[-1], peaks[-1]],
            'converge_x': peaks[-1] + min_duration,
            'converge_y': np.mean(peak_prices),
            'breakout': breakout
        })
    
    # Check for descending triangles (horizontal support, falling resistance)
    for i in range(len(min_idx) - 2):
        troughs = min_idx[i:i+3]
        
        # Duration check
        if troughs[-1] - troughs[0] < min_duration:
            continue
        
        # Get trough prices
        trough_prices = lows[troughs]
        
        # Check for horizontal support (troughs should be at similar levels)
        if np.std(trough_prices) / np.mean(trough_prices) > 0.03:
            continue
        
        # Find peaks between the troughs
        peaks = [p for p in max_idx if p > troughs[0] and p < troughs[-1]]
        if len(peaks) < 2:
            continue
        
        # Get peak prices
        peak_prices = highs[peaks]
        
        # Check for falling resistance
        if not all(peak_prices[i] > peak_prices[i+1] for i in range(len(peak_prices)-1)):
            continue
        
        # Confirmation: breakout below support
        if troughs[-1] + 5 < len(lows):
            support = np.mean(trough_prices)
            breakout = data['Close'].values[troughs[-1] + 5] < support
        else:
            breakout = False
        
        triangles.append({
            'type': "Descending",
            'points': [peaks[0], troughs[0], peaks[-1], troughs[1], troughs[-1]],
            'converge_x': troughs[-1] + min_duration,
            'converge_y': np.mean(trough_prices),
            'breakout': breakout
        })
    
    return triangles

def find_support_resistance(data: pd.DataFrame, sensitivity: int = 5, window: int = 30) -> Tuple[List[int], List[int]]:
    """
    Finds support and resistance levels in the price data.
    
    Args:
        data: DataFrame with OHLC price data
        sensitivity: Adjusts the sensitivity of detection (1-10, higher is more sensitive)
        window: The size of the window for detection
        
    Returns:
        Tuple of (support_indices, resistance_indices)
    """
    # Convert sensitivity to parameters
    num_touches = max(2, 6 - int(sensitivity / 2))  # Higher sensitivity = fewer touches required
    price_threshold = 0.02 * (11 - sensitivity)  # Higher sensitivity = lower threshold
    
    close_prices = data['Close'].values
    highs = data['High'].values
    lows = data['Low'].values
    
    # Find potential resistance levels (local highs)
    order = max(int(window / 5), 1)
    resistance_idx = list(argrelextrema(highs, np.greater_equal, order=order)[0])
    
    # Find potential support levels (local lows)
    support_idx = list(argrelextrema(lows, np.less_equal, order=order)[0])
    
    # Filter for significant support/resistance by counting price touches
    confirmed_supports = []
    confirmed_resistances = []
    
    # Check supports
    for idx in support_idx:
        support_price = lows[idx]
        touches = 0
        
        for i in range(len(lows)):
            # Skip the point itself
            if i == idx:
                continue
            
            # Count if price approaches within threshold
            if abs(lows[i] - support_price) / support_price < price_threshold:
                touches += 1
        
        if touches >= num_touches:
            confirmed_supports.append(idx)
    
    # Check resistances
    for idx in resistance_idx:
        resistance_price = highs[idx]
        touches = 0
        
        for i in range(len(highs)):
            # Skip the point itself
            if i == idx:
                continue
            
            # Count if price approaches within threshold
            if abs(highs[i] - resistance_price) / resistance_price < price_threshold:
                touches += 1
        
        if touches >= num_touches:
            confirmed_resistances.append(idx)
    
    return confirmed_supports, confirmed_resistances
