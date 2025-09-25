import yfinance as yf
import pandas as pd

def get_financial_data(tickers, period="1y"):
    """
    Fetches historical market data for a list of tickers.
    
    Args:
        tickers (list): A list of stock/crypto tickers.
        period (str): The period for which to fetch data (e.g., "1d", "5d", "1mo", "1y", "5y", "max").

    Returns:
        pandas.DataFrame: A DataFrame with the historical data, or None if an error occurs.
    """
    try:
        data = yf.download(tickers, period=period, group_by='ticker')
        return data
    except Exception as e:
        print(f"An error occurred while fetching financial data: {e}")
        return None

def get_ticker_info(ticker):
    """
    Fetches detailed information for a single ticker.

    Args:
        ticker (str): The stock/crypto ticker.

    Returns:
        dict: A dictionary containing information about the ticker, or None if invalid.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Check if the ticker is valid by looking for a key that most valid tickers have.
        if 'symbol' not in info:
            return None
        return info
    except Exception as e:
        print(f"Could not fetch info for ticker {ticker}: {e}")
        return None

def calculate_expected_return(data):
    """
    Calculates the expected annual return based on historical data.

    Args:
        data (pandas.DataFrame): DataFrame with historical price data.

    Returns:
        float: The annualized expected return.
    """
    if data is None or data.empty:
        return 0.0
        
    # Using 'Adj Close' for stocks and 'Close' for crypto if available
    close_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
    if close_col not in data.columns:
        return 0.0

    daily_returns = data[close_col].pct_change().dropna()
    avg_daily_return = daily_returns.mean()
    # Assuming 252 trading days in a year
    annualized_return = avg_daily_return * 252
    return annualized_return * 100 # Return as percentage
