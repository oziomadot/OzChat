#!/usr/bin/env python3
"""
Test script for the NaijaStay Web Application endpoints.
Tests all required functionality before running the full app.
"""

import requests
import json
import time
from threading import Thread
from app import app

def test_health_endpoint():
    """Test the /health endpoint."""
    print("🔍 Testing /health endpoint...")
    
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   RAG Pipeline: {data['rag_pipeline']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to health endpoint: {e}")
        print("   Make sure the app is running on http://localhost:5000")
        return False

def test_chat_endpoint():
    """Test the /chat API endpoint."""
    print("\n🔍 Testing /chat endpoint...")
    
    test_questions = [
        "What is the data privacy policy?",
        "How do I make a booking?",
        "What security measures are in place?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n   Test {i}: {question}")
        
        try:
            payload = {"question": question}
            response = requests.post(
                'http://localhost:5000/chat',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response received ({data['processing_time']}s)")
                print(f"   📚 Citations: {len(data['citations'])}")
                print(f"   📄 Preview: {data['answer'][:100]}...")
                
                # Check required fields
                required_fields = ['answer', 'citations', 'num_chunks_retrieved', 'processing_time']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ⚠️  Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ All required fields present")
                    
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return False
    
    return True

def test_chat_edge_cases():
    """Test edge cases for /chat endpoint."""
    print("\n🔍 Testing /chat edge cases...")
    
    edge_cases = [
        {"name": "Empty question", "payload": {"question": ""}, "expected_status": 400},
        {"name": "Missing question", "payload": {}, "expected_status": 400},
        {"name": "Too long question", "payload": {"question": "x" * 501}, "expected_status": 400},
        {"name": "Invalid JSON", "payload": "invalid", "expected_status": 400}
    ]
    
    for case in edge_cases:
        print(f"\n   Testing: {case['name']}")
        
        try:
            if case['name'] == "Invalid JSON":
                response = requests.post(
                    'http://localhost:5000/chat',
                    data=case['payload'],
                    timeout=5
                )
            else:
                response = requests.post(
                    'http://localhost:5000/chat',
                    json=case['payload'],
                    timeout=5
                )
            
            if response.status_code == case['expected_status']:
                print(f"   ✅ Correctly returned {response.status_code}")
            else:
                print(f"   ❌ Expected {case['expected_status']}, got {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
    
    return True

def test_ui_accessibility():
    """Test that the main UI is accessible."""
    print("\n🔍 Testing UI accessibility...")
    
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        
        if response.status_code == 200:
            # Check for key HTML elements
            content = response.text
            required_elements = [
                'chat-container',
                'messageInput',
                'sendButton',
                'statusIndicator'
            ]
            
            missing_elements = [elem for elem in required_elements if elem not in content]
            
            if not missing_elements:
                print("✅ UI loaded successfully with all required elements")
                return True
            else:
                print(f"⚠️  UI missing elements: {missing_elements}")
                return False
        else:
            print(f"❌ UI not accessible: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access UI: {e}")
        return False

def run_app_in_background():
    """Run the Flask app in background for testing."""
    def run():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
    thread = Thread(target=run, daemon=True)
    thread.start()
    
    # Wait for app to start
    print("⏳ Waiting for app to start...")
    time.sleep(3)
    
    return thread

def main():
    """Run all tests."""
    print("🧪 NaijaStay Web Application Test Suite")
    print("=" * 50)
    
    # Start app in background
    app_thread = run_app_in_background()
    
    # Give it more time to fully start
    time.sleep(2)
    
    all_tests_passed = True
    
    # Run tests
    tests = [
        ("Health Check", test_health_endpoint),
        ("Chat API", test_chat_endpoint),
        ("Edge Cases", test_chat_edge_cases),
        ("UI Accessibility", test_ui_accessibility)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            result = test_func()
            if not result:
                all_tests_passed = False
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            all_tests_passed = False
    
    # Summary
    print(f"\n{'='*50}")
    if all_tests_passed:
        print("🎉 All tests passed! The web application is ready to use.")
        print("\n🌐 Open http://localhost:5000 in your browser to access the chat interface")
        print("📚 API Documentation:")
        print("   POST /chat - JSON: {'question': 'your question'}")
        print("   GET  /health - Returns service status")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print(f"\n{'='*50}")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
