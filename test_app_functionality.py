#!/usr/bin/env python3
"""
Comprehensive test script to verify FastAPI app functionality
"""
import sys
import os
sys.path.append('.')

def test_app_import():
    """Test that the FastAPI app can be imported successfully"""
    try:
        from app import app
        print('✅ FastAPI app imported successfully')
        
        print(f'✅ App title: {app.title}')
        print(f'✅ App version: {app.version}')
        
        routes = [route.path for route in app.routes]
        print(f'✅ Found {len(routes)} routes')
        
        return True
    except Exception as e:
        print(f'❌ App import failed: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test that all required dependencies can be imported"""
    dependencies = [
        'boto3',
        'fastapi',
        'uvicorn',
        'psycopg2',
        'sqlparse',
        'markdown',
        'jinja2',
        'anthropic',
        'numpy',
        'pandas'
    ]
    
    failed_imports = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f'✅ {dep} imported successfully')
        except ImportError as e:
            print(f'❌ {dep} import failed: {e}')
            failed_imports.append(dep)
    
    return len(failed_imports) == 0

def test_fastapi_endpoints():
    """Test FastAPI endpoints with mock client"""
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        response = client.get('/health')
        if response.status_code == 200:
            print('✅ Health endpoint test passed')
        else:
            print(f'❌ Health endpoint failed with status {response.status_code}')
            return False
        
        response = client.post('/query', json={'query_text': 'test'})
        if response.status_code != 404:
            print('✅ Query endpoint structure test passed')
        else:
            print('❌ Query endpoint not found')
            return False
        
        return True
    except Exception as e:
        print(f'❌ FastAPI endpoint test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Starting comprehensive app functionality tests...\n")
    
    tests = [
        ("App Import", test_app_import),
        ("Dependencies", test_dependencies),
        ("FastAPI Endpoints", test_fastapi_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- Running {test_name} Test ---")
        result = test_func()
        results.append((test_name, result))
        print(f"--- {test_name} Test {'PASSED' if result else 'FAILED'} ---\n")
    
    print("=== Test Summary ===")
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
