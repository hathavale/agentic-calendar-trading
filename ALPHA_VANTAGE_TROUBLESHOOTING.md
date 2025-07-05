# Alpha Vantage API Troubleshooting Guide

This guide helps diagnose and resolve common issues with Alpha Vantage API integration in the Agentic Calendar Trading System.

## Quick Diagnostic Commands

### 1. Web Interface Diagnostics
- **Simple Test**: `GET /api/diagnostics/simple?symbol=AAPL`
- **Full Diagnostics**: `GET /api/diagnostics?symbol=AAPL`

### 2. Command Line Diagnostics
```bash
# Run comprehensive diagnostics
python diagnostics/alpha_vantage_diagnostic.py AAPL

# Check specific symbol
python diagnostics/alpha_vantage_diagnostic.py MSFT
```

### 3. Environment Check
```bash
# Check if API key is set
echo $ALPHA_VANTAGE_API_KEY

# Test basic connectivity
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=demo"
```

## Common Error Messages and Solutions

### 🔑 "API key not found" / "overview API returned no data"

**Symptoms:**
- Log messages: `❌ Alpha Vantage API key not found`
- System falls back to yfinance
- Missing fundamental data in analysis

**Solutions:**
1. **Set the API Key:**
   ```bash
   export ALPHA_VANTAGE_API_KEY="your_api_key_here"
   ```

2. **Get a Free API Key:**
   - Visit: https://www.alphavantage.co/support/#api-key
   - Sign up for free (500 requests/day limit)
   - Premium plans available for higher limits

3. **Verify API Key Format:**
   - Should be 16+ characters
   - Alphanumeric string
   - No spaces or special characters

### ⚠️ "Rate Limited" / "Thank you for using Alpha Vantage!"

**Symptoms:**
- Log messages: `⚠️ Alpha Vantage API Note: Thank you for using Alpha Vantage!`
- Intermittent data failures
- API responses contain "Note" field

**Solutions:**
1. **Wait Between Requests:**
   - Free tier: 5 requests/minute, 500/day
   - Wait 12+ seconds between requests

2. **Upgrade API Plan:**
   - Visit: https://www.alphavantage.co/premium/
   - Premium plans offer higher rate limits

3. **Use Caching:**
   - System already implements caching
   - Data is cached for the configured duration

### 🌐 "HTTP Error" / Connection Issues

**Symptoms:**
- Log messages: `❌ Alpha Vantage overview API HTTP error`
- Network timeouts
- Connection refused errors

**Solutions:**
1. **Check Internet Connection:**
   ```bash
   ping www.alphavantage.co
   ```

2. **Verify Firewall Settings:**
   - Ensure outbound HTTPS (443) is allowed
   - Check corporate proxy settings

3. **Test Direct API Access:**
   ```bash
   curl -v "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=demo"
   ```

### 🤔 "Unexpected response format" / Invalid Symbol

**Symptoms:**
- Log messages: `🤔 Alpha Vantage overview returned unexpected format`
- Data parsing errors
- Missing expected response fields

**Solutions:**
1. **Verify Symbol Format:**
   - Use standard ticker symbols (AAPL, MSFT, GOOGL)
   - No spaces or special characters
   - US exchanges primarily supported

2. **Check Symbol Validity:**
   ```bash
   # Test known good symbol
   python diagnostics/alpha_vantage_diagnostic.py AAPL
   ```

3. **Review API Documentation:**
   - Visit: https://www.alphavantage.co/documentation/

## Diagnostic Output Interpretation

### ✅ Success Indicators
- `✅ Successfully fetched overview for SYMBOL`
- `✅ Successfully connected to Alpha Vantage`
- HTTP status 200 responses
- Valid data in response fields

### ❌ Failure Indicators
- `❌ Alpha Vantage API Error: [message]`
- `❌ Alpha Vantage API key not found`
- HTTP status codes 4xx/5xx
- Empty or malformed responses

### ⚠️ Warning Indicators
- `⚠️ Alpha Vantage API Note: [rate limit message]`
- `⚠️ Alpha Vantage API Info: [informational message]`
- Fallback to yfinance activated

## System Behavior with API Issues

### Automatic Fallback
The system automatically falls back to yfinance when:
- Alpha Vantage API key is missing
- Rate limits are exceeded
- Network connectivity issues occur
- Invalid/unexpected responses received

### Data Source Priority
1. **Alpha Vantage** (default, comprehensive data)
2. **yfinance** (fallback, basic data)
3. **Sample data** (demonstration purposes)

### Caching Behavior
- Successful responses cached for configured duration
- Cache prevents redundant API calls
- Failed requests not cached
- Cache keys include symbol and time period

## Configuration Options

### Data Source Configuration (config.json)
```json
{
  "data_sources": {
    "default": "alpha_vantage",
    "fallback_order": ["alpha_vantage", "yfinance"],
    "alpha_vantage": {
      "timeout": 30,
      "cache_duration_minutes": 60
    }
  }
}
```

### Environment Variables
- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `DATA_SOURCE`: Override default data source
- `FLASK_ENV`: Set to 'development' for debug logging

## Performance Optimization

### Rate Limit Management
- Implement request queuing for high-volume usage
- Use batch requests where available
- Cache frequently requested data

### Error Handling Best Practices
- Implement exponential backoff for retries
- Monitor API usage quotas
- Log detailed error information for debugging

### Monitoring and Alerting
- Track API success/failure rates
- Monitor response times
- Alert on quota exhaustion

## Advanced Troubleshooting

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Network Diagnostics
```bash
# Test DNS resolution
nslookup www.alphavantage.co

# Test HTTPS connectivity
openssl s_client -connect www.alphavantage.co:443

# Check proxy settings
env | grep -i proxy
```

### API Response Analysis
- Save raw API responses for analysis
- Compare working vs. failing requests
- Check for subtle format differences
- Validate JSON structure

## Support Resources

### Alpha Vantage Support
- **Documentation**: https://www.alphavantage.co/documentation/
- **Support**: https://www.alphavantage.co/support/
- **Status Page**: Check for service outages

### Application Support
- Check application logs in `alpha_vantage_diagnostic.log`
- Run full diagnostics: `python diagnostics/alpha_vantage_diagnostic.py`
- Use Flask diagnostic endpoints: `/api/diagnostics/simple`

## Common Solutions Summary

| Issue | Quick Fix | Long-term Solution |
|-------|-----------|-------------------|
| No API Key | Set `ALPHA_VANTAGE_API_KEY` | Get premium API key |
| Rate Limited | Wait 15 minutes | Upgrade API plan |
| Network Error | Check internet | Review firewall rules |
| Invalid Symbol | Use valid ticker | Implement symbol validation |
| Timeout | Increase timeout | Optimize network/caching |

Remember: The system is designed to gracefully handle Alpha Vantage issues by falling back to yfinance, ensuring continuous operation even when the primary data source is unavailable.
