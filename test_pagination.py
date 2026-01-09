#!/usr/bin/env python3
"""
Script para probar la paginación
"""
import requests

BASE_URL = "http://localhost:8000/api"

def test_pagination(endpoint, name):
    """Probar paginación en un endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing Pagination: {name}")
    print(f"{'='*60}")
    
    try:
        # Página 1
        page1_resp = requests.get(f"{BASE_URL}/{endpoint}?page=1", timeout=5)
        if page1_resp.status_code != 200:
            print(f"✗ Failed to get page 1: {page1_resp.status_code}")
            return False
        
        page1_data = page1_resp.json()
        if 'results' not in page1_data:
            print(f"⚠ Endpoint does not use pagination (no 'results' key)")
            return True  # No es un error si no usa paginación
        
        count = page1_data.get('count', 0)
        results = page1_data.get('results', [])
        next_page = page1_data.get('next')
        previous_page = page1_data.get('previous')
        
        print(f"✓ Page 1 loaded")
        print(f"  Total items: {count}")
        print(f"  Items in page: {len(results)}")
        print(f"  Next page: {next_page is not None}")
        print(f"  Previous page: {previous_page is not None}")
        
        # Si hay más páginas, probar página 2
        if next_page:
            page2_resp = requests.get(next_page, timeout=5)
            if page2_resp.status_code == 200:
                page2_data = page2_resp.json()
                page2_results = page2_data.get('results', [])
                print(f"✓ Page 2 loaded")
                print(f"  Items in page 2: {len(page2_results)}")
                
                # Verificar que son diferentes
                if results and page2_results:
                    if results[0]['id'] != page2_results[0]['id']:
                        print(f"✓ Pages contain different items")
                    else:
                        print(f"⚠ Pages might contain same items")
            else:
                print(f"✗ Failed to load page 2: {page2_resp.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("PAGINATION TESTING")
    print("="*60)
    
    results = {
        'passed': 0,
        'failed': 0
    }
    
    # Test students pagination
    if test_pagination("students/students/", "Students"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test payments pagination
    if test_pagination("payments/payments/", "Payments"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test enrollments pagination
    if test_pagination("students/enrollments/", "Enrollments"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test documents pagination
    if test_pagination("students/documents/", "Documents"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test courses pagination
    if test_pagination("academics/courses/", "Courses"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Summary
    print("\n" + "="*60)
    print("PAGINATION TEST SUMMARY")
    print("="*60)
    print(f"Passed: {results['passed']} ✓")
    print(f"Failed: {results['failed']} ✗")
    print(f"Total: {results['passed'] + results['failed']}")
    print(f"Success rate: {(results['passed']/(results['passed']+results['failed'])*100):.1f}%")
    print("="*60 + "\n")
    
    return results['failed'] == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)




