"""
Agentic Calendar Spread Trading System - Flask Application
A web application for automated stock screening and calendar spread trading analysis.
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['DEBUG'] = True

# Sample data - in a real application, this would come from a database or external API
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
    "qualified_stocks": [
        {
            "symbol": "XLF",
            "current_price": 64.83,
            "atr_percentage": 0.017,
            "implied_volatility": 22.0,
            "iv_percentile": 30.0,
            "open_interest": 12000,
            "price_stability_30d": 0.063,
            "score": 56.7,
            "criteria_met": {
                "price_range": True,
                "atr_stable": True,
                "iv_range": True,
                "iv_percentile": True,
                "open_interest": True,
                "price_stable": True,
                "no_dividend": True,
                "no_earnings": True
            }
        }
    ],
    "all_stocks": [
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
            "qualified": True,
            "criteria_met_count": 8
        },
        {
            "symbol": "SPY",
            "current_price": 79.14,
            "atr_percentage": 0.014,
            "implied_volatility": 18.0,
            "iv_percentile": 25.0,
            "open_interest": 25000,
            "price_stability_30d": 0.071,
            "has_dividend": False,
            "has_earnings_soon": False,
            "qualified": False,
            "criteria_met_count": 7
        },
        {
            "symbol": "QQQ",
            "current_price": 69.02,
            "atr_percentage": 0.017,
            "implied_volatility": 25.0,
            "iv_percentile": 35.0,
            "open_interest": 15000,
            "price_stability_30d": 0.149,
            "has_dividend": False,
            "has_earnings_soon": False,
            "qualified": False,
            "criteria_met_count": 7
        },
        {
            "symbol": "IWM",
            "current_price": 97.92,
            "atr_percentage": 0.018,
            "implied_volatility": 28.0,
            "iv_percentile": 40.0,
            "open_interest": 8000,
            "price_stability_30d": 0.117,
            "has_dividend": False,
            "has_earnings_soon": False,
            "qualified": False,
            "criteria_met_count": 7
        },
        {
            "symbol": "TLT",
            "current_price": 116.98,
            "atr_percentage": 0.017,
            "implied_volatility": 31.0,
            "iv_percentile": 45.0,
            "open_interest": 18000,
            "price_stability_30d": 0.124,
            "has_dividend": False,
            "has_earnings_soon": False,
            "qualified": False,
            "criteria_met_count": 7
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
            "qualified": False,
            "criteria_met_count": 3
        },
        {
            "symbol": "TSLA",
            "current_price": 39.89,
            "atr_percentage": 0.025,
            "implied_volatility": 55.0,
            "iv_percentile": 85.0,
            "open_interest": 3000,
            "price_stability_30d": 0.240,
            "has_dividend": False,
            "has_earnings_soon": True,
            "qualified": False,
            "criteria_met_count": 3
        },
        {
            "symbol": "AMZN",
            "current_price": 128.49,
            "atr_percentage": 0.028,
            "implied_volatility": 38.0,
            "iv_percentile": 60.0,
            "open_interest": 7000,
            "price_stability_30d": 0.234,
            "has_dividend": False,
            "has_earnings_soon": True,
            "qualified": False,
            "criteria_met_count": 5
        }
    ],
    "calendar_spreads": [
        {
            "symbol": "XLF",
            "current_price": 64.83,
            "strike_price": 64,
            "strategy_type": "Put Calendar",
            "max_profit_zone_low": 62.72,
            "max_profit_zone_high": 65.28,
            "breakeven_low": 62.59,
            "breakeven_high": 65.41,
            "risk_reward_ratio": 2.50,
            "front_month_days": 30,
            "back_month_days": 60,
            "implied_volatility": 22.0
        },
        {
            "symbol": "XLF",
            "current_price": 64.83,
            "strike_price": 65,
            "strategy_type": "Call Calendar",
            "max_profit_zone_low": 63.70,
            "max_profit_zone_high": 66.30,
            "breakeven_low": 63.57,
            "breakeven_high": 66.43,
            "risk_reward_ratio": 2.50,
            "front_month_days": 30,
            "back_month_days": 60,
            "implied_volatility": 22.0
        },
        {
            "symbol": "XLF",
            "current_price": 64.83,
            "strike_price": 66,
            "strategy_type": "Call Calendar",
            "max_profit_zone_low": 64.68,
            "max_profit_zone_high": 67.32,
            "breakeven_low": 64.55,
            "breakeven_high": 67.45,
            "risk_reward_ratio": 2.50,
            "front_month_days": 30,
            "back_month_days": 60,
            "implied_volatility": 22.0
        }
    ],
    "system_stats": {
        "total_stocks_analyzed": 8,
        "qualified_stocks": 1,
        "success_rate": 12.5,
        "average_criteria_met": 6.25,
        "last_scan_time": "2025-07-04T11:47:00Z",
        "next_scan_time": "2025-07-04T12:17:00Z"
    }
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/data')
def get_application_data():
    """API endpoint to get all application data"""
    return jsonify(APPLICATION_DATA)

@app.route('/api/stocks')
def get_stocks():
    """API endpoint to get stock data"""
    filter_type = request.args.get('filter', 'all')
    
    # Use the all_stocks data from APPLICATION_DATA
    stocks = APPLICATION_DATA['all_stocks']
    
    if filter_type == 'qualified':
        stocks = [s for s in stocks if s['qualified']]
    elif filter_type == 'unqualified':
        stocks = [s for s in stocks if not s['qualified']]
    
    return jsonify(stocks)

@app.route('/api/calendar-spreads')
def get_calendar_spreads():
    """API endpoint to get calendar spread data"""
    return jsonify(APPLICATION_DATA['calendar_spreads'])

@app.route('/api/screening-criteria', methods=['GET', 'POST'])
def screening_criteria():
    """API endpoint to get or update screening criteria"""
    if request.method == 'POST':
        # Update criteria
        new_criteria = request.get_json()
        APPLICATION_DATA['screening_criteria'].update(new_criteria)
        return jsonify({"status": "success", "message": "Criteria updated"})
    else:
        # Get current criteria
        return jsonify(APPLICATION_DATA['screening_criteria'])

@app.route('/api/refresh-scan', methods=['POST'])
def refresh_scan():
    """API endpoint to trigger a new scan"""
    # In a real application, this would trigger the scanning process
    APPLICATION_DATA['system_stats']['last_scan_time'] = datetime.utcnow().isoformat() + 'Z'
    next_scan = datetime.utcnow() + timedelta(minutes=30)
    APPLICATION_DATA['system_stats']['next_scan_time'] = next_scan.isoformat() + 'Z'
    
    return jsonify({
        "status": "success", 
        "message": "Scan completed",
        "stats": APPLICATION_DATA['system_stats']
    })

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return '', 204  # Return empty response with "No Content" status

@app.route('/api/export/stocks')
def export_stocks():
    """API endpoint to export stock data as CSV"""
    # In a real application, this would generate and return a CSV file
    return jsonify({"status": "success", "message": "Export functionality would be implemented here"})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
