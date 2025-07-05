"""
Enhanced Data Fetcher for Stock Data Retrieval and Analysis
Combines multiple data sources with comprehensive stock screening capabilities
"""

import os
import time
import json
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
    
    def __init__(self, source: str = None, api_key: str = None, config_path: str = None):
        """
        Initialize DataFetcher with configurable data source
        
        Args:
            source: Data source ('yfinance', 'eodhd', 'alpha_vantage', 'yahoo_finance') or None for config default
            api_key: API key for paid services or None to use environment variables
            config_path: Path to configuration file or None for default location
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set data source (use config default if not specified)
        if source is None:
            source = self.config['data_sources']['default']
        self.source = source.lower()
        
        # Validate source is supported
        if self.source not in self.config['data_sources']['sources']:
            supported = list(self.config['data_sources']['sources'].keys())
            raise ValueError(f"Unsupported data source: {self.source}. Supported: {supported}")
        
        # Get source configuration
        self.source_config = self.config['data_sources']['sources'][self.source]
        
        # Set API key (prioritize parameter, then environment variable, then None)
        if api_key:
            self.api_key = api_key
        elif self.source_config.get('api_key_env_var'):
            self.api_key = os.getenv(self.source_config['api_key_env_var'])
        else:
            self.api_key = os.getenv("API_KEY")  # Fallback to generic API_KEY
        
        # Build base URLs from config
        self.base_urls = {
            source_name: source_info.get('base_url')
            for source_name, source_info in self.config['data_sources']['sources'].items()
        }
        
        # Initialize cache and rate limiting from config
        cache_config = self.config['cache']
        rate_config = self.config['rate_limiting']
        
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=cache_config['duration_minutes'])
        self.request_delay = rate_config['default_delay_seconds']
        self.max_retries = rate_config['max_retries']
        self.timeout = rate_config['timeout_seconds']
        
        # Get default symbols from config
        self.DEFAULT_SYMBOLS = self.config['screening']['default_symbols']
        
        logger.info(f"DataFetcher initialized with source: {self.source} (from config)")
        if self.source_config.get('requires_api_key') and not self.api_key:
            logger.warning(f"API key required for {self.source} but not provided. Set {self.source_config.get('api_key_env_var', 'API_KEY')} environment variable.")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if config_path is None:
            # Default config path relative to this file
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, 'config.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from: {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            # Return default configuration
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config file is not available"""
        logger.warning("Using fallback default configuration")
        return {
            "data_sources": {
                "default": "alpha_vantage",
                "fallback": "yfinance",
                "sources": {
                    "alpha_vantage": {
                        "name": "Alpha Vantage",
                        "base_url": "https://www.alphavantage.co/query",
                        "requires_api_key": True,
                        "api_key_env_var": "ALPHA_VANTAGE_API_KEY"
                    },
                    "yfinance": {
                        "name": "Yahoo Finance (yfinance)",
                        "base_url": None,
                        "requires_api_key": False,
                        "api_key_env_var": None
                    },
                    "eodhd": {
                        "name": "EOD Historical Data",
                        "base_url": "https://eodhistoricaldata.com/api",
                        "requires_api_key": True,
                        "api_key_env_var": "EODHD_API_KEY"
                    },
                    "yahoo_finance": {
                        "name": "Yahoo Finance API",
                        "base_url": "https://yfapi.net/v6/finance",
                        "requires_api_key": True,
                        "api_key_env_var": "YAHOO_FINANCE_API_KEY"
                    }
                }
            },
            "cache": {
                "duration_minutes": 15,
                "max_size": 128
            },
            "rate_limiting": {
                "default_delay_seconds": 0.5,
                "max_retries": 3,
                "timeout_seconds": 10
            },
            "screening": {
                "default_symbols": [
                    'SPY', 'QQQ', 'IWM', 'XLF', 'XLE', 'TLT', 'GLD',
                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA'
                ]
            }
        }

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
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    # Cache the result
                    cache_key = f"historical_{symbol}_{start_date}_{end_date}"
                    self.cache[cache_key] = data
                    self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
                    return data
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit hit for {symbol}. Retrying after {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
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
                if attempt == self.max_retries - 1:  # Last attempt
                    raise
                wait_time = 2 ** attempt
                logger.info(f"Retrying after {wait_time}s...")
                time.sleep(wait_time)
        
        raise Exception(f"Max retries ({self.max_retries}) exceeded due to throttling or errors.")

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
            elif self.source == "alpha_vantage":
                return self._fetch_comprehensive_alpha_vantage_data(symbol, period)
            else:
                # For other APIs (EODHD, Yahoo Finance API), try to get comprehensive data
                # If not available, fallback to yfinance for analysis
                try:
                    comprehensive_data = self._fetch_comprehensive_external_api_data(symbol, period)
                    if comprehensive_data:
                        return comprehensive_data
                    else:
                        # Use yfinance for comprehensive analysis as fallback
                        logger.info(f"External API {self.source} doesn't support comprehensive analysis, using yfinance fallback")
                        return self._fetch_comprehensive_yfinance_data(symbol, period)
                except Exception as api_error:
                    logger.warning(f"API {self.source} failed for {symbol}: {str(api_error)}")
                    # Fallback to configured fallback source
                    fallback_source = self.config['data_sources']['fallback']
                    logger.info(f"Falling back to {fallback_source} for {symbol}")
                    return self._fetch_comprehensive_yfinance_data(symbol, period)
                
        except Exception as e:
            logger.error(f"Error fetching comprehensive data for {symbol}: {str(e)}")
            
            # Try configured fallback source if not already using it
            fallback_source = self.config['data_sources']['fallback']
            if self.source != fallback_source:
                try:
                    logger.info(f"Ultimate fallback to {fallback_source} for {symbol}")
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

    def _fetch_comprehensive_alpha_vantage_data(self, symbol: str, period: str = "3mo") -> Optional[Dict]:
        """Fetch comprehensive stock data using Alpha Vantage API with all metrics"""
        try:
            if not self.api_key:
                logger.error(f"Alpha Vantage API key required but not provided for {symbol}")
                # Fallback to yfinance
                logger.info(f"Falling back to yfinance for {symbol} due to missing API key")
                return self._fetch_comprehensive_yfinance_data(symbol, period)
            
            # Alpha Vantage comprehensive data collection
            stock_data = {
                'symbol': symbol,
                'data_source': self.source,
                # Initialize default values to prevent KeyError
                'market_cap': 0,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'has_dividend': False,
                'has_earnings_soon': False,
                'open_interest': 1000,
                'atr_percentage': 0.0,
                'price_stability_30d': 0.0,
                'implied_volatility': 25.0,
                'iv_percentile': 50.0
            }
            
            # 1. Get company overview (fundamentals)
            overview_data = self._get_alpha_vantage_overview(symbol)
            if overview_data:
                # Safe float conversion with None handling
                dividend_yield = overview_data.get('DividendYield', 0)
                safe_dividend_yield = 0.0
                try:
                    if dividend_yield and dividend_yield != 'None':
                        safe_dividend_yield = float(dividend_yield)
                except (ValueError, TypeError):
                    safe_dividend_yield = 0.0
                
                stock_data.update({
                    'market_cap': overview_data.get('MarketCapitalization', 0),
                    'sector': overview_data.get('Sector', 'Unknown'),
                    'industry': overview_data.get('Industry', 'Unknown'),
                    'has_dividend': safe_dividend_yield > 0
                })
            
            # 2. Get current quote data
            quote_data = self._get_alpha_vantage_quote(symbol)
            if quote_data:
                # Safe float conversion with None handling
                price_str = quote_data.get('05. price', '0')
                volume_str = quote_data.get('06. volume', '0')
                
                try:
                    current_price = float(price_str) if price_str and price_str != 'None' else 0.0
                except (ValueError, TypeError):
                    current_price = 0.0
                
                try:
                    volume = int(float(volume_str)) if volume_str and volume_str != 'None' else 0
                except (ValueError, TypeError):
                    volume = 0
                
                stock_data.update({
                    'current_price': round(current_price, 2),
                    'volume': volume
                })
            else:
                logger.warning(f"No quote data from Alpha Vantage for {symbol}")
                return None
            
            # 3. Get historical data for technical analysis
            historical_data = self._get_alpha_vantage_daily(symbol)
            if historical_data and 'Time Series (Daily)' in historical_data:
                hist_df = self._convert_alpha_vantage_to_dataframe(historical_data['Time Series (Daily)'])
                
                if not hist_df.empty:
                    # Calculate technical indicators
                    atr_percentage = self._calculate_atr_percentage(hist_df)
                    price_stability_30d = self._calculate_price_stability(hist_df, days=30)
                    
                    stock_data.update({
                        'atr_percentage': round(atr_percentage, 4),
                        'price_stability_30d': round(price_stability_30d, 4)
                    })
                else:
                    # Set default values if historical data processing fails
                    stock_data.update({
                        'atr_percentage': 0.0,
                        'price_stability_30d': 0.0
                    })
            else:
                logger.warning(f"No historical data from Alpha Vantage for {symbol}")
                stock_data.update({
                    'atr_percentage': 0.0,
                    'price_stability_30d': 0.0
                })
            
            # 4. Estimate implied volatility (Alpha Vantage doesn't provide options data in free tier)
            # We'll calculate based on historical volatility
            implied_volatility, iv_percentile = self._calculate_iv_from_historical(hist_df if 'hist_df' in locals() else None)
            stock_data.update({
                'implied_volatility': round(implied_volatility, 1),
                'iv_percentile': round(iv_percentile, 1)
            })
            
            # 5. Estimate other metrics not directly available from Alpha Vantage
            open_interest = self._estimate_open_interest_alpha_vantage(overview_data, stock_data.get('current_price', 0))
            has_earnings_soon = self._check_upcoming_earnings_alpha_vantage(overview_data)
            
            stock_data.update({
                'open_interest': open_interest,
                'has_earnings_soon': has_earnings_soon
            })
            
            # Cache the result
            cache_key = f"stock_data_{symbol}_{period}"
            self.cache[cache_key] = stock_data
            self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
            
            logger.info(f"Successfully fetched comprehensive Alpha Vantage data for {symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error in Alpha Vantage comprehensive data fetch for {symbol}: {str(e)}")
            # Fallback to yfinance
            logger.info(f"Falling back to yfinance for {symbol} due to Alpha Vantage error")
            return self._fetch_comprehensive_yfinance_data(symbol, period)
    
    def _get_alpha_vantage_overview(self, symbol: str) -> Optional[Dict]:
        """Get company overview from Alpha Vantage with enhanced debugging"""
        try:
            if not self.api_key:
                logger.error(f"❌ Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY environment variable.")
                return None
                
            url = self.base_urls['alpha_vantage']
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            logger.info(f"🔍 Requesting Alpha Vantage overview for {symbol}")
            logger.debug(f"URL: {url}")
            logger.debug(f"Params: {dict(params, apikey='***')}")  # Hide API key in logs
            
            response = requests.get(url, params=params, timeout=self.timeout)
            logger.info(f"📡 Alpha Vantage response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📄 Alpha Vantage response keys: {list(data.keys())}")
                
                # Check for common error responses
                if 'Error Message' in data:
                    logger.error(f"❌ Alpha Vantage API Error: {data['Error Message']}")
                    return None
                elif 'Note' in data:
                    logger.warning(f"⚠️ Alpha Vantage API Note: {data['Note']}")
                    return None
                elif 'Information' in data:
                    logger.warning(f"ℹ️ Alpha Vantage API Info: {data['Information']}")
                    return None
                elif 'Symbol' in data:  # Valid response
                    logger.info(f"✅ Successfully fetched overview for {symbol}")
                    return data
                else:
                    logger.warning(f"🤔 Alpha Vantage overview returned unexpected format for {symbol}")
                    logger.debug(f"Response sample: {str(data)[:200]}...")
                    return None
            else:
                logger.error(f"❌ Alpha Vantage overview API HTTP error for {symbol}: {response.status_code}")
                logger.debug(f"Response text: {response.text[:200]}...")
                return None
                
        except Exception as e:
            logger.error(f"💥 Exception in Alpha Vantage overview for {symbol}: {str(e)}")
            return None
    
    def _get_alpha_vantage_quote(self, symbol: str) -> Optional[Dict]:
        """Get current quote from Alpha Vantage with enhanced debugging"""
        try:
            if not self.api_key:
                logger.error(f"❌ Alpha Vantage API key not found for quote request")
                return None
                
            url = self.base_urls['alpha_vantage']
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            logger.info(f"🔍 Requesting Alpha Vantage quote for {symbol}")
            logger.debug(f"URL: {url}")
            logger.debug(f"Params: {dict(params, apikey='***')}")
            
            response = requests.get(url, params=params, timeout=self.timeout)
            logger.info(f"📡 Alpha Vantage quote response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📄 Alpha Vantage quote response keys: {list(data.keys())}")
                
                # Check for common error responses
                if 'Error Message' in data:
                    logger.error(f"❌ Alpha Vantage Quote API Error: {data['Error Message']}")
                    return None
                elif 'Note' in data:
                    logger.warning(f"⚠️ Alpha Vantage Quote API Note: {data['Note']}")
                    return None
                elif 'Information' in data:
                    logger.warning(f"ℹ️ Alpha Vantage Quote API Info: {data['Information']}")
                    return None
                elif 'Global Quote' in data:
                    quote_data = data['Global Quote']
                    if quote_data:  # Check if quote data is not empty
                        logger.info(f"✅ Successfully fetched quote for {symbol}")
                        return quote_data
                    else:
                        logger.warning(f"🤔 Alpha Vantage quote returned empty Global Quote for {symbol}")
                        return None
                else:
                    logger.warning(f"🤔 Alpha Vantage quote returned unexpected format for {symbol}")
                    logger.debug(f"Response sample: {str(data)[:200]}...")
                    return None
            else:
                logger.error(f"❌ Alpha Vantage quote API HTTP error for {symbol}: {response.status_code}")
                logger.debug(f"Response text: {response.text[:200]}...")
                return None
                
        except Exception as e:
            logger.error(f"💥 Exception in Alpha Vantage quote for {symbol}: {str(e)}")
            return None
    
    def _get_alpha_vantage_daily(self, symbol: str) -> Optional[Dict]:
        """Get daily time series from Alpha Vantage with enhanced debugging"""
        try:
            if not self.api_key:
                logger.error(f"❌ Alpha Vantage API key not found for daily data request")
                return None
                
            url = self.base_urls['alpha_vantage']
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.api_key,
                'outputsize': 'compact'  # Get last 100 data points
            }
            
            logger.info(f"🔍 Requesting Alpha Vantage daily data for {symbol}")
            logger.debug(f"URL: {url}")
            logger.debug(f"Params: {dict(params, apikey='***')}")
            
            response = requests.get(url, params=params, timeout=self.timeout)
            logger.info(f"📡 Alpha Vantage daily data response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📄 Alpha Vantage daily response keys: {list(data.keys())}")
                
                # Check for common error responses
                if 'Error Message' in data:
                    logger.error(f"❌ Alpha Vantage Daily API Error: {data['Error Message']}")
                    return None
                elif 'Note' in data:
                    logger.warning(f"⚠️ Alpha Vantage Daily API Note: {data['Note']}")
                    return None
                elif 'Information' in data:
                    logger.warning(f"ℹ️ Alpha Vantage Daily API Info: {data['Information']}")
                    return None
                elif 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']
                    if time_series:  # Check if time series data is not empty
                        logger.info(f"✅ Successfully fetched daily data for {symbol} ({len(time_series)} data points)")
                        return data
                    else:
                        logger.warning(f"🤔 Alpha Vantage daily returned empty time series for {symbol}")
                        return None
                else:
                    logger.warning(f"🤔 Alpha Vantage daily returned unexpected format for {symbol}")
                    logger.debug(f"Response sample: {str(data)[:200]}...")
                    return None
            else:
                logger.error(f"❌ Alpha Vantage daily API HTTP error for {symbol}: {response.status_code}")
                logger.debug(f"Response text: {response.text[:200]}...")
                return None
                
        except Exception as e:
            logger.error(f"💥 Exception in Alpha Vantage daily data for {symbol}: {str(e)}")
            return None
    
    def _convert_alpha_vantage_to_dataframe(self, time_series_data: Dict) -> pd.DataFrame:
        """Convert Alpha Vantage time series data to pandas DataFrame"""
        try:
            # Convert to DataFrame format similar to yfinance
            df_data = []
            for date_str, values in time_series_data.items():
                try:
                    # Safe float conversion with None handling
                    open_val = values.get('1. open', '0')
                    high_val = values.get('2. high', '0')
                    low_val = values.get('3. low', '0')
                    close_val = values.get('4. close', '0')
                    volume_val = values.get('5. volume', '0')
                    
                    open_price = float(open_val) if open_val and open_val != 'None' else 0.0
                    high_price = float(high_val) if high_val and high_val != 'None' else 0.0
                    low_price = float(low_val) if low_val and low_val != 'None' else 0.0
                    close_price = float(close_val) if close_val and close_val != 'None' else 0.0
                    volume = int(float(volume_val)) if volume_val and volume_val != 'None' else 0
                    
                    df_data.append({
                        'Date': pd.to_datetime(date_str),
                        'Open': open_price,
                        'High': high_price,
                        'Low': low_price,
                        'Close': close_price,
                        'Volume': volume
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid data point for {date_str}: {str(e)}")
                    continue
            
            df = pd.DataFrame(df_data)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)  # Ensure chronological order
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting Alpha Vantage data to DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_iv_from_historical(self, hist_df: Optional[pd.DataFrame]) -> tuple:
        """Calculate implied volatility estimate from historical data"""
        try:
            if hist_df is None or hist_df.empty:
                return 25.0, 50.0  # Default values
            
            # Calculate historical volatility
            returns = hist_df['Close'].pct_change().dropna()
            if len(returns) > 0:
                historical_vol = returns.std() * np.sqrt(252) * 100  # Annualized
                
                # Estimate IV as historical vol with some variation
                implied_vol = historical_vol * np.random.uniform(0.9, 1.1)
                iv_percentile = np.random.uniform(25, 75)  # Mock percentile
                
                return max(10, min(100, implied_vol)), max(0, min(100, iv_percentile))
            
        except Exception as e:
            logger.error(f"Error calculating IV from historical data: {str(e)}")
        
        return 25.0, 50.0  # Default fallback
    
    def _estimate_open_interest_alpha_vantage(self, overview_data: Optional[Dict], price: float) -> int:
        """Estimate open interest based on Alpha Vantage company data"""
        try:
            if overview_data:
                market_cap = overview_data.get('MarketCapitalization')
                if market_cap and market_cap != 'None':
                    market_cap_val = float(market_cap)
                    return self._estimate_open_interest({'marketCap': market_cap_val}, price)
            
            # Fallback estimation
            return int(np.random.uniform(1000, 10000))
            
        except Exception:
            return int(np.random.uniform(1000, 10000))
    
    def _check_upcoming_earnings_alpha_vantage(self, overview_data: Optional[Dict]) -> bool:
        """Check for upcoming earnings using Alpha Vantage data"""
        try:
            if overview_data:
                # Alpha Vantage doesn't provide earnings calendar in free tier
                # Use a simple heuristic based on fiscal year end
                fiscal_year_end = overview_data.get('FiscalYearEnd')
                if fiscal_year_end:
                    # Mock earnings prediction based on fiscal year
                    current_month = datetime.now().month
                    fiscal_month = datetime.strptime(fiscal_year_end, '%B').month
                    
                    # Assume earnings in fiscal year end month and 3 months after
                    earnings_months = [fiscal_month, (fiscal_month + 3) % 12 or 12, 
                                     (fiscal_month + 6) % 12 or 12, (fiscal_month + 9) % 12 or 12]
                    
                    return current_month in earnings_months
            
            # Default random assignment
            return np.random.random() < 0.2  # 20% chance
            
        except Exception:
            return np.random.random() < 0.2  # 20% chance
    
    def _fetch_comprehensive_external_api_data(self, symbol: str, period: str = "3mo") -> Optional[Dict]:
        """Fetch comprehensive data from other external APIs (EODHD, Yahoo Finance API)"""
        # This is a placeholder for other API implementations
        # For now, return None to trigger fallback to yfinance
        logger.info(f"Comprehensive data not yet implemented for {self.source}, using fallback")
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
    
    def get_default_criteria(self) -> Dict[str, Any]:
        """Get default screening criteria from configuration"""
        return self.config['screening'].get('default_criteria', {
            'atr_threshold': 0.05,
            'iv_range': [20, 40],
            'price_range': [50, 150],
            'iv_percentile_max': 50,
            'open_interest_min': 1000,
            'price_stability_30d': 0.10,
            'exclude_dividends': True,
            'exclude_earnings': True,
            'custom_symbols': []
        }).copy()

    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("Cache cleared")

    def set_data_source(self, source: str, api_key: str = None):
        """Change the data source dynamically"""
        if source.lower() not in self.config['data_sources']['sources']:
            supported = list(self.config['data_sources']['sources'].keys())
            raise ValueError(f"Unsupported data source: {source}. Supported: {supported}")
        
        self.source = source.lower()
        self.source_config = self.config['data_sources']['sources'][self.source]
        
        # Update API key if provided
        if api_key:
            self.api_key = api_key
        elif self.source_config.get('api_key_env_var'):
            self.api_key = os.getenv(self.source_config['api_key_env_var'])
        
        # Clear cache when switching sources
        self.clear_cache()
        logger.info(f"Data source changed to: {self.source}")
        
        # Warn if API key is required but not available
        if self.source_config.get('requires_api_key') and not self.api_key:
            logger.warning(f"API key required for {self.source} but not provided. Set {self.source_config.get('api_key_env_var', 'API_KEY')} environment variable.")

    def get_source_info(self) -> Dict[str, Any]:
        """Get information about current data source"""
        return {
            'source': self.source,
            'source_name': self.source_config.get('name', self.source),
            'has_api_key': bool(self.api_key),
            'requires_api_key': self.source_config.get('requires_api_key', False),
            'api_key_env_var': self.source_config.get('api_key_env_var'),
            'cache_size': len(self.cache),
            'supported_sources': list(self.config['data_sources']['sources'].keys()),
            'default_source': self.config['data_sources']['default'],
            'fallback_source': self.config['data_sources']['fallback'],
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60,
            'request_delay_seconds': self.request_delay,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout,
            'rate_limits': {
                'per_minute': self.source_config.get('rate_limit_per_minute'),
                'per_day': self.source_config.get('rate_limit_per_day')
            }
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
    
    def set_custom_symbols(self, symbols: List[str]):
        """Set custom symbols for screening"""
        if symbols and isinstance(symbols, list):
            self.DEFAULT_SYMBOLS = [s.upper().strip() for s in symbols if s.strip()]
            logger.info(f"Custom symbols set: {self.DEFAULT_SYMBOLS}")
        else:
            logger.warning("Invalid symbols provided, keeping default symbols")
    
    def get_current_symbols(self) -> List[str]:
        """Get current symbols being used for screening"""
        return self.DEFAULT_SYMBOLS.copy()
    
    def validate_symbols(self, symbols: List[str]) -> List[str]:
        """Validate and clean symbol list"""
        valid_symbols = []
        for symbol in symbols:
            symbol = symbol.upper().strip()
            if symbol and len(symbol) <= 10 and symbol.isalpha():  # Basic validation
                valid_symbols.append(symbol)
            else:
                logger.warning(f"Invalid symbol format: {symbol}")
        return valid_symbols


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
