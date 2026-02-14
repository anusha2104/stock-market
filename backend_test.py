import requests
import sys
import time
from datetime import datetime

class StockAnalyzerAPITester:
    def __init__(self, base_url="https://stockanalyze-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            self.failed_tests.append({
                "test": name,
                "error": "Timeout",
                "timeout": timeout
            })
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_stock_data(self, symbol="AAPL"):
        """Test stock data endpoint"""
        success, response = self.run_test(
            f"Stock Data ({symbol})",
            "GET",
            f"stocks/{symbol}",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['symbol', 'price', 'change', 'change_percent', 'volume', 'timestamp']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"⚠️  Warning: Missing fields in response: {missing_fields}")
            else:
                print(f"   Stock: {response.get('symbol')} - Price: ${response.get('price')}")
        
        return success, response

    def test_stock_chart(self, symbol="AAPL"):
        """Test stock chart data endpoint"""
        success, response = self.run_test(
            f"Stock Chart ({symbol})",
            "GET",
            f"stocks/{symbol}/chart",
            200
        )
        
        if success and isinstance(response, dict):
            data_points = len(response.get('data', []))
            print(f"   Chart data points: {data_points}")
        
        return success, response

    def test_stock_prediction(self, symbol="AAPL"):
        """Test stock prediction endpoint"""
        success, response = self.run_test(
            f"Stock Prediction ({symbol})",
            "GET",
            f"stocks/{symbol}/predict",
            200
        )
        
        if success and isinstance(response, dict):
            print(f"   Prediction: ${response.get('predicted_price')} - Trend: {response.get('trend')}")
        
        return success, response

    def test_technical_indicators(self, symbol="AAPL"):
        """Test technical indicators endpoint"""
        success, response = self.run_test(
            f"Technical Indicators ({symbol})",
            "GET",
            f"stocks/{symbol}/indicators",
            200
        )
        
        if success and isinstance(response, dict):
            indicators = [k for k, v in response.items() if k != 'symbol' and v is not None]
            print(f"   Available indicators: {indicators}")
        
        return success, response

    def test_contact_form(self):
        """Test contact form submission"""
        test_data = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": "test@example.com",
            "message": "This is a test message from automated testing."
        }
        
        success, response = self.run_test(
            "Contact Form",
            "POST",
            "contact",
            200,
            data=test_data
        )
        
        if success and isinstance(response, dict):
            print(f"   Contact ID: {response.get('id')}")
        
        return success, response

    def test_invalid_stock_symbol(self):
        """Test with invalid stock symbol"""
        return self.run_test(
            "Invalid Stock Symbol",
            "GET",
            "stocks/INVALID123",
            404
        )

    def test_rate_limiting_behavior(self):
        """Test multiple rapid requests to check rate limiting"""
        print(f"\n🔍 Testing Rate Limiting Behavior...")
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "META"]
        
        for i, symbol in enumerate(symbols):
            print(f"   Request {i+1}/6: {symbol}")
            success, response = self.run_test(
                f"Rate Limit Test {symbol}",
                "GET",
                f"stocks/{symbol}",
                [200, 429]  # Accept both success and rate limit
            )
            
            if not success:
                break
                
            # Small delay between requests
            time.sleep(0.5)

def main():
    print("🚀 Starting Stock Market Analyzer API Tests")
    print("=" * 50)
    
    tester = StockAnalyzerAPITester()
    
    # Test basic endpoints
    tester.test_root_endpoint()
    
    # Test stock-related endpoints with AAPL
    print(f"\n📊 Testing with AAPL (with delays to avoid rate limits)")
    tester.test_stock_data("AAPL")
    time.sleep(2)  # Wait to avoid rate limiting
    
    tester.test_stock_chart("AAPL")
    time.sleep(2)
    
    tester.test_stock_prediction("AAPL")
    time.sleep(2)
    
    tester.test_technical_indicators("AAPL")
    time.sleep(2)
    
    # Test with different stock symbols
    print(f"\n📊 Testing with TSLA")
    tester.test_stock_data("TSLA")
    time.sleep(2)
    
    print(f"\n📊 Testing with MSFT")
    tester.test_stock_data("MSFT")
    time.sleep(2)
    
    # Test contact form
    tester.test_contact_form()
    
    # Test error handling
    tester.test_invalid_stock_symbol()
    
    # Test rate limiting (this might trigger rate limits)
    print(f"\n⚡ Testing Rate Limiting (may trigger API limits)")
    tester.test_rate_limiting_behavior()
    
    # Print final results
    print(f"\n" + "=" * 50)
    print(f"📊 Test Results Summary")
    print(f"=" * 50)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {len(tester.failed_tests)}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests:")
        for failure in tester.failed_tests:
            print(f"   - {failure.get('test', 'Unknown')}: {failure.get('error', failure.get('actual', 'Unknown error'))}")
    
    return 0 if len(tester.failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())