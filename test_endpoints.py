#!/usr/bin/env python3
"""
Script para probar todos los endpoints del sistema
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_endpoint(method, url, data=None, files=None, description=""):
    """Prueba un endpoint y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    print(f"{method.upper()} {url}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=5)
        elif method.upper() == 'POST':
            if files:
                response = requests.post(url, data=data, files=files, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code < 400:
            try:
                result = response.json()
                if isinstance(result, dict):
                    if 'results' in result:
                        print(f"✓ Success - {len(result.get('results', []))} items returned")
                        print(f"  Total count: {result.get('count', 'N/A')}")
                    else:
                        print(f"✓ Success - Response received")
                        if 'id' in result:
                            print(f"  ID: {result['id']}")
                elif isinstance(result, list):
                    print(f"✓ Success - {len(result)} items returned")
                else:
                    print(f"✓ Success - Response received")
            except:
                print(f"✓ Success - Non-JSON response (size: {len(response.content)} bytes)")
        else:
            print(f"✗ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"  Error text: {response.text[:200]}")
        
        return response.status_code < 400
        
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection Error - Is the server running?")
        return False
    except requests.exceptions.Timeout:
        print(f"✗ Timeout - Request took too long")
        return False
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("ADMINCUSC - ENDPOINT TESTING")
    print("="*60)
    
    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # ===== STUDENTS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("STUDENTS ENDPOINTS")
    print("="*60)
    
    # List students (paginated)
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/students/students/?page=1", 
                     description="List students (paginated)"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Get first student if exists
    try:
        students_resp = requests.get(f"{BASE_URL}/students/students/?page=1", timeout=5)
        if students_resp.status_code == 200:
            students_data = students_resp.json()
            students = students_data.get('results', students_data if isinstance(students_data, list) else [])
            if students:
                student_id = students[0]['id']
                
                results['total'] += 1
                if test_endpoint('GET', f"{BASE_URL}/students/students/{student_id}/",
                               description=f"Get student by ID ({student_id})"):
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                
                results['total'] += 1
                if test_endpoint('GET', f"{BASE_URL}/students/students/{student_id}/progress/",
                               description=f"Get student progress ({student_id})"):
                    results['passed'] += 1
                else:
                    results['failed'] += 1
    except:
        print("  ⚠ Could not test student detail endpoints (no students found)")
    
    # ===== ENROLLMENTS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("ENROLLMENTS ENDPOINTS")
    print("="*60)
    
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/students/enrollments/",
                     description="List enrollments"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # ===== DOCUMENTS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("STUDENT DOCUMENTS ENDPOINTS")
    print("="*60)
    
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/students/documents/",
                     description="List student documents"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # ===== CAREERS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("CAREERS ENDPOINTS")
    print("="*60)
    
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/academics/careers/",
                     description="List careers"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Get first career if exists
    try:
        careers_resp = requests.get(f"{BASE_URL}/academics/careers/", timeout=5)
        if careers_resp.status_code == 200:
            careers_data = careers_resp.json()
            careers = careers_data.get('results', careers_data if isinstance(careers_data, list) else [])
            if careers:
                career_id = careers[0]['id']
                
                results['total'] += 1
                if test_endpoint('GET', f"{BASE_URL}/academics/careers/{career_id}/pensum/",
                               description=f"Get career pensum ({career_id})"):
                    results['passed'] += 1
                else:
                    results['failed'] += 1
    except:
        print("  ⚠ Could not test career pensum endpoint (no careers found)")
    
    # ===== COURSES ENDPOINTS =====
    print("\n\n" + "="*60)
    print("COURSES ENDPOINTS")
    print("="*60)
    
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/academics/courses/",
                     description="List courses"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # ===== ENROLLMENTS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("COURSE ENROLLMENTS ENDPOINTS")
    print("="*60)
    
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/academics/enrollments/",
                     description="List course enrollments"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # ===== PAYMENTS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("PAYMENTS ENDPOINTS")
    print("="*60)
    
    # List payments (paginated)
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/payments/payments/?page=1",
                     description="List payments (paginated)"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Get payment status
    try:
        payments_resp = requests.get(f"{BASE_URL}/payments/payments/?page=1", timeout=5)
        if payments_resp.status_code == 200:
            payments_data = payments_resp.json()
            payments = payments_data.get('results', payments_data if isinstance(payments_data, list) else [])
            if payments:
                payment_id = payments[0]['id']
                student_id = payments[0].get('student', '')
                
                if student_id:
                    results['total'] += 1
                    if test_endpoint('GET', f"{BASE_URL}/payments/payments/student_status/?student_id={student_id}",
                                   description=f"Get student payment status ({student_id})"):
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
    except:
        print("  ⚠ Could not test payment status endpoint (no payments found)")
    
    # ===== SCHOLARSHIPS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("SCHOLARSHIPS ENDPOINTS")
    print("="*60)
    
    results['total'] += 1
    if test_endpoint('GET', f"{BASE_URL}/payments/scholarships/",
                     description="List scholarships"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # ===== THESIS ENDPOINTS =====
    print("\n\n" + "="*60)
    print("THESIS ENDPOINTS")
    print("="*60)
    
    try:
        students_resp = requests.get(f"{BASE_URL}/students/students/?page=1", timeout=5)
        if students_resp.status_code == 200:
            students_data = students_resp.json()
            students = students_data.get('results', students_data if isinstance(students_data, list) else [])
            if students:
                student_id = students[0]['id']
                
                results['total'] += 1
                if test_endpoint('GET', f"{BASE_URL}/academics/thesis/by_student/?student_id={student_id}",
                               description=f"Get thesis by student ({student_id})"):
                    results['passed'] += 1
                else:
                    results['failed'] += 1
    except:
        print("  ⚠ Could not test thesis endpoint (no students found)")
    
    # ===== SUMMARY =====
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']} ✓")
    print(f"Failed: {results['failed']} ✗")
    print(f"Success rate: {(results['passed']/results['total']*100):.1f}%")
    print("="*60 + "\n")
    
    return results['failed'] == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)



