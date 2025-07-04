"""
Yahoo Finance Service for Stock Data Retrieval and Analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooFinanceService:
    """Service for fetching and analyzing stock data from Yahoo Finance"""
    
    # Popular ETFs and stocks for screening (reduced list to avoid rate limits)
    DEFAULT_SYMBOLS = [
        # ETFs (most popular)
        'SPY', 'QQQ', 'IWM', 'XLF', 'XLE', 'TLT', 'GLD',
        # Individual Stocks (blue chips)
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA'
    ]
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
        self.request_delay = 0.5  # Delay between requests to avoid rate limits
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[symbol]
    
    def fetch_stock_data(self, symbol: str, period: str = "3mo") -> Optional[Dict]:
        """Fetch comprehensive stock data from Yahoo Finance"""
        
        # Check cache first
        if self._is_cache_valid(symbol):
            logger.info(f"Using cached data for {symbol}")
            return self.cache[symbol]
        
        try:
            logger.info(f"Fetching data for {symbol}")
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
                'industry': info.get('industry', 'Unknown')
            }
            
            # Cache the result
            self.cache[symbol] = stock_data
            self.cache_expiry[symbol] = datetime.now() + self.cache_duration
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
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
    
    def screen_stocks(self, symbols: List[str], criteria: Dict) -> List[Dict]:
        """Screen multiple stocks against given criteria"""
        results = []
        
        logger.info(f"Screening {len(symbols)} stocks with criteria: {criteria}")
        
        for i, symbol in enumerate(symbols):
            # Add delay between requests to avoid rate limits
            if i > 0:
                import time
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
    
    def get_default_symbols(self) -> List[str]:
        """Get list of default symbols for screening"""
        return self.DEFAULT_SYMBOLS.copy()
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("Cache cleared")
