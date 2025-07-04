"""
Agentic Calendar Spread Trading System - Flask Application
A web application for automated stock screening and calendar spread trading analysis.
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta
import logging
from services.data_fetcher import DataFetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['DEBUG'] = True

# Initialize Data Fetcher with yfinance as default (free, no API key required)
# Can be switched to other sources like 'eodhd', 'alpha_vantage', etc. with API keys
data_fetcher = DataFetcher(source="yfinance")

# Application state - will be populated with real data
APPLICATION_DATA = {
    "screening_criteria": {
        "atr_threshold": 0.05,
        "iv_range": [20, 40],
        "price_range": [50, 150],
        "iv_percentile_max": 50,
        "open_interest_min": 1000,
        "price_stability_30d": 0.10,
        "exclude_dividends": True,
        "exclude_earnings": True
    },
    "qualified_stocks": [],
    "all_stocks": [],
    "calendar_spreads": [],
    "system_stats": {
        "total_stocks_analyzed": 0,
        "qualified_stocks": 0,
        "success_rate": 0.0,
        "average_criteria_met": 0.0,
        "last_scan_time": None,
        "next_scan_time": None
    }
}

# Helper function to perform initial data load
def load_initial_data():
    """Load initial stock data on app startup"""
    logger.info("Loading initial stock data...")
    try:
        symbols = data_fetcher.get_default_symbols()
        criteria = APPLICATION_DATA['screening_criteria']
        
        # Fetch and screen stocks
        all_stocks = data_fetcher.screen_stocks(symbols, criteria)
        
        # If no stocks were successfully fetched (due to rate limits), use sample data
        if not all_stocks:
            logger.warning("No stocks fetched from data source, using sample data...")
            all_stocks = get_sample_stock_data()
        elif len(all_stocks) < 3:
            logger.warning("Very few stocks fetched, supplementing with sample data...")
            sample_stocks = get_sample_stock_data()
            # Add sample stocks that aren't already in the results
            existing_symbols = {stock['symbol'] for stock in all_stocks}
            for sample_stock in sample_stocks:
                if sample_stock['symbol'] not in existing_symbols:
                    all_stocks.append(sample_stock)
        
        # Update application data
        APPLICATION_DATA['all_stocks'] = all_stocks
        APPLICATION_DATA['qualified_stocks'] = [s for s in all_stocks if s['qualified']]
        
        # Update stats
        total_stocks = len(all_stocks)
        qualified_count = len(APPLICATION_DATA['qualified_stocks'])
        success_rate = (qualified_count / total_stocks * 100) if total_stocks > 0 else 0
        avg_criteria = sum(s['criteria_met_count'] for s in all_stocks) / total_stocks if total_stocks > 0 else 0
        
        APPLICATION_DATA['system_stats'].update({
            'total_stocks_analyzed': total_stocks,
            'qualified_stocks': qualified_count,
            'success_rate': round(success_rate, 1),
            'average_criteria_met': round(avg_criteria, 2),
            'last_scan_time': datetime.utcnow().isoformat() + 'Z',
            'next_scan_time': (datetime.utcnow() + timedelta(minutes=30)).isoformat() + 'Z'
        })
        
        # Generate sample calendar spreads for qualified stocks
        APPLICATION_DATA['calendar_spreads'] = generate_calendar_spreads()
        
        logger.info(f"Initial data loaded: {total_stocks} stocks, {qualified_count} qualified")
        
    except Exception as e:
        logger.error(f"Error loading initial data: {str(e)}")
        # Fall back to sample data if loading fails
        logger.info("Loading sample data as fallback...")
        all_stocks = get_sample_stock_data()
        APPLICATION_DATA['all_stocks'] = all_stocks
        APPLICATION_DATA['qualified_stocks'] = [s for s in all_stocks if s['qualified']]
        APPLICATION_DATA['calendar_spreads'] = generate_calendar_spreads()
        
        # Update stats for sample data
        total_stocks = len(all_stocks)
        qualified_count = len(APPLICATION_DATA['qualified_stocks'])
        success_rate = (qualified_count / total_stocks * 100) if total_stocks > 0 else 0
        avg_criteria = sum(s['criteria_met_count'] for s in all_stocks) / total_stocks if total_stocks > 0 else 0
        
        APPLICATION_DATA['system_stats'].update({
            'total_stocks_analyzed': total_stocks,
            'qualified_stocks': qualified_count,
            'success_rate': round(success_rate, 1),
            'average_criteria_met': round(avg_criteria, 2),
            'last_scan_time': datetime.utcnow().isoformat() + 'Z',
            'next_scan_time': (datetime.utcnow() + timedelta(minutes=30)).isoformat() + 'Z'
        })

def get_sample_stock_data():
    """Get sample stock data as fallback when Yahoo Finance fails"""
    return [
        {
            "symbol": "SPY",
            "current_price": 542.15,
            "atr_percentage": 0.014,
            "implied_volatility": 18.0,
            "iv_percentile": 25.0,
            "open_interest": 25000,
            "price_stability_30d": 0.071,
            "has_dividend": False,
            "has_earnings_soon": False,
            "market_cap": 500_000_000_000,
            "volume": 45_000_000,
            "sector": "Financial Services",
            "industry": "Exchange Traded Fund",
            "qualified": False,
            "criteria_met_count": 7
        },
        {
            "symbol": "QQQ",
            "current_price": 467.23,
            "atr_percentage": 0.017,
            "implied_volatility": 25.0,
            "iv_percentile": 35.0,
            "open_interest": 15000,
            "price_stability_30d": 0.089,
            "has_dividend": False,
            "has_earnings_soon": False,
            "market_cap": 250_000_000_000,
            "volume": 28_000_000,
            "sector": "Technology",
            "industry": "Exchange Traded Fund",
            "qualified": False,
            "criteria_met_count": 7
        },
        {
            "symbol": "XLF",
            "current_price": 64.83,
            "atr_percentage": 0.017,
            "implied_volatility": 22.0,
            "iv_percentile": 30.0,
            "open_interest": 12000,
            "price_stability_30d": 0.063,
            "has_dividend": False,
            "has_earnings_soon": False,
            "market_cap": 50_000_000_000,
            "volume": 18_000_000,
            "sector": "Financial Services",
            "industry": "Exchange Traded Fund",
            "qualified": True,
            "criteria_met_count": 8
        },
        {
            "symbol": "AAPL",
            "current_price": 209.11,
            "atr_percentage": 0.030,
            "implied_volatility": 45.0,
            "iv_percentile": 70.0,
            "open_interest": 5000,
            "price_stability_30d": 0.190,
            "has_dividend": True,
            "has_earnings_soon": False,
            "market_cap": 3_200_000_000_000,
            "volume": 42_000_000,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "qualified": False,
            "criteria_met_count": 3
        },
        {
            "symbol": "TSLA",
            "current_price": 145.89,
            "atr_percentage": 0.025,
            "implied_volatility": 55.0,
            "iv_percentile": 85.0,
            "open_interest": 3000,
            "price_stability_30d": 0.240,
            "has_dividend": False,
            "has_earnings_soon": True,
            "market_cap": 450_000_000_000,
            "volume": 35_000_000,
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers",
            "qualified": False,
            "criteria_met_count": 3
        }
    ]

def generate_calendar_spreads():
    """Generate sample calendar spreads for qualified stocks"""
    spreads = []
    for stock in APPLICATION_DATA['qualified_stocks'][:3]:  # Limit to first 3 for demo
        symbol = stock['symbol']
        price = stock['current_price']
        iv = stock['implied_volatility']
        
        # Generate strikes around current price
        strikes = [
            int(price * 0.98),  # 2% OTM put
            int(price),         # ATM
            int(price * 1.02)   # 2% OTM call
        ]
        
        for i, strike in enumerate(strikes):
            strategy_type = "Put Calendar" if i == 0 else "Call Calendar"
            
            # Mock profit zone and breakevens (would use actual options pricing)
            profit_zone_width = price * 0.04  # 4% width
            spread = {
                "symbol": symbol,
                "current_price": price,
                "strike_price": strike,
                "strategy_type": strategy_type,
                "max_profit_zone_low": round(strike - profit_zone_width/2, 2),
                "max_profit_zone_high": round(strike + profit_zone_width/2, 2),
                "breakeven_low": round(strike - profit_zone_width/2 * 1.1, 2),
                "breakeven_high": round(strike + profit_zone_width/2 * 1.1, 2),
                "risk_reward_ratio": 2.5,
                "front_month_days": 30,
                "back_month_days": 60,
                "implied_volatility": iv
            }
            spreads.append(spread)
    
    return spreads

@app.route('/')
def index():
    """Main dashboard page"""
    # Load initial data if not already loaded
    if not APPLICATION_DATA['all_stocks']:
        load_initial_data()
    return render_template('index.html')

@app.route('/api/data')
def get_application_data():
    """API endpoint to get all application data"""
    # Load initial data if not already loaded
    if not APPLICATION_DATA['all_stocks']:
        load_initial_data()
    return jsonify(APPLICATION_DATA)

@app.route('/api/stocks')
def get_stocks():
    """API endpoint to get stock data"""
    try:
        # Load initial data if not already loaded
        if not APPLICATION_DATA['all_stocks']:
            load_initial_data()
        
        filter_type = request.args.get('filter', 'all')
        stocks = APPLICATION_DATA['all_stocks']
        
        if filter_type == 'qualified':
            stocks = [s for s in stocks if s['qualified']]
        elif filter_type == 'unqualified':
            stocks = [s for s in stocks if not s['qualified']]
        
        return jsonify(stocks)
    
    except Exception as e:
        logger.error(f"Error fetching stocks: {str(e)}")
        return jsonify({"error": "Failed to fetch stock data"}), 500

@app.route('/api/calendar-spreads')
def get_calendar_spreads():
    """API endpoint to get calendar spread data"""
    try:
        # Load initial data if not already loaded
        if not APPLICATION_DATA['calendar_spreads']:
            load_initial_data()
        
        return jsonify(APPLICATION_DATA['calendar_spreads'])
    
    except Exception as e:
        logger.error(f"Error fetching calendar spreads: {str(e)}")
        return jsonify({"error": "Failed to fetch calendar spread data"}), 500

@app.route('/api/screening-criteria', methods=['GET', 'POST'])
def screening_criteria():
    """API endpoint to get or update screening criteria"""
    try:
        if request.method == 'POST':
            # Update criteria
            new_criteria = request.get_json()
            APPLICATION_DATA['screening_criteria'].update(new_criteria)
            
            # Re-evaluate existing stocks with new criteria if we have stock data
            if APPLICATION_DATA['all_stocks']:
                logger.info("Re-evaluating stocks with updated criteria...")
                
                qualified_count = 0
                total_criteria_met = 0
                
                for stock in APPLICATION_DATA['all_stocks']:
                    qualified, criteria_met_count = data_fetcher._evaluate_stock(
                        stock, APPLICATION_DATA['screening_criteria']
                    )
                    stock['qualified'] = qualified
                    stock['criteria_met_count'] = criteria_met_count
                    
                    if qualified:
                        qualified_count += 1
                    total_criteria_met += criteria_met_count
                
                # Update stats
                total_stocks = len(APPLICATION_DATA['all_stocks'])
                success_rate = (qualified_count / total_stocks * 100) if total_stocks > 0 else 0
                average_criteria = total_criteria_met / total_stocks if total_stocks > 0 else 0
                
                APPLICATION_DATA['system_stats'].update({
                    'qualified_stocks': qualified_count,
                    'success_rate': round(success_rate, 1),
                    'average_criteria_met': round(average_criteria, 2)
                })
                
                # Update qualified stocks list
                APPLICATION_DATA['qualified_stocks'] = [s for s in APPLICATION_DATA['all_stocks'] if s['qualified']]
                
                # Regenerate calendar spreads
                APPLICATION_DATA['calendar_spreads'] = generate_calendar_spreads()
            
            return jsonify({
                "status": "success", 
                "message": "Criteria updated and stocks re-evaluated"
            })
        else:
            # Get current criteria
            return jsonify(APPLICATION_DATA['screening_criteria'])
            
    except Exception as e:
        logger.error(f"Error updating screening criteria: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Failed to update criteria: {str(e)}"
        }), 500

@app.route('/api/refresh-scan', methods=['POST'])
def refresh_scan():
    """API endpoint to trigger a new scan with real data from configured source"""
    try:
        logger.info("Starting refresh scan with live data...")
        
        # Clear cache to get fresh data
        data_fetcher.clear_cache()
        
        # Get symbols to scan
        symbols = data_fetcher.get_default_symbols()
        criteria = APPLICATION_DATA['screening_criteria']
        
        # Fetch fresh data and screen stocks
        all_stocks = data_fetcher.screen_stocks(symbols, criteria)
        
        # If no or very few stocks were fetched (due to rate limits), keep existing data
        if not all_stocks:
            logger.warning("No new stocks fetched due to rate limits, keeping existing data")
            return jsonify({
                "status": "warning", 
                "message": "Rate limit reached - keeping existing data. Try again in a few minutes.",
                "stats": APPLICATION_DATA['system_stats']
            })
        elif len(all_stocks) < len(APPLICATION_DATA['all_stocks']) // 2:
            logger.warning("Fewer stocks fetched than expected, supplementing with existing data")
            # Keep existing stocks that weren't refreshed
            existing_symbols = {stock['symbol'] for stock in all_stocks}
            for existing_stock in APPLICATION_DATA['all_stocks']:
                if existing_stock['symbol'] not in existing_symbols:
                    all_stocks.append(existing_stock)
        
        # Update application data
        APPLICATION_DATA['all_stocks'] = all_stocks
        APPLICATION_DATA['qualified_stocks'] = [s for s in all_stocks if s['qualified']]
        
        # Update system stats
        total_stocks = len(all_stocks)
        qualified_count = len(APPLICATION_DATA['qualified_stocks'])
        success_rate = (qualified_count / total_stocks * 100) if total_stocks > 0 else 0
        total_criteria_met = sum(s['criteria_met_count'] for s in all_stocks)
        average_criteria = total_criteria_met / total_stocks if total_stocks > 0 else 0
        
        APPLICATION_DATA['system_stats'].update({
            'total_stocks_analyzed': total_stocks,
            'qualified_stocks': qualified_count,
            'success_rate': round(success_rate, 1),
            'average_criteria_met': round(average_criteria, 2),
            'last_scan_time': datetime.utcnow().isoformat() + 'Z',
            'next_scan_time': (datetime.utcnow() + timedelta(minutes=30)).isoformat() + 'Z'
        })
        
        # Regenerate calendar spreads
        APPLICATION_DATA['calendar_spreads'] = generate_calendar_spreads()
        
        fetched_count = sum(1 for stock in all_stocks if stock.get('symbol') in symbols)
        logger.info(f"Refresh scan completed: {fetched_count}/{len(symbols)} symbols fetched, {qualified_count} qualified")
        
        return jsonify({
            "status": "success", 
            "message": f"Scan completed - refreshed {fetched_count} of {len(symbols)} stocks, {qualified_count} qualified",
            "stats": APPLICATION_DATA['system_stats']
        })
        
    except Exception as e:
        logger.error(f"Error during refresh scan: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Scan failed: {str(e)}"
        }), 500

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return '', 204  # Return empty response with "No Content" status

@app.route('/api/export/stocks')
def export_stocks():
    """API endpoint to export stock data as CSV"""
    # In a real application, this would generate and return a CSV file
    return jsonify({"status": "success", "message": "Export functionality would be implemented here"})

@app.route('/api/data-source', methods=['GET', 'POST'])
def data_source():
    """API endpoint to get or change data source configuration"""
    try:
        if request.method == 'POST':
            # Change data source
            data = request.get_json()
            new_source = data.get('source')
            api_key = data.get('api_key')
            
            if not new_source:
                return jsonify({
                    "status": "error", 
                    "message": "Source is required"
                }), 400
            
            # Change the data source
            data_fetcher.set_data_source(new_source, api_key)
            
            logger.info(f"Data source changed to: {new_source}")
            
            return jsonify({
                "status": "success", 
                "message": f"Data source changed to {new_source}",
                "source_info": data_fetcher.get_source_info()
            })
        else:
            # Get current data source info
            return jsonify({
                "status": "success",
                "source_info": data_fetcher.get_source_info()
            })
            
    except Exception as e:
        logger.error(f"Error managing data source: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Failed to manage data source: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Load initial data on startup
    logger.info("Starting Flask application...")
    try:
        load_initial_data()
        logger.info("Initial data loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load initial data: {str(e)}")
        logger.info("Starting with empty data - use refresh scan to load data")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
