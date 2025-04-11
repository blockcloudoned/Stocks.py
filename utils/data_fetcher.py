import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_stock_data(symbol: str, start_date=None, end_date=None, period: str = None) -> pd.DataFrame:
    """
    Fetch stock or cryptocurrency data from Yahoo Finance.
    
    Args:
        symbol: The ticker symbol (e.g., 'AAPL', 'BTC-USD')
        start_date: Start date for data retrieval (datetime or string)
        end_date: End date for data retrieval (datetime or string)
        period: Alternative to start/end dates (e.g., '1y', '6mo', '1d')
            Only used if start_date and end_date are None
    
    Returns:
        DataFrame with the stock data
    """
    try:
        # If period is provided and dates are not, use period
        if period and not (start_date or end_date):
            data = yf.download(symbol, period=period, progress=False)
        else:
            # Use dates if provided
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            raise ValueError(f"No data found for symbol: {symbol}")
        
        # Some cleaning and preprocessing
        data = data.dropna()
        
        # If the data has less than 20 points, try to get more by extending the date range
        if len(data) < 20 and not period:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            
            # Try to get 1 year of data
            new_start_date = start_date - timedelta(days=365)
            data = yf.download(symbol, start=new_start_date, end=end_date, progress=False)
            
            if data.empty:
                raise ValueError(f"No data found for symbol: {symbol}")
        
        return data
    
    except Exception as e:
        # Re-raise with more context
        raise Exception(f"Error fetching data for {symbol}: {str(e)}")

def get_symbol_info(symbol: str) -> dict:
    """
    Get basic information about a stock or cryptocurrency.
    
    Args:
        symbol: The ticker symbol (e.g., 'AAPL', 'BTC-USD')
    
    Returns:
        Dictionary with symbol information
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Select the most relevant fields
        relevant_info = {
            'symbol': symbol,
            'name': info.get('shortName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            'average_volume': info.get('averageVolume', 'N/A'),
            'beta': info.get('beta', 'N/A'),
            'description': info.get('longBusinessSummary', 'N/A'),
        }
        
        return relevant_info
    
    except Exception as e:
        # Return minimal info if there's an error
        return {
            'symbol': symbol,
            'name': symbol,
            'error': str(e)
        }

def search_symbols(query: str, limit: int = 10) -> list:
    """
    Search for symbols matching the query.
    This is a simple implementation as yfinance doesn't have a direct search API.
    
    Args:
        query: Search term
        limit: Maximum number of results to return
    
    Returns:
        List of matching symbols with basic info
    """
    # This is a very basic implementation
    # For a production app, you might want to use a more comprehensive API
    
    # Common stock tickers that might match the query
    common_stocks = {
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'amazon': 'AMZN',
        'google': 'GOOGL',
        'facebook': 'META',
        'tesla': 'TSLA',
        'netflix': 'NFLX',
        'nvidia': 'NVDA',
        'bitcoin': 'BTC-USD',
        'ethereum': 'ETH-USD',
        'dow': 'DJI',
        'sp500': '^GSPC',
        'nasdaq': '^IXIC',
        'gold': 'GC=F',
        'silver': 'SI=F',
        'oil': 'CL=F',
    }
    
    results = []
    
    # First check if query directly matches a symbol
    try:
        info = get_symbol_info(query.upper())
        if 'error' not in info:
            results.append(info)
    except:
        pass
    
    # Then check common names
    query_lower = query.lower()
    for name, symbol in common_stocks.items():
        if query_lower in name:
            try:
                info = get_symbol_info(symbol)
                if 'error' not in info and info not in results:
                    results.append(info)
                    if len(results) >= limit:
                        break
            except:
                continue
    
    return results[:limit]
