# Agentic Calendar Spread Trading System

[![CI/CD Pipeline](https://github.com/yourusername/agentic-calendar-trading/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/agentic-calendar-trading/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A Flask-based web application for automated stock screening and calendar spread trading analysis.

## Features

- **Real-time Stock Screening**: Automated analysis of stocks based on 8 key criteria
- **Calendar Spread Analysis**: Generation of optimal calendar spread strategies
- **Interactive Dashboard**: Modern web interface with real-time updates
- **Risk Assessment**: Calculation of risk/reward ratios and profit zones
- **Data Export**: CSV export functionality for analysis results

## Project Structure

```
agentic-calendar-trading/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Application styles
│   ├── js/
│   │   └── app.js        # Frontend JavaScript
│   ├── images/           # Image assets
│   └── data/             # Data files (CSV, etc.)
└── templates/            # HTML templates
    └── index.html        # Main application template
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-calendar-trading
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Dashboard
- View real-time screening statistics
- Monitor system status and scan intervals
- See top qualified stocks

### Stock Screening
- Configure screening criteria
- View all analyzed stocks with filtering options
- Export results to CSV

### Calendar Spreads
- Analyze calendar spread opportunities
- View profit/loss charts
- Review strategy guides

### Settings
- Adjust screening parameters
- Customize analysis criteria

## API Endpoints

- `GET /api/data` - Get all application data
- `GET /api/stocks` - Get stock screening results
- `GET /api/calendar-spreads` - Get calendar spread analysis
- `GET /api/screening-criteria` - Get current screening criteria
- `POST /api/screening-criteria` - Update screening criteria
- `POST /api/refresh-scan` - Trigger new stock scan

## Development

To extend the application:

1. **Add new screening criteria**: Update the `screening_criteria` in `app.py`
2. **Integrate real market data**: Add API clients in a new `services/` directory
3. **Add database support**: Use Flask-SQLAlchemy for data persistence
4. **Add authentication**: Implement user management with Flask-Login

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Roadmap

- [ ] Real-time market data integration
- [ ] Database support with SQLAlchemy
- [ ] User authentication and portfolios
- [ ] Advanced trading strategies
- [ ] Mobile app development
- [ ] Backtesting capabilities
- [ ] Risk management tools

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/agentic-calendar-trading/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about your environment and the issue

## Screenshots

### Dashboard
![Dashboard](static/images/dashboard-screenshot.png)

### Stock Screening
![Stock Screening](static/images/screening-screenshot.png)

### Calendar Spreads
![Calendar Spreads](static/images/calendar-screenshot.png)

## Acknowledgments

- Chart.js for interactive charts
- Flask framework for the web application
- Bootstrap-inspired CSS framework for UI components

## Disclaimer

This software is for educational and research purposes only. It should not be used as the sole basis for making trading decisions. Trading involves substantial risk of loss and is not suitable for all investors.

## License

This project is licensed under the MIT License.
