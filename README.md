# Agentic Calendar Spread Trading System

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

## License

This project is licensed under the MIT License.
