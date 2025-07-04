"""
Enhanced Data Fetcher for Stock Data Retrieval and Analysis
Combines multiple data sources with comprehensive stock screening capabilities
"""

import os
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    """Enhanced data fetcher that abstracts multiple financial data sources with comprehensive analysis."""
    
    # Popular ETFs and stocks for screening (reduced list to avoid rate limits)
    DEFAULT_SYMBOLS = [
        # ETFs (most popular)
        'SPY', 'QQQ', 'IWM', 'XLF', 'XLE', 'TLT', 'GLD',
        # Individual Stocks (blue chips)
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA'
    ]
    
    def __init__(self, source: str = "yfinance", api_key: str = None):
        """
        Initialize DataFetcher with configurable data source
        
        Args:
            source: Data source ('yfinance', 'eodhd', 'alpha_vantage', 'yahoo_finance')
            api_key: API key for paid services
        """
        self.source = source.lower()
        self.api_key = api_key or os.getenv("API_KEY")
        self.base_urls = {
            "eodhd": "https://eodhistoricaldata.com/api",
            "alpha_vantage": "https://www.alphavantage.co/query",
            "yahoo_finance": "https://yfapi.net/v6/finance",
            "yfinance": None  # Uses yfinance library directly
        }
        
        # Cache and rate limiting
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=15)
        self.request_delay = 0.5  # Delay between requests
        
        if self.source not in self.base_urls:
            raise ValueError(f"Unsupported data source: {self.source}. Supported: {list(self.base_urls.keys())}")
        
        logger.info(f"DataFetcher initialized with source: {self.source}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[cache_key]

    @lru_cache(maxsize=128)
    def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None, period: str = "3mo") -> Dict[str, Any]:
        """
        Fetches cached historical data with throttling handling.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date for historical data (YYYY-MM-DD)
            end_date: End date for historical data (YYYY-MM-DD)
            period: Period for data (used with yfinance: '1d', '5d', '1mo', '3mo', etc.)
        """
        cache_key = f"historical_{symbol}_{start_date}_{end_date}_{period}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached historical data for {symbol}")
            return self.cache[cache_key]
        
        try:
            if self.source == "yfinance":
                return self._fetch_yfinance_historical(symbol, period, start_date, end_date)
            else:
                return self._fetch_api_historical(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return {}

    def _fetch_yfinance_historical(self, symbol: str, period: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Fetch historical data using yfinance library"""
        ticker = yf.Ticker(symbol)
        
        if start_date and end_date:
            hist = ticker.history(start=start_date, end=end_date)
        else:
            hist = ticker.history(period=period)
        
        if hist.empty:
            raise Exception(f"No historical data found for {symbol}")
        
        # Convert to dictionary format
        data = {
            'symbol': symbol,
            'data': hist.to_dict('records'),
            'info': ticker.info
        }
        
        # Cache the result
        cache_key = f"historical_{symbol}_{start_date}_{end_date}_{period}"
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
        
        return data

    def _fetch_api_historical(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch historical data using external APIs with enhanced retry logic"""
        url = self._build_url(symbol, start_date, end_date)
        headers = self._build_headers()
        params = self._build_params(symbol, start_date, end_date)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Cache the result
                    cache_key = f"historical_{symbol}_{start_date}_{end_date}"
                    self.cache[cache_key] = data
                    self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
                    return data
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit hit for {symbol}. Retrying after {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                elif response.status_code in [502, 503, 504]:  # Server errors
                    wait_time = 1 + attempt
                    logger.warning(f"Server error {response.status_code} for {symbol}. Retrying after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error for {symbol}: {response.status_code} - {response.text}")
                    raise Exception(f"API error: {response.status_code} - {response.text}")
            except requests.RequestException as e:
                logger.error(f"Request error for {symbol}: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise
                wait_time = 2 ** attempt
                logger.info(f"Retrying after {wait_time}s...")
                time.sleep(wait_time)
        
        raise Exception(f"Max retries ({max_retries}) exceeded due to throttling or errors.")

    def fetch_stock_data(self, symbol: str, period: str = "3mo") -> Optional[Dict]:
        """
        Fetch comprehensive stock data for analysis with enhanced fallback
        
        Args:
            symbol: Stock symbol
            period: Data period
            
        Returns:
            Dictionary with comprehensive stock metrics or None if failed
        """
        cache_key = f"stock_data_{symbol}_{period}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached stock data for {symbol}")
            return self.cache[cache_key]
        
        # Try primary source first
        try:
            logger.info(f"Fetching comprehensive data for {symbol} using {self.source}")
            
            if self.source == "yfinance":
                return self._fetch_comprehensive_yfinance_data(symbol, period)
            else:
                # For other APIs, try to get data and fallback to yfinance for analysis
                try:
                    # Get basic data from API
                    historical_data = self.get_historical_data(symbol, period=period)
                    if historical_data:
                        # Use yfinance for comprehensive analysis
                        logger.info(f"Got basic data from {self.source}, using yfinance for analysis")
                        return self._fetch_comprehensive_yfinance_data(symbol, period)
                except Exception as api_error:
                    logger.warning(f"API {self.source} failed for {symbol}: {str(api_error)}")
                    # Fallback to yfinance
                    logger.info(f"Falling back to yfinance for {symbol}")
                    return self._fetch_comprehensive_yfinance_data(symbol, period)
                
        except Exception as e:
            logger.error(f"Error fetching comprehensive data for {symbol}: {str(e)}")
            
            # Try yfinance as ultimate fallback if not already using it
            if self.source != "yfinance":
                try:
                    logger.info(f"Ultimate fallback to yfinance for {symbol}")
                    return self._fetch_comprehensive_yfinance_data(symbol, period)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {symbol}: {str(fallback_error)}")
            
            return None

    def _fetch_comprehensive_yfinance_data(self, symbol: str, period: str = "3mo") -> Optional[Dict]:
        """Fetch comprehensive stock data using yfinance with all metrics"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get historical data for calculations
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None
            
            # Calculate metrics
            current_price = hist['Close'].iloc[-1]
            
            # Calculate ATR (Average True Range)
            atr_percentage = self._calculate_atr_percentage(hist)
            
            # Calculate 30-day price stability
            price_stability_30d = self._calculate_price_stability(hist, days=30)
            
            # Get options data for IV (if available)
            implied_volatility, iv_percentile = self._get_implied_volatility(ticker, symbol)
            
            # Get dividend and earnings info
            has_dividend = self._check_upcoming_dividend(ticker)
            has_earnings_soon = self._check_upcoming_earnings(ticker)
            
            # Mock open interest for now (would need options data API)
            open_interest = self._estimate_open_interest(info, current_price)
            
            stock_data = {
                'symbol': symbol,
                'current_price': round(float(current_price), 2),
                'atr_percentage': round(atr_percentage, 4),
                'implied_volatility': round(implied_volatility, 1),
                'iv_percentile': round(iv_percentile, 1),
                'open_interest': open_interest,
                'price_stability_30d': round(price_stability_30d, 4),
                'has_dividend': has_dividend,
                'has_earnings_soon': has_earnings_soon,
                'market_cap': info.get('marketCap', 0),
                'volume': int(hist['Volume'].iloc[-1]) if len(hist) > 0 else 0,
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'data_source': self.source
            }
            
            # Cache the result
            cache_key = f"stock_data_{symbol}_{period}"
            self.cache[cache_key] = stock_data
            self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error in comprehensive data fetch for {symbol}: {str(e)}")
            return None

    def screen_stocks(self, symbols: List[str], criteria: Dict) -> List[Dict]:
        """Screen multiple stocks against given criteria with rate limiting"""
        results = []
        
        logger.info(f"Screening {len(symbols)} stocks with criteria: {criteria}")
        
        for i, symbol in enumerate(symbols):
            # Add delay between requests to avoid rate limits
            if i > 0:
                time.sleep(self.request_delay)
            
            stock_data = self.fetch_stock_data(symbol)
            if stock_data:
                # Evaluate against criteria
                qualified, criteria_met_count = self._evaluate_stock(stock_data, criteria)
                
                stock_data.update({
                    'qualified': qualified,
                    'criteria_met_count': criteria_met_count
                })
                
                results.append(stock_data)
            else:
                logger.warning(f"Failed to fetch data for {symbol}, skipping...")
        
        logger.info(f"Screening complete. {len(results)} stocks processed successfully.")
        return results

    def _evaluate_stock(self, stock: Dict, criteria: Dict) -> tuple:
        """Evaluate a stock against screening criteria"""
        criteria_met = 0
        total_criteria = 8
        
        # Check price range
        if criteria['price_range'][0] <= stock['current_price'] <= criteria['price_range'][1]:
            criteria_met += 1
        
        # Check ATR threshold
        if stock['atr_percentage'] <= criteria['atr_threshold']:
            criteria_met += 1
        
        # Check IV range
        if criteria['iv_range'][0] <= stock['implied_volatility'] <= criteria['iv_range'][1]:
            criteria_met += 1
        
        # Check IV percentile
        if stock['iv_percentile'] <= criteria['iv_percentile_max']:
            criteria_met += 1
        
        # Check open interest
        if stock['open_interest'] >= criteria['open_interest_min']:
            criteria_met += 1
        
        # Check price stability
        if stock['price_stability_30d'] <= criteria['price_stability_30d']:
            criteria_met += 1
        
        # Check no dividends
        if not stock['has_dividend']:
            criteria_met += 1
        
        # Check no earnings soon
        if not stock['has_earnings_soon']:
            criteria_met += 1
        
        # Qualified if meets all criteria
        qualified = criteria_met == total_criteria
        
        return qualified, criteria_met

    # Analysis helper methods (preserved from original)
    def _calculate_atr_percentage(self, hist: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range as percentage of price"""
        try:
            if len(hist) < period + 1:
                return 0.0
            
            # Calculate True Range
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            current_price = hist['Close'].iloc[-1]
            return atr / current_price if current_price > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return 0.0

    def _calculate_price_stability(self, hist: pd.DataFrame, days: int = 30) -> float:
        """Calculate price stability over specified period"""
        try:
            if len(hist) < days:
                days = len(hist)
            
            recent_prices = hist['Close'].tail(days)
            if len(recent_prices) < 2:
                return 0.0
            
            returns = recent_prices.pct_change().dropna()
            return float(returns.std()) if len(returns) > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating price stability: {str(e)}")
            return 0.0

    def _get_implied_volatility(self, ticker, symbol: str) -> tuple:
        """Get implied volatility data (mock for now)"""
        try:
            # This would require options data API
            # For now, we'll estimate based on historical volatility
            hist = ticker.history(period="1y")
            if not hist.empty:
                returns = hist['Close'].pct_change().dropna()
                historical_vol = returns.std() * np.sqrt(252) * 100  # Annualized
                
                # Mock IV based on historical vol with some variation
                implied_vol = historical_vol * np.random.uniform(0.8, 1.2)
                iv_percentile = np.random.uniform(20, 80)  # Mock percentile
                
                return max(10, min(100, implied_vol)), max(0, min(100, iv_percentile))
            
        except Exception as e:
            logger.error(f"Error calculating IV for {symbol}: {str(e)}")
        
        # Default fallback
        return 25.0, 50.0

    def _check_upcoming_dividend(self, ticker) -> bool:
        """Check if dividend is expected in next 30 days"""
        try:
            dividends = ticker.dividends
            if dividends.empty:
                return False
            
            # Check last dividend date and estimate next one
            last_dividend_date = dividends.index[-1]
            days_since_last = (datetime.now() - last_dividend_date.to_pydatetime()).days
            
            # Assume quarterly dividends (90 days cycle)
            return days_since_last > 60  # Likely due soon
            
        except Exception:
            return False

    def _check_upcoming_earnings(self, ticker) -> bool:
        """Check if earnings announcement is expected soon"""
        try:
            # Mock earnings check - would need earnings calendar API
            # For now, randomly assign some stocks as having earnings soon
            import random
            return random.random() < 0.2  # 20% chance of earnings soon
            
        except Exception:
            return False

    def _estimate_open_interest(self, info: dict, price: float) -> int:
        """Estimate open interest based on market cap and price"""
        try:
            market_cap = info.get('marketCap', 0)
            if market_cap > 0:
                # Rough estimation: larger companies tend to have higher open interest
                if market_cap > 100_000_000_000:  # > $100B
                    return int(np.random.uniform(15000, 50000))
                elif market_cap > 10_000_000_000:  # > $10B
                    return int(np.random.uniform(8000, 25000))
                elif market_cap > 1_000_000_000:  # > $1B
                    return int(np.random.uniform(3000, 15000))
                else:
                    return int(np.random.uniform(500, 8000))
            
        except Exception:
            pass
        
        return int(np.random.uniform(1000, 10000))

    # API-specific methods for external data sources
    def _build_url(self, symbol: str, start_date: str, end_date: str) -> str:
        """Builds the API URL based on the data source."""
        base = self.base_urls[self.source]
        if self.source == "eodhd":
            return f"{base}/eod/{symbol}.US"
        elif self.source == "alpha_vantage":
            return base
        elif self.source == "yahoo_finance":
            return f"{base}/quote"
        return ""

    def _build_headers(self) -> Dict[str, str]:
        """Build headers for API requests"""
        if self.source == "yahoo_finance":
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _build_params(self, symbol: str, start_date: str, end_date: str) -> Dict[str, str]:
        """Builds API request parameters based on the data source."""
        if self.source == "eodhd":
            return {"api_token": self.api_key, "from": start_date, "to": end_date}
        elif self.source == "alpha_vantage":
            return {"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": self.api_key}
        elif self.source == "yahoo_finance":
            return {"symbols": symbol}
        return {}

    # Utility methods
    def get_default_symbols(self) -> List[str]:
        """Get list of default symbols for screening"""
        return self.DEFAULT_SYMBOLS.copy()

    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("Cache cleared")

    def set_data_source(self, source: str, api_key: str = None):
        """Change the data source dynamically"""
        if source.lower() not in self.base_urls:
            raise ValueError(f"Unsupported data source: {source}")
        
        self.source = source.lower()
        if api_key:
            self.api_key = api_key
        
        # Clear cache when switching sources
        self.clear_cache()
        logger.info(f"Data source changed to: {self.source}")

    def get_source_info(self) -> Dict[str, Any]:
        """Get information about current data source"""
        return {
            'source': self.source,
            'has_api_key': bool(self.api_key),
            'cache_size': len(self.cache),
            'supported_sources': list(self.base_urls.keys()),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60,
            'request_delay_seconds': self.request_delay
        }
    
    def test_data_source(self, test_symbol: str = "AAPL") -> Dict[str, Any]:
        """Test the current data source with a simple request"""
        try:
            start_time = time.time()
            
            if self.source == "yfinance":
                ticker = yf.Ticker(test_symbol)
                info = ticker.info
                success = bool(info.get('symbol') or info.get('shortName'))
            else:
                # Test API connection
                historical_data = self.get_historical_data(
                    test_symbol, 
                    start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d')
                )
                success = bool(historical_data)
            
            response_time = time.time() - start_time
            
            return {
                'source': self.source,
                'success': success,
                'response_time_seconds': round(response_time, 2),
                'test_symbol': test_symbol,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'source': self.source,
                'success': False,
                'error': str(e),
                'test_symbol': test_symbol,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics"""
        now = datetime.now()
        valid_entries = sum(1 for expiry in self.cache_expiry.values() if expiry > now)
        expired_entries = len(self.cache_expiry) - valid_entries
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_hit_ratio': f"{(valid_entries / max(1, len(self.cache)) * 100):.1f}%",
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60
        }


# Example usage and backward compatibility
if __name__ == "__main__":
    # Example with yfinance (default, free)
    fetcher = DataFetcher(source="yfinance")
    stock_data = fetcher.fetch_stock_data("AAPL")
    print("AAPL Data:", stock_data)
    
    # Example with external API (requires API key)
    # fetcher = DataFetcher(source="eodhd", api_key="your-api-key-here")
    # data = fetcher.get_historical_data("AAPL", "2023-01-01", "2023-12-31")
    # print("Historical Data:", data)
    
    # Example screening
    criteria = {
        'atr_threshold': 0.05,
        'iv_range': [20, 40],
        'price_range': [50, 150],
        'iv_percentile_max': 50,
        'open_interest_min': 1000,
        'price_stability_30d': 0.1,
        'exclude_dividends': True,
        'exclude_earnings': True
    }
    
    results = fetcher.screen_stocks(['AAPL', 'MSFT'], criteria)
    print("Screening Results:", results)
