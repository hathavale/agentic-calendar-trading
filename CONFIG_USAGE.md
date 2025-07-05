# Configuration-Based Data Source Management

This document explains how to use the new configuration-based data source management system.

## Configuration File

The system now uses a `config.json` file to manage:
- **Data sources** and their settings
- **Default and fallback sources**
- **API key environment variables**
- **Rate limiting parameters**
- **Caching configuration**
- **Default screening criteria**

## Current Configuration

### Default Data Source: Alpha Vantage
- **Primary**: `alpha_vantage` (requires `ALPHA_VANTAGE_API_KEY`)
- **Fallback**: `yfinance` (free, no API key required)

### Supported Data Sources

1. **Alpha Vantage** (Default)
   - Environment Variable: `ALPHA_VANTAGE_API_KEY`
   - Rate Limits: 5/minute, 500/day
   - Requires API key

2. **Yahoo Finance (yfinance)** (Fallback)
   - Environment Variable: None (free)
   - Rate Limits: 60/minute, 2000/day
   - No API key required

3. **EOD Historical Data**
   - Environment Variable: `EODHD_API_KEY`
   - Rate Limits: 20/minute, 100,000/day
   - Requires API key

4. **Yahoo Finance API**
   - Environment Variable: `YAHOO_FINANCE_API_KEY`
   - Rate Limits: 100/minute, 10,000/day
   - Requires API key

## Usage Examples

### 1. Using Alpha Vantage (Default)
```bash
# Set API key
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"

# Run the application
python3 app.py
```

### 2. Force Using yfinance
```python
from services.data_fetcher import DataFetcher

# Explicitly specify yfinance
df = DataFetcher(source="yfinance")
```

### 3. Using EOD Historical Data
```bash
# Set API key
export EODHD_API_KEY="your_eodhd_key"

# Run with EODHD
python3 -c "
from services.data_fetcher import DataFetcher
df = DataFetcher(source='eodhd')
print('Using:', df.source)
"
```

### 4. Dynamic Source Switching
```python
# Switch data source at runtime
df.set_data_source("yfinance")

# Or via Flask API
curl -X POST http://localhost:5001/api/data-source \
  -H "Content-Type: application/json" \
  -d '{"source": "yfinance"}'
```

## Configuration Customization

You can modify `config.json` to:

1. **Change default source**:
   ```json
   "default": "yfinance"
   ```

2. **Update rate limits**:
   ```json
   "rate_limiting": {
     "default_delay_seconds": 1.0,
     "max_retries": 5
   }
   ```

3. **Modify default symbols**:
   ```json
   "screening": {
     "default_symbols": ["SPY", "QQQ", "AAPL"]
   }
   ```

4. **Update screening criteria**:
   ```json
   "screening": {
     "default_criteria": {
       "atr_threshold": 0.03,
       "iv_range": [15, 35]
     }
   }
   ```

## Fallback Behavior

1. **Primary source fails** → Falls back to configured fallback source
2. **No API key provided** → Warning logged, continues with fallback
3. **Rate limit hit** → Automatic retry with exponential backoff
4. **All sources fail** → Falls back to sample data

## Environment Variables

Set these environment variables for the respective data sources:

```bash
# Alpha Vantage (default)
export ALPHA_VANTAGE_API_KEY="your_key_here"

# EOD Historical Data
export EODHD_API_KEY="your_key_here"

# Yahoo Finance API
export YAHOO_FINANCE_API_KEY="your_key_here"

# Generic fallback (deprecated)
export API_KEY="your_key_here"
```

## Benefits

1. **Configuration-driven**: Easy to change settings without code changes
2. **Multi-source support**: Seamless switching between data providers
3. **Intelligent fallbacks**: Automatic failover to backup sources
4. **Rate limit awareness**: Per-source rate limiting configuration
5. **Environment-based**: Secure API key management via environment variables
6. **Production-ready**: Comprehensive error handling and logging
