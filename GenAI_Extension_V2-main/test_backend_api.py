"""
Script to test if Backend API is running and accessible
"""
import httpx
import asyncio
import json

BACKEND_API_URL = "http://localhost:7071/api/analyze"

async def test_backend_api():
    """Test if backend API is accessible"""
    print("="*80)
    print("🔍 TESTING BACKEND API CONNECTION")
    print("="*80)
    print(f"Endpoint: {BACKEND_API_URL}\n")
    
    # Sample payload
    test_payload = {
        "request_meta": {
            "request_id": "test_123",
            "timestamp": "2026-02-03T10:00:00Z",
            "mode_type": "Analyze Report"
        },
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        },
        "filters": {
            "project_identifier": ["TEST_PROJECT"]
        },
        "metrics_data": [
            {"date": "2024-01-01", "TestCaseActual": 100}
        ]
    }
    
    try:
        print("📤 Sending test request...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                BACKEND_API_URL,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"✅ Response Status: {response.status_code}")
            print(f"✅ Response:\n{json.dumps(response.json(), indent=2)}")
            print("\n" + "="*80)
            print("✅ BACKEND API IS RUNNING AND ACCESSIBLE!")
            print("="*80)
            
    except httpx.ConnectError:
        print("❌ Connection Failed!")
        print("   Cannot connect to Backend API at port 7071")
        print("\n" + "="*80)
        print("⚠️ BACKEND API IS NOT RUNNING")
        print("="*80)
        print("\n💡 Solutions:")
        print("   1. Start Backend API on port 7071")
        print("   2. Or set DEBUG_MODE = True in server.py to skip Backend API call")
        
    except httpx.TimeoutException:
        print("❌ Timeout!")
        print("   Backend API took too long to respond")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}")
        print(f"   {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_backend_api())
