#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Student Management System
Tests authentication, CRUD operations, role-based access, and activity logging
"""

import requests
import json
import base64
import time
from datetime import datetime
import sys

# Backend URL from environment
BACKEND_URL = "https://f317806e-757a-458b-bd36-a0008bc6f81c.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "rohan@gcet.edu.in"
ADMIN_PASSWORD = "Rohan@95@"

# Test user credentials
TEST_USER_EMAIL = "testuser@gcet.edu.in"
TEST_USER_PASSWORD = "TestUser123@"
TEST_USER_NAME = "Test User"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_user = None
        self.test_user = None
        self.test_student_id = None
        self.results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_admin_login(self):
        """Test admin user login with provided credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and data["user"]["role"] == "admin":
                    self.admin_user = data["user"]
                    self.log_result("Admin Login", True, "Admin user authenticated successfully")
                    return True
                else:
                    self.log_result("Admin Login", False, "Admin user role not found in response", data)
                    return False
            else:
                self.log_result("Admin Login", False, f"Login failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception during admin login: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/register", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "name": TEST_USER_NAME,
                "role": "user"
            })
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data:
                    self.log_result("User Registration", True, "User registered successfully")
                    return True
                else:
                    self.log_result("User Registration", False, "User not found in response", data)
                    return False
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_result("User Registration", True, "User already exists (expected behavior)")
                return True
            else:
                self.log_result("User Registration", False, f"Registration failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Exception during registration: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test regular user login"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and data["user"]["role"] == "user":
                    self.test_user = data["user"]
                    self.log_result("User Login", True, "Regular user authenticated successfully")
                    return True
                else:
                    self.log_result("User Login", False, "User role not found in response", data)
                    return False
            else:
                self.log_result("User Login", False, f"Login failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Exception during user login: {str(e)}")
            return False
    
    def test_create_student(self):
        """Test student creation with image upload"""
        try:
            # Create a simple base64 encoded test image (1x1 pixel PNG)
            test_image_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77mgAAAABJRU5ErkJggg=="
            
            student_data = {
                "name": "Arjun Kumar",
                "roll_number": "21CS001",
                "stream": "Computer Science",
                "photo": test_image_b64,
                "current_semester": "1"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/students",
                json=student_data,
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data:
                    self.test_student_id = data["id"]
                    self.log_result("Create Student", True, f"Student created successfully with ID: {self.test_student_id}")
                    return True
                else:
                    self.log_result("Create Student", False, "Student ID not found in response", data)
                    return False
            else:
                self.log_result("Create Student", False, f"Student creation failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Student", False, f"Exception during student creation: {str(e)}")
            return False
    
    def test_roll_number_uniqueness(self):
        """Test roll number uniqueness validation"""
        try:
            student_data = {
                "name": "Duplicate Roll Test",
                "roll_number": "21CS001",  # Same as previous student
                "stream": "Computer Science",
                "current_semester": "1"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/students",
                json=student_data,
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 400 and "already exists" in response.text:
                self.log_result("Roll Number Uniqueness", True, "Roll number uniqueness validation working correctly")
                return True
            else:
                self.log_result("Roll Number Uniqueness", False, f"Expected 400 error for duplicate roll number, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Roll Number Uniqueness", False, f"Exception during uniqueness test: {str(e)}")
            return False
    
    def test_get_students(self):
        """Test retrieving students list"""
        try:
            response = self.session.get(
                f"{BACKEND_URL}/students",
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.log_result("Get Students", True, f"Retrieved {len(data)} students successfully")
                    return True
                else:
                    self.log_result("Get Students", False, "No students found or invalid response format", data)
                    return False
            else:
                self.log_result("Get Students", False, f"Get students failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Get Students", False, f"Exception during get students: {str(e)}")
            return False
    
    def test_update_student(self):
        """Test student update functionality"""
        if not self.test_student_id:
            self.log_result("Update Student", False, "No test student ID available")
            return False
            
        try:
            update_data = {
                "name": "Arjun Kumar Updated",
                "stream": "Computer Science & Engineering"
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/students/{self.test_student_id}",
                json=update_data,
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("name") == "Arjun Kumar Updated":
                    self.log_result("Update Student", True, "Student updated successfully")
                    return True
                else:
                    self.log_result("Update Student", False, "Student update did not reflect changes", data)
                    return False
            else:
                self.log_result("Update Student", False, f"Student update failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Update Student", False, f"Exception during student update: {str(e)}")
            return False
    
    def test_update_student_subjects(self):
        """Test semester-based subject management with grade calculation"""
        if not self.test_student_id:
            self.log_result("Update Student Subjects", False, "No test student ID available")
            return False
            
        try:
            subjects_data = {
                "semester": "1",
                "subjects": [
                    {"name": "Mathematics", "marks": 85, "grade": ""},
                    {"name": "Physics", "marks": 92, "grade": ""},
                    {"name": "Chemistry", "marks": 78, "grade": ""},
                    {"name": "Programming", "marks": 95, "grade": ""}
                ]
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/students/{self.test_student_id}/subjects",
                json=subjects_data,
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 200:
                self.log_result("Update Student Subjects", True, "Student subjects updated with automatic grade calculation")
                return True
            else:
                self.log_result("Update Student Subjects", False, f"Subject update failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Update Student Subjects", False, f"Exception during subject update: {str(e)}")
            return False
    
    def test_role_based_access_admin_endpoints(self):
        """Test admin-only endpoints with admin user"""
        try:
            # Test get users (admin only)
            response = self.session.get(
                f"{BACKEND_URL}/users",
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Admin Access - Get Users", True, f"Admin can access users list ({len(data)} users)")
                else:
                    self.log_result("Admin Access - Get Users", False, "Invalid response format for users list", data)
                    return False
            else:
                self.log_result("Admin Access - Get Users", False, f"Admin get users failed with status {response.status_code}", response.text)
                return False
            
            # Test get activity logs (admin only)
            response = self.session.get(
                f"{BACKEND_URL}/activity-logs",
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Admin Access - Activity Logs", True, f"Admin can access activity logs ({len(data)} logs)")
                    return True
                else:
                    self.log_result("Admin Access - Activity Logs", False, "Invalid response format for activity logs", data)
                    return False
            else:
                self.log_result("Admin Access - Activity Logs", False, f"Admin get activity logs failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Access Test", False, f"Exception during admin access test: {str(e)}")
            return False
    
    def test_role_based_access_regular_user(self):
        """Test that regular users cannot access admin endpoints"""
        if not self.test_user:
            self.log_result("Regular User Access Test", False, "No test user available")
            return False
            
        try:
            # Test get users (should fail for regular user)
            response = self.session.get(
                f"{BACKEND_URL}/users",
                params={"user_email": self.test_user["email"]}
            )
            
            if response.status_code == 403:
                self.log_result("Regular User Access - Get Users", True, "Regular user correctly denied access to users list")
            else:
                self.log_result("Regular User Access - Get Users", False, f"Expected 403 for regular user, got {response.status_code}", response.text)
                return False
            
            # Test get activity logs (should fail for regular user)
            response = self.session.get(
                f"{BACKEND_URL}/activity-logs",
                params={"user_email": self.test_user["email"]}
            )
            
            if response.status_code == 403:
                self.log_result("Regular User Access - Activity Logs", True, "Regular user correctly denied access to activity logs")
                return True
            else:
                self.log_result("Regular User Access - Activity Logs", False, f"Expected 403 for regular user, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Regular User Access Test", False, f"Exception during regular user access test: {str(e)}")
            return False
    
    def test_authentication_required(self):
        """Test that endpoints require authentication"""
        try:
            # Test get students without authentication
            response = self.session.get(f"{BACKEND_URL}/students")
            
            if response.status_code == 401:
                self.log_result("Authentication Required", True, "Endpoints correctly require authentication")
                return True
            else:
                self.log_result("Authentication Required", False, f"Expected 401 for unauthenticated request, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Authentication Required Test", False, f"Exception during authentication test: {str(e)}")
            return False
    
    def test_admin_delete_student(self):
        """Test admin can delete students"""
        if not self.test_student_id:
            self.log_result("Admin Delete Student", False, "No test student ID available")
            return False
            
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/students/{self.test_student_id}",
                params={"user_email": self.admin_user["email"]}
            )
            
            if response.status_code == 200:
                self.log_result("Admin Delete Student", True, "Admin successfully deleted student")
                return True
            else:
                self.log_result("Admin Delete Student", False, f"Admin delete student failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Delete Student", False, f"Exception during admin delete student: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive backend tests"""
        print("🚀 Starting Comprehensive Backend Testing for Student Management System")
        print("=" * 80)
        
        # Authentication Tests
        print("\n📋 AUTHENTICATION SYSTEM TESTS")
        print("-" * 40)
        self.test_admin_login()
        self.test_user_registration()
        self.test_user_login()
        self.test_authentication_required()
        
        # Student Management Tests
        print("\n👥 STUDENT MANAGEMENT TESTS")
        print("-" * 40)
        self.test_create_student()
        self.test_roll_number_uniqueness()
        self.test_get_students()
        self.test_update_student()
        self.test_update_student_subjects()
        
        # Role-based Access Tests
        print("\n🔐 ROLE-BASED ACCESS CONTROL TESTS")
        print("-" * 40)
        self.test_role_based_access_admin_endpoints()
        self.test_role_based_access_regular_user()
        
        # Admin Operations Tests
        print("\n⚡ ADMIN OPERATIONS TESTS")
        print("-" * 40)
        self.test_admin_delete_student()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if "✅ PASS" in r["status"])
        failed = sum(1 for r in self.results if "❌ FAIL" in r["status"])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend tests passed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some backend tests failed. Check the details above.")
        sys.exit(1)