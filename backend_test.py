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
                response = requests.get(url, headers=test_headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

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

    def test_calendar_spending(self):
        """Test NEW calendar spending endpoint - REVOLUTIONARY FEATURE"""
        print("\n📅 TESTING NEW CALENDAR SPENDING - REVOLUTIONARY FEATURE!")
        
        success, calendar_data = self.run_test(
            "Get Calendar Spending (GET /calendar/spending)",
            "GET",
            "calendar/spending",
            200
        )
        
        if success:
            # Check required fields for calendar functionality
            required_fields = ['month', 'year', 'salary', 'total_spent', 'remaining_balance', 
                             'days_remaining', 'daily_available', 'calendar_data']
            missing_fields = [field for field in required_fields if field not in calendar_data]
            
            if not missing_fields:
                print(f"✅ Calendar data contains all required fields")
                print(f"   Month/Year: {calendar_data['month']}/{calendar_data['year']}")
                print(f"   Salary: R$ {calendar_data['salary']:.2f}")
                print(f"   Total Spent: R$ {calendar_data['total_spent']:.2f}")
                print(f"   Remaining Balance: R$ {calendar_data['remaining_balance']:.2f}")
                print(f"   Days Remaining: {calendar_data['days_remaining']}")
                print(f"   Daily Available: R$ {calendar_data['daily_available']:.2f}")
                print(f"   Calendar Days: {len(calendar_data['calendar_data'])}")
                
                # Verify calendar calculation logic
                expected_daily = calendar_data['remaining_balance'] / calendar_data['days_remaining'] if calendar_data['days_remaining'] > 0 else 0
                actual_daily = calendar_data['daily_available']
                
                if abs(expected_daily - actual_daily) < 0.01:
                    print("✅ Daily spending calculation is CORRECT!")
                    
                    # Check calendar_data structure
                    if calendar_data['calendar_data']:
                        first_day = calendar_data['calendar_data'][0]
                        day_required_fields = ['day', 'spent', 'available', 'is_past', 'is_today', 'is_future', 'status']
                        day_missing = [field for field in day_required_fields if field not in first_day]
                        
                        if not day_missing:
                            print("✅ Calendar day structure is CORRECT!")
                            print(f"   Sample day data: {first_day}")
                            return True
                        else:
                            print(f"❌ Calendar day missing fields: {day_missing}")
                    else:
                        print("❌ Calendar data is empty")
                else:
                    print(f"❌ Daily calculation wrong: expected {expected_daily:.2f}, got {actual_daily:.2f}")
            else:
                print(f"❌ Calendar missing fields: {missing_fields}")
        
        return False

    def test_appointments_crud(self):
        """Test NEW appointments CRUD - AGENDA FUNCTIONALITY"""
        print("\n📋 TESTING NEW APPOINTMENTS CRUD - AGENDA FUNCTIONALITY!")
        
        # Test POST /api/appointments - Create appointment
        tomorrow = datetime.now() + timedelta(days=1)
        appointment_data = {
            "title": "Reunião Importante",
            "description": "Reunião com cliente sobre projeto",
            "date": tomorrow.isoformat(),
            "time": "14:00",
            "location": "Escritório Central"
        }
        
        success_post, response = self.run_test(
            "Create Appointment (POST /appointments)",
            "POST",
            "appointments",
            200,
            data=appointment_data
        )
        
        appointment_id = None
        if success_post and 'id' in response:
            appointment_id = response['id']
            print(f"✅ Appointment created with ID: {appointment_id}")
            print(f"   Title: {response.get('title')}")
            print(f"   Date: {response.get('date')}")
            print(f"   Time: {response.get('time')}")
        else:
            print("❌ Failed to create appointment")
            return False
        
        # Test GET /api/appointments - List appointments
        success_get, appointments = self.run_test(
            "Get All Appointments (GET /appointments)",
            "GET",
            "appointments",
            200
        )
        
        if success_get and len(appointments) > 0:
            print(f"✅ Found {len(appointments)} appointments")
            found_appointment = next((apt for apt in appointments if apt['id'] == appointment_id), None)
            if found_appointment:
                print("✅ Created appointment found in list")
            else:
                print("❌ Created appointment not found in list")
                return False
        else:
            print("❌ No appointments found or request failed")
            return False
        
        # Test GET /api/appointments/month - Get appointments by month
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        success_month, month_appointments = self.run_test(
            f"Get Appointments by Month (GET /appointments/month)",
            "GET",
            "appointments/month",
            200,
            params={"month": current_month, "year": current_year}
        )
        
        if success_month:
            print(f"✅ Month appointments endpoint working, found {len(month_appointments)} appointments")
        else:
            print("❌ Month appointments endpoint failed")
            return False
        
        # Test PUT /api/appointments/{id} - Update appointment
        update_data = {
            "title": "Reunião Atualizada",
            "location": "Escritório Novo"
        }
        
        success_put, updated = self.run_test(
            f"Update Appointment (PUT /appointments/{appointment_id})",
            "PUT",
            f"appointments/{appointment_id}",
            200,
            data=update_data
        )
        
        if success_put and updated.get('title') == "Reunião Atualizada":
            print("✅ Appointment updated successfully")
        else:
            print("❌ Appointment update failed")
            return False
        
        # Test DELETE /api/appointments/{id} - Delete appointment
        success_delete, _ = self.run_test(
            f"Delete Appointment (DELETE /appointments/{appointment_id})",
            "DELETE",
            f"appointments/{appointment_id}",
            200
        )
        
        if success_delete:
            print("✅ Appointment deleted successfully")
            
            # Verify deletion
            success_verify, verify_appointments = self.run_test(
                "Verify Deletion (GET /appointments)",
                "GET",
                "appointments",
                200
            )
            
            if success_verify:
                deleted_found = any(apt['id'] == appointment_id for apt in verify_appointments)
                if not deleted_found:
                    print("✅ Appointment deletion verified - not found in list")
                    return True
                else:
                    print("❌ Appointment still exists after deletion")
            else:
                print("❌ Could not verify deletion")
        else:
            print("❌ Appointment deletion failed")
        
        return False

def main():
    print("🚀 COMPREHENSIVE API TESTS FOR REVOLUTIONARY NEW FEATURES")
    print("Testing: Calendar Intelligence, Appointments Agenda, Salary, Installments, Reports")
    print("=" * 80)
    
    # Setup - Use the specific test user from requirements
    tester = ExpenseTrackerAPITester()
    test_user = "calendario123"  # As specified in requirements
    test_email = "calendario123@test.com"
    test_password = "123456"

    print(f"Test user: {test_user}")
    print(f"Test email: {test_email}")

    # Test 0: Health check first
    health_success, _ = tester.run_test("API Health Check", "GET", "health", 200)
    if not health_success:
        print("❌ API health check failed, stopping tests")
        return 1

    # Test 1: User Registration (or login if exists)
    if not tester.test_register(test_user, test_email, test_password):
        print("⚠️  Registration failed, trying login...")
        if not tester.test_login(test_user, test_password):
            print("❌ Both registration and login failed, stopping tests")
            return 1

    # Test 2: NEW REVOLUTIONARY FEATURE - Salary endpoints (required for calendar)
    print("\n" + "="*60)
    print("🆕 TESTING SALARY FEATURE (Required for Calendar)")
    print("="*60)
    salary_success = tester.test_salary_endpoints()

    # Test 3: Create expenses (required for calendar calculations)
    print("\n💰 Creating expenses for calendar testing...")
    expense_id1 = tester.test_create_expense("Supermercado", 200.00, "Alimentação")
    expense_id2 = tester.test_create_expense("Transporte", 50.00, "Transporte")

    # Test 4: NEW REVOLUTIONARY FEATURE - Calendar Spending Intelligence
    print("\n" + "="*60)
    print("🆕 TESTING REVOLUTIONARY CALENDAR SPENDING INTELLIGENCE!")
    print("="*60)
    calendar_success = tester.test_calendar_spending()

    # Test 5: NEW REVOLUTIONARY FEATURE - Appointments Agenda
    print("\n" + "="*60)
    print("🆕 TESTING REVOLUTIONARY APPOINTMENTS AGENDA!")
    print("="*60)
    appointments_success = tester.test_appointments_crud()

    # Test 6: Dashboard with balance calculation
    print("\n" + "="*50)
    print("🆕 TESTING DASHBOARD WITH BALANCE")
    print("="*50)
    dashboard_success = tester.test_dashboard_with_balance()

    # Test 7: Installment expenses
    print("\n" + "="*50)
    print("🆕 TESTING INSTALLMENT EXPENSES")
    print("="*50)
    installment_success = tester.test_installment_expenses()

    # Test 8: Period reports
    print("\n" + "="*50)
    print("🆕 TESTING PERIOD REPORTS")
    print("="*50)
    reports_success = tester.test_period_reports()

    # Test 9: PDF export
    print("\n" + "="*50)
    print("🆕 TESTING PDF EXPORT")
    print("="*50)
    pdf_success = tester.test_pdf_export()

    # Test 10: Original functionality - More expenses
    print("\n📝 Testing additional expense functionality...")
    expense_id3 = tester.test_create_expense("Uber para trabalho", 15.00)
    expense_id4 = tester.test_create_expense("Compra de livros", 45.00, "Educação")

    # Test 11: Get all expenses
    expenses = tester.test_get_expenses()

    # Test 12: AI Insights (requires expenses)
    if expenses:
        print("\n🤖 Testing AI features...")
        ai_insights_success = tester.test_ai_insights()
        ai_predictions_success = tester.test_ai_predictions()

    # Print final results
    print("\n" + "=" * 80)
    print(f"📊 COMPREHENSIVE TEST RESULTS FOR REVOLUTIONARY FEATURES")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    # Detailed summary
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    # Check critical revolutionary features
    critical_features_passed = all([
        calendar_success,
        appointments_success,
        salary_success,
        dashboard_success
    ])
    
    if tester.tests_passed == tester.tests_run and critical_features_passed:
        print("🎉 ALL TESTS PASSED! REVOLUTIONARY FEATURES ARE WORKING!")
        print("\n✅ REVOLUTIONARY FEATURES VERIFIED:")
        print("   🌟 CALENDAR INTELLIGENCE - Daily spending calculations")
        print("   🌟 APPOINTMENTS AGENDA - Complete CRUD functionality")
        print("   • Salary management (PUT/GET /api/user/salary)")
        print("   • Installment expenses (POST/GET /api/installment-expenses)")
        print("   • Dashboard with balance calculation")
        print("   • Period reports (GET /api/reports/period)")
        print("   • PDF export (GET /api/reports/export-pdf)")
        print("\n🚀 READY FOR FRONTEND TESTING!")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} tests failed.")
        
        if not critical_features_passed:
            print("❌ CRITICAL REVOLUTIONARY FEATURES FAILED:")
            if not calendar_success:
                print("   ❌ Calendar Intelligence not working")
            if not appointments_success:
                print("   ❌ Appointments Agenda not working")
            if not salary_success:
                print("   ❌ Salary management not working")
            if not dashboard_success:
                print("   ❌ Dashboard balance calculation not working")
        
        print("🔧 Backend needs fixes before frontend testing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())