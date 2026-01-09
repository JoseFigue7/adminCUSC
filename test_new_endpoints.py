#!/usr/bin/env python3
"""
Script para probar los nuevos endpoints implementados
"""
import requests
import json
import os
from io import BytesIO
from PIL import Image

BASE_URL = "http://localhost:8000/api"

def test_payment_creation():
    """Probar creación de pago"""
    print("\n" + "="*60)
    print("TESTING: Payment Creation")
    print("="*60)
    
    # Primero obtener un estudiante
    try:
        students_resp = requests.get(f"{BASE_URL}/students/students/?page=1", timeout=5)
        if students_resp.status_code != 200:
            print("✗ Could not get students")
            return False
        
        students_data = students_resp.json()
        students = students_data.get('results', students_data if isinstance(students_data, list) else [])
        if not students:
            print("✗ No students found")
            return False
        
        student_id = students[0]['id']
        print(f"Using student: {student_id}")
        
        # Crear un pago de prueba
        payment_data = {
            'student': student_id,
            'payment_method': 'EFECTIVO',
            'amount': '500.00',
            'month': 1,
            'year': 2024,
            'receipt_number': f'TEST-{os.urandom(4).hex()}'
        }
        
        print(f"Creating payment: {json.dumps(payment_data, indent=2)}")
        response = requests.post(
            f"{BASE_URL}/payments/payments/",
            json=payment_data,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            payment = response.json()
            print(f"✓ Payment created successfully")
            print(f"  Payment ID: {payment.get('id')}")
            print(f"  Status: {payment.get('status')}")
            return payment.get('id')
        else:
            print(f"✗ Failed to create payment")
            try:
                error = response.json()
                print(f"  Error: {json.dumps(error, indent=2)}")
            except:
                print(f"  Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return None

def test_receipt_upload(payment_id):
    """Probar subida de comprobante"""
    print("\n" + "="*60)
    print("TESTING: Receipt Upload")
    print("="*60)
    
    if not payment_id:
        print("✗ No payment ID provided")
        return False
    
    # Primero necesitamos un pago de tipo TRANSFERENCIA
    # Crear un pago de transferencia
    try:
        students_resp = requests.get(f"{BASE_URL}/students/students/?page=1", timeout=5)
        students_data = students_resp.json()
        students = students_data.get('results', students_data if isinstance(students_data, list) else [])
        student_id = students[0]['id']
        
        payment_data = {
            'student': student_id,
            'payment_method': 'TRANSFERENCIA',
            'amount': '750.00',
            'month': 2,
            'year': 2024
        }
        
        print(f"Creating transfer payment...")
        create_resp = requests.post(
            f"{BASE_URL}/payments/payments/",
            json=payment_data,
            timeout=10
        )
        
        if create_resp.status_code not in [200, 201]:
            print(f"✗ Could not create transfer payment: {create_resp.status_code}")
            return False
        
        transfer_payment = create_resp.json()
        transfer_payment_id = transfer_payment.get('id')
        print(f"✓ Transfer payment created: {transfer_payment_id}")
        
        # Crear un archivo de prueba (imagen dummy)
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Subir el comprobante
        print(f"Uploading receipt to payment {transfer_payment_id}...")
        files = {'file': ('test_receipt.png', img_bytes, 'image/png')}
        
        upload_resp = requests.post(
            f"{BASE_URL}/payments/payments/{transfer_payment_id}/upload_receipt/",
            files=files,
            timeout=10
        )
        
        print(f"Status: {upload_resp.status_code}")
        if upload_resp.status_code == 200:
            result = upload_resp.json()
            print(f"✓ Receipt uploaded successfully")
            print(f"  Transfer receipt: {result.get('transfer_receipt', 'N/A')}")
            print(f"  Status: {result.get('status')}")
            return True
        else:
            print(f"✗ Failed to upload receipt")
            try:
                error = upload_resp.json()
                print(f"  Error: {json.dumps(error, indent=2)}")
            except:
                print(f"  Error: {upload_resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_payment_approval():
    """Probar aprobación de pago"""
    print("\n" + "="*60)
    print("TESTING: Payment Approval")
    print("="*60)
    
    try:
        # Obtener un pago pendiente
        payments_resp = requests.get(f"{BASE_URL}/payments/payments/?page=1", timeout=5)
        if payments_resp.status_code != 200:
            print("✗ Could not get payments")
            return False
        
        payments_data = payments_resp.json()
        payments = payments_data.get('results', payments_data if isinstance(payments_data, list) else [])
        
        # Buscar un pago pendiente
        pending_payment = None
        for payment in payments:
            if payment.get('status') in ['PENDIENTE', 'EN_REVISION']:
                pending_payment = payment
                break
        
        if not pending_payment:
            print("⚠ No pending payments found, creating one...")
            # Crear un pago pendiente
            students_resp = requests.get(f"{BASE_URL}/students/students/?page=1", timeout=5)
            students_data = students_resp.json()
            students = students_data.get('results', students_data if isinstance(students_data, list) else [])
            student_id = students[0]['id']
            
            payment_data = {
                'student': student_id,
                'payment_method': 'TARJETA',
                'amount': '600.00',
                'month': 3,
                'year': 2024,
                'card_last_four': '1234',
                'transaction_id': f'TXN-{os.urandom(4).hex()}'
            }
            
            create_resp = requests.post(
                f"{BASE_URL}/payments/payments/",
                json=payment_data,
                timeout=10
            )
            
            if create_resp.status_code in [200, 201]:
                pending_payment = create_resp.json()
            else:
                print("✗ Could not create test payment")
                return False
        
        payment_id = pending_payment['id']
        print(f"Approving payment: {payment_id}")
        
        approve_resp = requests.patch(
            f"{BASE_URL}/payments/payments/{payment_id}/approve/",
            json={},
            timeout=10
        )
        
        print(f"Status: {approve_resp.status_code}")
        if approve_resp.status_code == 200:
            result = approve_resp.json()
            print(f"✓ Payment approved successfully")
            print(f"  Status: {result.get('status')}")
            return True
        else:
            print(f"✗ Failed to approve payment")
            try:
                error = approve_resp.json()
                print(f"  Error: {json.dumps(error, indent=2)}")
            except:
                print(f"  Error: {approve_resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_payment_rejection():
    """Probar rechazo de pago"""
    print("\n" + "="*60)
    print("TESTING: Payment Rejection")
    print("="*60)
    
    try:
        # Crear un pago pendiente
        students_resp = requests.get(f"{BASE_URL}/students/students/?page=1", timeout=5)
        students_data = students_resp.json()
        students = students_data.get('results', students_data if isinstance(students_data, list) else [])
        student_id = students[0]['id']
        
        payment_data = {
            'student': student_id,
            'payment_method': 'EFECTIVO',
            'amount': '400.00',
            'month': 4,
            'year': 2024,
            'receipt_number': f'REJECT-TEST-{os.urandom(4).hex()}'
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/payments/payments/",
            json=payment_data,
            timeout=10
        )
        
        if create_resp.status_code not in [200, 201]:
            print("✗ Could not create test payment")
            return False
        
        payment = create_resp.json()
        payment_id = payment['id']
        print(f"Rejecting payment: {payment_id}")
        
        reject_data = {
            'notes': 'Pago de prueba rechazado - motivo de prueba'
        }
        
        reject_resp = requests.patch(
            f"{BASE_URL}/payments/payments/{payment_id}/reject/",
            json=reject_data,
            timeout=10
        )
        
        print(f"Status: {reject_resp.status_code}")
        if reject_resp.status_code == 200:
            result = reject_resp.json()
            print(f"✓ Payment rejected successfully")
            print(f"  Status: {result.get('status')}")
            print(f"  Notes: {result.get('notes', 'N/A')}")
            return True
        else:
            print(f"✗ Failed to reject payment")
            try:
                error = reject_resp.json()
                print(f"  Error: {json.dumps(error, indent=2)}")
            except:
                print(f"  Error: {reject_resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("TESTING NEW ENDPOINTS")
    print("="*60)
    
    results = {
        'passed': 0,
        'failed': 0
    }
    
    # Test payment creation
    payment_id = test_payment_creation()
    if payment_id:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test receipt upload
    if test_receipt_upload(payment_id):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test payment approval
    if test_payment_approval():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test payment rejection
    if test_payment_rejection():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Summary
    print("\n" + "="*60)
    print("NEW ENDPOINTS TEST SUMMARY")
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




