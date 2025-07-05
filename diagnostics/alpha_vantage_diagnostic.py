#!/usr/bin/env python3
"""
Alpha Vantage API Diagnostic Tool

This script helps diagnose common issues with Alpha Vantage API integration:
- API key validation
- Rate limit checking
- Symbol validation
- Response format analysis
- Network connectivity testing

Usage:
    python alpha_vantage_diagnostic.py [SYMBOL]
    
Environment Variables:
    ALPHA_VANTAGE_API_KEY: Your Alpha Vantage API key
"""

import os
import sys
import time
import json
import requests
from typing import Dict, Optional, List
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('alpha_vantage_diagnostic.log')
    ]
)
logger = logging.getLogger(__name__)

class AlphaVantageDiagnostic:
    """Comprehensive Alpha Vantage API diagnostic tool"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self.timeout = 30
        
    def run_full_diagnostic(self, symbol: str = 'AAPL') -> Dict:
        """Run complete diagnostic suite"""
        print(f"\n{'='*60}")
        print(f"🔍 ALPHA VANTAGE API DIAGNOSTIC REPORT")
        print(f"{'='*60}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Target Symbol: {symbol}")
        print(f"{'='*60}\n")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'tests': {}
        }
        
        # Run diagnostics
        results['tests']['api_key'] = self._test_api_key()
        results['tests']['connectivity'] = self._test_connectivity()
        results['tests']['overview'] = self._test_overview(symbol)
        results['tests']['quote'] = self._test_quote(symbol)
        results['tests']['daily'] = self._test_daily(symbol)
        results['tests']['rate_limit'] = self._test_rate_limit()
        
        # Generate summary
        self._print_summary(results)
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _test_api_key(self) -> Dict:
        """Test API key validity"""
        print("🔑 Testing API Key...")
        
        if not self.api_key:
            result = {
                'status': 'FAIL',
                'message': 'API key not found in environment variables',
                'recommendation': 'Set ALPHA_VANTAGE_API_KEY environment variable'
            }
            print(f"   ❌ {result['message']}")
            return result
        
        if len(self.api_key) < 10:
            result = {
                'status': 'FAIL',
                'message': f'API key appears too short ({len(self.api_key)} characters)',
                'recommendation': 'Verify API key from Alpha Vantage dashboard'
            }
            print(f"   ❌ {result['message']}")
            return result
        
        result = {
            'status': 'PASS',
            'message': f'API key found ({len(self.api_key)} characters)',
            'key_preview': f"{self.api_key[:4]}...{self.api_key[-4:]}"
        }
        print(f"   ✅ {result['message']}")
        return result
    
    def _test_connectivity(self) -> Dict:
        """Test basic connectivity to Alpha Vantage"""
        print("🌐 Testing Connectivity...")
        
        try:
            # Test basic GET request
            response = requests.get(
                self.base_url,
                params={'function': 'GLOBAL_QUOTE', 'symbol': 'AAPL', 'apikey': 'demo'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = {
                    'status': 'PASS',
                    'message': f'Successfully connected to Alpha Vantage (HTTP {response.status_code})',
                    'response_time': response.elapsed.total_seconds()
                }
                print(f"   ✅ {result['message']}")
                print(f"   📊 Response time: {result['response_time']:.2f}s")
            else:
                result = {
                    'status': 'FAIL',
                    'message': f'HTTP error: {response.status_code}',
                    'recommendation': 'Check network connection and Alpha Vantage service status'
                }
                print(f"   ❌ {result['message']}")
            
            return result
            
        except requests.exceptions.Timeout:
            result = {
                'status': 'FAIL',
                'message': 'Connection timeout',
                'recommendation': 'Check network connection or try again later'
            }
            print(f"   ❌ {result['message']}")
            return result
            
        except Exception as e:
            result = {
                'status': 'FAIL',
                'message': f'Connection error: {str(e)}',
                'recommendation': 'Check network connection and firewall settings'
            }
            print(f"   ❌ {result['message']}")
            return result
    
    def _test_overview(self, symbol: str) -> Dict:
        """Test company overview endpoint"""
        print(f"📊 Testing Company Overview for {symbol}...")
        
        if not self.api_key:
            result = {
                'status': 'SKIP',
                'message': 'Skipping due to missing API key'
            }
            print(f"   ⏭️ {result['message']}")
            return result
        
        try:
            response = requests.get(
                self.base_url,
                params={
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.api_key
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                result = {
                    'status': 'FAIL',
                    'message': f'HTTP error: {response.status_code}',
                    'response_preview': response.text[:200]
                }
                print(f"   ❌ {result['message']}")
                return result
            
            data = response.json()
            
            # Analyze response
            if 'Error Message' in data:
                result = {
                    'status': 'FAIL',
                    'message': f"API Error: {data['Error Message']}",
                    'recommendation': 'Check symbol format or try a different symbol'
                }
                print(f"   ❌ {result['message']}")
                
            elif 'Note' in data:
                result = {
                    'status': 'RATE_LIMITED',
                    'message': f"Rate Limited: {data['Note']}",
                    'recommendation': 'Wait before making more requests or upgrade API plan'
                }
                print(f"   ⚠️ {result['message']}")
                
            elif 'Information' in data:
                result = {
                    'status': 'INFO',
                    'message': f"API Info: {data['Information']}",
                    'recommendation': 'Check API documentation for more details'
                }
                print(f"   ℹ️ {result['message']}")
                
            elif 'Symbol' in data:
                result = {
                    'status': 'PASS',
                    'message': f"Successfully retrieved overview for {symbol}",
                    'company_name': data.get('Name', 'Unknown'),
                    'sector': data.get('Sector', 'Unknown'),
                    'data_keys': list(data.keys())[:10]  # First 10 keys
                }
                print(f"   ✅ {result['message']}")
                print(f"   🏢 Company: {result['company_name']}")
                print(f"   🏭 Sector: {result['sector']}")
                
            else:
                result = {
                    'status': 'UNEXPECTED',
                    'message': 'Unexpected response format',
                    'response_keys': list(data.keys()),
                    'response_preview': str(data)[:200]
                }
                print(f"   🤔 {result['message']}")
                print(f"   📋 Keys: {result['response_keys']}")
            
            return result
            
        except Exception as e:
            result = {
                'status': 'FAIL',
                'message': f'Exception: {str(e)}',
                'recommendation': 'Check API key and network connection'
            }
            print(f"   💥 {result['message']}")
            return result
    
    def _test_quote(self, symbol: str) -> Dict:
        """Test global quote endpoint"""
        print(f"💰 Testing Global Quote for {symbol}...")
        
        if not self.api_key:
            result = {
                'status': 'SKIP',
                'message': 'Skipping due to missing API key'
            }
            print(f"   ⏭️ {result['message']}")
            return result
        
        try:
            response = requests.get(
                self.base_url,
                params={
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.api_key
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                result = {
                    'status': 'FAIL',
                    'message': f'HTTP error: {response.status_code}',
                    'response_preview': response.text[:200]
                }
                print(f"   ❌ {result['message']}")
                return result
            
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                result = {
                    'status': 'PASS',
                    'message': f"Successfully retrieved quote for {symbol}",
                    'price': quote.get('05. price', 'Unknown'),
                    'change': quote.get('09. change', 'Unknown'),
                    'quote_keys': list(quote.keys())
                }
                print(f"   ✅ {result['message']}")
                print(f"   💵 Price: ${result['price']}")
                print(f"   📈 Change: {result['change']}")
                
            elif 'Note' in data:
                result = {
                    'status': 'RATE_LIMITED',
                    'message': f"Rate Limited: {data['Note']}"
                }
                print(f"   ⚠️ {result['message']}")
                
            else:
                result = {
                    'status': 'FAIL',
                    'message': 'No quote data returned',
                    'response_keys': list(data.keys()),
                    'response_preview': str(data)[:200]
                }
                print(f"   ❌ {result['message']}")
            
            return result
            
        except Exception as e:
            result = {
                'status': 'FAIL',
                'message': f'Exception: {str(e)}'
            }
            print(f"   💥 {result['message']}")
            return result
    
    def _test_daily(self, symbol: str) -> Dict:
        """Test daily time series endpoint"""
        print(f"📈 Testing Daily Time Series for {symbol}...")
        
        if not self.api_key:
            result = {
                'status': 'SKIP',
                'message': 'Skipping due to missing API key'
            }
            print(f"   ⏭️ {result['message']}")
            return result
        
        try:
            response = requests.get(
                self.base_url,
                params={
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'apikey': self.api_key,
                    'outputsize': 'compact'
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                result = {
                    'status': 'FAIL',
                    'message': f'HTTP error: {response.status_code}',
                    'response_preview': response.text[:200]
                }
                print(f"   ❌ {result['message']}")
                return result
            
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                latest_date = max(time_series.keys()) if time_series else None
                result = {
                    'status': 'PASS',
                    'message': f"Successfully retrieved daily data for {symbol}",
                    'data_points': len(time_series),
                    'latest_date': latest_date,
                    'latest_close': time_series.get(latest_date, {}).get('4. close', 'Unknown') if latest_date else None
                }
                print(f"   ✅ {result['message']}")
                print(f"   📊 Data points: {result['data_points']}")
                print(f"   📅 Latest: {result['latest_date']}")
                
            elif 'Note' in data:
                result = {
                    'status': 'RATE_LIMITED',
                    'message': f"Rate Limited: {data['Note']}"
                }
                print(f"   ⚠️ {result['message']}")
                
            else:
                result = {
                    'status': 'FAIL',
                    'message': 'No time series data returned',
                    'response_keys': list(data.keys()),
                    'response_preview': str(data)[:200]
                }
                print(f"   ❌ {result['message']}")
            
            return result
            
        except Exception as e:
            result = {
                'status': 'FAIL',
                'message': f'Exception: {str(e)}'
            }
            print(f"   💥 {result['message']}")
            return result
    
    def _test_rate_limit(self) -> Dict:
        """Test rate limiting behavior"""
        print("⏱️ Testing Rate Limit Behavior...")
        
        if not self.api_key:
            result = {
                'status': 'SKIP',
                'message': 'Skipping due to missing API key'
            }
            print(f"   ⏭️ {result['message']}")
            return result
        
        # Make multiple quick requests to test rate limiting
        request_times = []
        responses = []
        
        for i in range(3):
            start_time = time.time()
            try:
                response = requests.get(
                    self.base_url,
                    params={
                        'function': 'GLOBAL_QUOTE',
                        'symbol': 'AAPL',
                        'apikey': self.api_key
                    },
                    timeout=self.timeout
                )
                end_time = time.time()
                request_times.append(end_time - start_time)
                responses.append(response.status_code)
                
                if i < 2:  # Don't sleep after last request
                    time.sleep(1)  # Small delay between requests
                    
            except Exception as e:
                responses.append(f"Error: {str(e)}")
                request_times.append(None)
        
        avg_response_time = sum(t for t in request_times if t is not None) / len([t for t in request_times if t is not None])
        
        result = {
            'status': 'INFO',
            'message': 'Rate limit test completed',
            'response_codes': responses,
            'avg_response_time': avg_response_time,
            'recommendation': 'Free tier: 5 requests/minute, 500 requests/day'
        }
        
        print(f"   ✅ {result['message']}")
        print(f"   📊 Response codes: {result['response_codes']}")
        print(f"   ⏱️ Avg response time: {avg_response_time:.2f}s")
        print(f"   💡 {result['recommendation']}")
        
        return result
    
    def _print_summary(self, results: Dict):
        """Print diagnostic summary"""
        print(f"\n{'='*60}")
        print("📋 DIAGNOSTIC SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(results['tests'])
        passed = sum(1 for test in results['tests'].values() if test['status'] == 'PASS')
        failed = sum(1 for test in results['tests'].values() if test['status'] == 'FAIL')
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(passed/total_tests)*100:.1f}%")
        
        print("\n🎯 RECOMMENDATIONS:")
        for test_name, test_result in results['tests'].items():
            if 'recommendation' in test_result:
                print(f"• {test_name.upper()}: {test_result['recommendation']}")
        
        print(f"\n📄 Full results saved to: alpha_vantage_diagnostic_results.json")
    
    def _save_results(self, results: Dict):
        """Save diagnostic results to file"""
        filename = f"alpha_vantage_diagnostic_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

def main():
    """Main diagnostic function"""
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'
    
    diagnostic = AlphaVantageDiagnostic()
    results = diagnostic.run_full_diagnostic(symbol)
    
    return results

if __name__ == "__main__":
    main()
