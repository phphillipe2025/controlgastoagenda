import requests
import sys
import json
from datetime import datetime, timedelta
import time

class ExpenseTrackerAPITester:
    def __init__(self, base_url="https://expense-tracker-493.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, params=None, response_type='json'):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        if data:
            print(f"   Data: {data}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                if response_type == 'json':
                    try:
                        response_data = response.json()
                        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                        return True, response_data
                    except:
                        return True, {}
                else:
                    print(f"   Response type: {response.headers.get('content-type', 'unknown')}")
                    return True, response.content
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self, username, email, password):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"username": username, "email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token received: {self.token[:20]}...")
            return True
        return False

    def test_login(self, username, password):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token received: {self.token[:20]}...")
            return True
        return False

    def test_create_expense(self, description, amount, category=None):
        """Create an expense"""
        data = {"description": description, "amount": amount}
        if category:
            data["category"] = category
            
        success, response = self.run_test(
            f"Create Expense: {description}",
            "POST",
            "expenses",
            200,
            data=data
        )
        if success and 'id' in response:
            print(f"   Expense ID: {response['id']}")
            print(f"   Category assigned: {response.get('category', 'None')}")
            return response['id']
        return None

    def test_get_expenses(self):
        """Get all expenses"""
        success, response = self.run_test(
            "Get All Expenses",
            "GET",
            "expenses",
            200
        )
        if success:
            print(f"   Found {len(response)} expenses")
            return response
        return []

    def test_update_expense(self, expense_id, description=None, amount=None, category=None):
        """Update an expense"""
        data = {}
        if description:
            data["description"] = description
        if amount:
            data["amount"] = amount
        if category:
            data["category"] = category
            
        success, response = self.run_test(
            f"Update Expense {expense_id}",
            "PUT",
            f"expenses/{expense_id}",
            200,
            data=data
        )
        return success

    def test_delete_expense(self, expense_id):
        """Delete an expense"""
        success, response = self.run_test(
            f"Delete Expense {expense_id}",
            "DELETE",
            f"expenses/{expense_id}",
            200
        )
        return success

    def test_dashboard_data(self):
        """Get dashboard data"""
        success, response = self.run_test(
            "Get Dashboard Data",
            "GET",
            "dashboard",
            200
        )
        if success:
            print(f"   Total spent: {response.get('total_spent', 0)}")
            print(f"   Total expenses: {response.get('total_expenses', 0)}")
            print(f"   Categories: {list(response.get('categories', {}).keys())}")
        return success, response

    def test_ai_insights(self):
        """Get AI insights"""
        print("   Waiting for AI processing...")
        time.sleep(3)  # Wait for AI processing
        
        success, response = self.run_test(
            "Get AI Insights",
            "GET",
            "ai/insights",
            200
        )
        if success:
            insights = response.get('insights', response.get('message', ''))
            print(f"   Insights: {insights[:100]}...")
        return success

    def test_ai_predictions(self):
        """Get AI predictions"""
        print("   Waiting for AI processing...")
        time.sleep(3)  # Wait for AI processing
        
        success, response = self.run_test(
            "Get AI Predictions",
            "GET",
            "ai/predictions",
            200
        )
        if success:
            predictions = response.get('predictions', '')
            print(f"   Predictions: {predictions[:100]}...")
        return success

    # NEW FEATURE TESTS
    def test_salary_endpoints(self):
        """Test salary PUT and GET endpoints"""
        print("\n💰 TESTING NEW SALARY FUNCTIONALITY")
        
        # Test PUT /api/user/salary
        salary_data = {"salary": 5000.00}
        success_put, _ = self.run_test(
            "Set Salary (PUT /user/salary)",
            "PUT",
            "user/salary", 
            200,
            data=salary_data
        )
        
        # Test GET /api/user/salary
        success_get, response = self.run_test(
            "Get Salary (GET /user/salary)",
            "GET",
            "user/salary",
            200
        )
        
        if success_get and response.get('salary') == 5000.0:
            print("✅ Salary correctly set and retrieved: R$ 5000.00")
            return True
        else:
            print("❌ Salary not correctly set/retrieved")
            return False

    def test_installment_expenses(self):
        """Test installment expenses endpoints"""
        print("\n💳 TESTING NEW INSTALLMENT EXPENSES")
        
        # Test POST /api/installment-expenses
        installment_data = {
            "description": "Notebook",
            "total_amount": 2400.00,
            "installments": 12,
            "category": "Tecnologia"
        }
        
        success_post, response = self.run_test(
            "Create Installment Expense (POST /installment-expenses)",
            "POST",
            "installment-expenses",
            200,
            data=installment_data
        )
        
        # Test GET /api/installment-expenses
        success_get, installments = self.run_test(
            "Get Installment Expenses (GET /installment-expenses)",
            "GET", 
            "installment-expenses",
            200
        )
        
        if success_get and len(installments) > 0:
            installment = installments[0]
            expected_monthly = 2400.00 / 12
            if abs(installment['monthly_amount'] - expected_monthly) < 0.01:
                print(f"✅ Installment correctly calculated: R$ {installment['monthly_amount']:.2f}/month")
                return True
            else:
                print(f"❌ Installment calculation wrong: expected {expected_monthly}, got {installment['monthly_amount']}")
        
        return False

    def test_dashboard_with_balance(self):
        """Test dashboard endpoint with new balance calculation"""
        print("\n📈 TESTING NEW DASHBOARD WITH BALANCE")
        
        success, dashboard = self.run_test(
            "Get Dashboard Data (GET /dashboard)",
            "GET",
            "dashboard",
            200
        )
        
        if success:
            salary = dashboard.get('salary', 0)
            current_month_spent = dashboard.get('current_month_spent', 0)
            current_balance = dashboard.get('current_balance', 0)
            
            expected_balance = salary - current_month_spent
            
            print(f"   Salary: R$ {salary:.2f}")
            print(f"   Current Month Spent: R$ {current_month_spent:.2f}")
            print(f"   Current Balance: R$ {current_balance:.2f}")
            print(f"   Expected Balance: R$ {expected_balance:.2f}")
            
            # Check if all new fields are present
            required_fields = ['salary', 'current_balance', 'current_month_spent']
            missing_fields = [field for field in required_fields if field not in dashboard]
            
            if missing_fields:
                print(f"❌ Dashboard missing new fields: {missing_fields}")
                return False
            
            if abs(current_balance - expected_balance) < 0.01:
                print("✅ Balance calculation is correct")
                return True
            else:
                print("❌ Balance calculation is incorrect")
        
        return False

    def test_period_reports(self):
        """Test new period reports endpoint"""
        print("\n📊 TESTING NEW PERIOD REPORTS")
        
        # Test with current month
        start_date = datetime.now().replace(day=1).isoformat()
        end_date = datetime.now().isoformat()
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        success, report = self.run_test(
            "Get Period Report (GET /reports/period)",
            "GET",
            "reports/period",
            200,
            params=params
        )
        
        if success:
            required_fields = ['period', 'total_spent', 'total_expenses', 'categories', 'daily_data', 'expenses']
            missing_fields = [field for field in required_fields if field not in report]
            
            if not missing_fields:
                print(f"✅ Report contains all required fields")
                print(f"   Total spent: R$ {report['total_spent']:.2f}")
                print(f"   Total expenses: {report['total_expenses']}")
                print(f"   Categories: {len(report['categories'])}")
                print(f"   Daily data points: {len(report['daily_data'])}")
                return True
            else:
                print(f"❌ Report missing fields: {missing_fields}")
        
        return False

    def test_pdf_export(self):
        """Test new PDF export endpoint"""
        print("\n📄 TESTING NEW PDF EXPORT")
        
        start_date = datetime.now().replace(day=1).isoformat()
        end_date = datetime.now().isoformat()
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        success, pdf_content = self.run_test(
            "Export PDF Report (GET /reports/export-pdf)",
            "GET",
            "reports/export-pdf",
            200,
            params=params,
            response_type='binary'
        )
        
        if success and pdf_content:
            # Check if it's actually a PDF
            if pdf_content[:4] == b'%PDF':
                print(f"✅ PDF export successful, size: {len(pdf_content)} bytes")
                return True
            else:
                print("❌ Response is not a valid PDF")
        
        return False

def main():
    print("🚀 Starting Expense Tracker API Tests")
    print("=" * 50)
    
    # Setup
    tester = ExpenseTrackerAPITester()
    timestamp = datetime.now().strftime('%H%M%S')
    test_user = f"teste_{timestamp}"
    test_email = f"teste_{timestamp}@email.com"
    test_password = "123456"

    print(f"Test user: {test_user}")
    print(f"Test email: {test_email}")

    # Test 1: User Registration
    if not tester.test_register(test_user, test_email, test_password):
        print("❌ Registration failed, stopping tests")
        return 1

    # Test 2: Create expenses with AI categorization
    expense_ids = []
    
    # Test expense 1: Should be categorized as "Alimentação"
    expense_id1 = tester.test_create_expense("Almoço no McDonald's", 25.00)
    if expense_id1:
        expense_ids.append(expense_id1)
    
    # Test expense 2: Should be categorized as "Transporte"  
    expense_id2 = tester.test_create_expense("Uber para trabalho", 15.00)
    if expense_id2:
        expense_ids.append(expense_id2)
    
    # Test expense 3: Manual category
    expense_id3 = tester.test_create_expense("Compra de livros", 45.00, "Educação")
    if expense_id3:
        expense_ids.append(expense_id3)

    # Test 3: Get all expenses
    expenses = tester.test_get_expenses()

    # Test 4: Update an expense
    if expense_ids:
        tester.test_update_expense(expense_ids[0], description="Almoço no McDonald's - Atualizado", amount=30.00)

    # Test 5: Dashboard data
    tester.test_dashboard_data()

    # Test 6: AI Insights (requires expenses)
    if expenses:
        tester.test_ai_insights()

    # Test 7: AI Predictions (requires expenses)
    if expenses:
        tester.test_ai_predictions()

    # Test 8: Delete an expense
    if expense_ids:
        tester.test_delete_expense(expense_ids[-1])

    # Test 9: Test login with existing user
    tester.token = None  # Reset token
    tester.test_login(test_user, test_password)

    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())