#!/usr/bin/env python3
"""
Phase 1 Testing Script
Tests all Phase 1 functionality locally before cloud deployment.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8001"


async def test_health_endpoint():
    """Test health check endpoint."""
    print("🔍 Testing health endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Dependencies: {data['dependencies']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False


async def test_chat_endpoint():
    """Test chat endpoint with sample message."""
    print("\n💬 Testing chat endpoint...")
    
    test_message = {
        "message": "Hello! I'm a coffee farmer in Kenya. Can you help me?",
        "user_id": "test_farmer_123",
        "session_id": "test_session_456"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat",
                json=test_message
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Chat endpoint working!")
                print(f"   Response: {data['response'][:100]}...")
                print(f"   Model: {data['model_used']}")
                print(f"   Tokens: {data['tokens_used']}")
                return True
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat endpoint error: {str(e)}")
            return False


async def test_info_endpoint():
    """Test service info endpoint."""
    print("\n📋 Testing info endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/info")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Info endpoint working!")
                print(f"   App: {data['app_name']} v{data['version']}")
                print(f"   Features: {data['features']}")
                return True
            else:
                print(f"❌ Info endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Info endpoint error: {str(e)}")
            return False


async def test_error_handling():
    """Test error handling with invalid requests."""
    print("\n🚨 Testing error handling...")
    
    # Test invalid message (empty)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat",
                json={"message": ""}
            )
            
            if response.status_code == 422:
                print("✅ Input validation working (empty message rejected)")
                return True
            else:
                print(f"❌ Input validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test failed: {str(e)}")
            return False


async def run_phase1_tests():
    """Run all Phase 1 tests."""
    print("🚀 Starting Phase 1 Tests for Gukas AI Agent")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Service Info", test_info_endpoint),
        ("Error Handling", test_error_handling),
        ("Chat Functionality", test_chat_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Phase 1 Test Results:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 Phase 1 is ready for cloud deployment!")
        return True
    else:
        print("⚠️  Fix failing tests before deployment")
        return False


if __name__ == "__main__":
    print("Make sure the server is running: python main.py")
    print("Then run this test script in another terminal\n")
    
    try:
        result = asyncio.run(run_phase1_tests())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        exit(1)