import requests
import sys
import json
from datetime import datetime
import time

class EmergentChatAPITester:
    def __init__(self, base_url="https://0c7a9b73-4815-4b95-8c7a-88602d3618c8.preview.emergentagent.com"):
        self.base_url = base_url
        self.token1 = None
        self.token2 = None
        self.user1_id = None
        self.user2_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def run_api_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                print(f"   Status: {response.status_code} ✅")
                try:
                    response_data = response.json()
                    self.log_test(name, True)
                    return True, response_data
                except:
                    self.log_test(name, True)
                    return True, {}
            else:
                error_details = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_response = response.json()
                    error_details += f" - {error_response}"
                except:
                    error_details += f" - {response.text[:200]}"
                
                print(f"   Status: {response.status_code} ❌")
                self.log_test(name, False, error_details)
                return False, {}

        except Exception as e:
            error_details = f"Request failed: {str(e)}"
            print(f"   Error: {error_details} ❌")
            self.log_test(name, False, error_details)
            return False, {}

    def test_basic_connectivity(self):
        """Test if backend is accessible"""
        print("\n" + "="*50)
        print("TESTING BASIC CONNECTIVITY")
        print("="*50)
        
        try:
            response = requests.get(f"{self.base_url}/api/users", timeout=5)
            # We expect 401 since no auth, but this means backend is running
            if response.status_code in [401, 422]:
                self.log_test("Backend Connectivity", True)
                return True
            else:
                self.log_test("Backend Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Connectivity", False, str(e))
            return False

    def test_user_registration(self):
        """Test user registration"""
        print("\n" + "="*50)
        print("TESTING USER REGISTRATION")
        print("="*50)
        
        # Test user 1 registration
        user1_data = {
            "username": "testuser1",
            "email": "test1@example.com",
            "password": "password123"
        }
        
        success, response = self.run_api_test(
            "Register User 1",
            "POST",
            "api/auth/register",
            200,
            data=user1_data
        )
        
        if success and 'id' in response:
            self.user1_id = response['id']
            print(f"   User 1 ID: {self.user1_id}")
        
        # Test user 2 registration
        user2_data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "password123"
        }
        
        success, response = self.run_api_test(
            "Register User 2",
            "POST",
            "api/auth/register",
            200,
            data=user2_data
        )
        
        if success and 'id' in response:
            self.user2_id = response['id']
            print(f"   User 2 ID: {self.user2_id}")
        
        # Test duplicate registration (should fail)
        success, response = self.run_api_test(
            "Duplicate Registration (should fail)",
            "POST",
            "api/auth/register",
            400,
            data=user1_data
        )
        
        return self.user1_id is not None and self.user2_id is not None

    def test_user_login(self):
        """Test user login"""
        print("\n" + "="*50)
        print("TESTING USER LOGIN")
        print("="*50)
        
        # Test user 1 login
        login_data = {
            "username": "testuser1",
            "password": "password123"
        }
        
        success, response = self.run_api_test(
            "Login User 1",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token1 = response['access_token']
            print(f"   User 1 Token: {self.token1[:20]}...")
        
        # Test user 2 login
        login_data = {
            "username": "testuser2",
            "password": "password123"
        }
        
        success, response = self.run_api_test(
            "Login User 2",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token2 = response['access_token']
            print(f"   User 2 Token: {self.token2[:20]}...")
        
        # Test invalid login
        invalid_login = {
            "username": "testuser1",
            "password": "wrongpassword"
        }
        
        success, response = self.run_api_test(
            "Invalid Login (should fail)",
            "POST",
            "api/auth/login",
            401,
            data=invalid_login
        )
        
        return self.token1 is not None and self.token2 is not None

    def test_authenticated_endpoints(self):
        """Test authenticated endpoints"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATED ENDPOINTS")
        print("="*50)
        
        if not self.token1:
            self.log_test("Authenticated Endpoints", False, "No token available")
            return False
        
        # Test get current user
        success, response = self.run_api_test(
            "Get Current User",
            "GET",
            "api/users/me",
            200,
            token=self.token1
        )
        
        # Test get all users
        success, response = self.run_api_test(
            "Get All Users",
            "GET",
            "api/users",
            200,
            token=self.token1
        )
        
        if success:
            print(f"   Found {len(response)} users")
        
        # Test unauthorized access
        success, response = self.run_api_test(
            "Unauthorized Access (should fail)",
            "GET",
            "api/users/me",
            401
        )
        
        return True

    def test_messaging_endpoints(self):
        """Test messaging functionality"""
        print("\n" + "="*50)
        print("TESTING MESSAGING ENDPOINTS")
        print("="*50)
        
        if not (self.token1 and self.token2 and self.user1_id and self.user2_id):
            self.log_test("Messaging Endpoints", False, "Missing tokens or user IDs")
            return False
        
        # Test sending message from user 1 to user 2
        message_data = {
            "receiver_id": self.user2_id,
            "content": "Hello from testuser1!",
            "message_type": "text"
        }
        
        success, response = self.run_api_test(
            "Send Message User1 -> User2",
            "POST",
            "api/messages",
            200,
            data=message_data,
            token=self.token1
        )
        
        message_id = None
        if success and 'id' in response:
            message_id = response['id']
            print(f"   Message ID: {message_id}")
        
        # Test sending message from user 2 to user 1
        message_data = {
            "receiver_id": self.user1_id,
            "content": "Hello back from testuser2!",
            "message_type": "text"
        }
        
        success, response = self.run_api_test(
            "Send Message User2 -> User1",
            "POST",
            "api/messages",
            200,
            data=message_data,
            token=self.token2
        )
        
        # Test getting messages between users
        success, response = self.run_api_test(
            "Get Messages User1 <-> User2",
            "GET",
            f"api/messages/{self.user2_id}",
            200,
            token=self.token1
        )
        
        if success:
            print(f"   Found {len(response)} messages")
        
        # Test sending message to non-existent user
        invalid_message = {
            "receiver_id": "non-existent-id",
            "content": "This should fail",
            "message_type": "text"
        }
        
        success, response = self.run_api_test(
            "Send Message to Non-existent User (should fail)",
            "POST",
            "api/messages",
            404,
            data=invalid_message,
            token=self.token1
        )
        
        return True

    def test_logout(self):
        """Test logout functionality"""
        print("\n" + "="*50)
        print("TESTING LOGOUT")
        print("="*50)
        
        if not self.token1:
            self.log_test("Logout", False, "No token available")
            return False
        
        success, response = self.run_api_test(
            "Logout User 1",
            "POST",
            "api/auth/logout",
            200,
            token=self.token1
        )
        
        return success

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_run - self.tests_passed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['name']}: {result['details']}")
        
        print("\n" + "="*60)

def main():
    print("🚀 Starting EmergentChat API Tests")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = EmergentChatAPITester()
    
    # Run tests in order
    tests = [
        tester.test_basic_connectivity,
        tester.test_user_registration,
        tester.test_user_login,
        tester.test_authenticated_endpoints,
        tester.test_messaging_endpoints,
        tester.test_logout
    ]
    
    for test in tests:
        try:
            test()
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    tester.print_summary()
    
    # Return exit code based on results
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())