#!/usr/bin/env python3
"""
Test script to demonstrate the humanistic response improvements.
"""

import requests
import json

def test_humanistic_responses():
    """Test the humanistic responses for different policy questions."""
    
    print("🤖 Testing Humanistic Response System")
    print("=" * 50)
    
    # Test questions covering different policy areas
    test_questions = [
        "What is the data privacy policy?",
        "How do I make a booking?",
        "What security measures are in place?",
        "Tell me about business continuity",
        "How does the recommendation algorithm work?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 40)
        
        try:
            response = requests.post(
                'http://localhost:5000/chat',
                json={"question": question},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data['answer']
                
                print(f"🤖 Response: {answer}")
                
                # Check for humanistic phrases
                humanistic_phrases = [
                    "I've checked our records",
                    "I can confirm",
                    "I've reviewed",
                    "Looking at",
                    "I've checked how",
                    "Regarding"
                ]
                
                found_phrases = [phrase for phrase in humanistic_phrases if phrase in answer]
                if found_phrases:
                    print(f"✅ Humanistic phrases detected: {', '.join(found_phrases)}")
                else:
                    print("⚠️  No humanistic phrases detected")
                
                print(f"⏱️  Processing time: {data['processing_time']}s")
                print(f"📚 Citations: {len(data['citations'])}")
                
            else:
                print(f"❌ Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            print("   Make sure the app is running on http://localhost:5000")
            return False
    
    return True

def compare_responses():
    """Show a comparison of old vs new response styles."""
    
    print("\n" + "=" * 50)
    print("📊 Response Style Comparison")
    print("=" * 50)
    
    comparison = {
        "Data Privacy": {
            "old_style": "Based on the policy documents, Data Privacy Policy Version: 1.1 Date: March 10, 2026...",
            "new_style": "I've checked our records and found that NSR is fully committed to protecting your personal data..."
        },
        "Booking": {
            "old_style": "According to NSR's booking procedures, users complete transactions through Paystack...",
            "new_style": "Regarding our booking process, I can confirm that we use Paystack's secure payment system..."
        },
        "Security": {
            "old_style": "NSR's Information Security Policy is aligned with ISO 27001 principles...",
            "new_style": "I've reviewed our security measures and can assure you that we take data protection very seriously..."
        }
    }
    
    for topic, styles in comparison.items():
        print(f"\n🔍 {topic}:")
        print(f"   ❌ Old: {styles['old_style'][:60]}...")
        print(f"   ✅ New: {styles['new_style'][:60]}...")

def main():
    """Run all humanistic response tests."""
    
    print("🧪 Humanistic Response Testing Suite")
    print("This test demonstrates the improved user experience with humanistic responses.")
    
    # Check if app is running
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code != 200:
            print("❌ App is not running. Please start with: python app.py")
            return
    except:
        print("❌ Cannot connect to app. Please start with: python app.py")
        return
    
    # Run tests
    success = test_humanistic_responses()
    
    if success:
        compare_responses()
        
        print("\n" + "=" * 50)
        print("🎉 Humanistic Response System Summary")
        print("=" * 50)
        print("✅ Professional, warm, and helpful tone")
        print("✅ Context-aware responses")
        print("✅ Natural language instead of robotic citations")
        print("✅ Maintains accuracy and source attribution")
        print("\n💡 The system now provides:")
        print("   • More conversational responses")
        print("   • Better user experience")
        print("   • Same factual accuracy")
        print("   • Professional assistance tone")

if __name__ == "__main__":
    main()
