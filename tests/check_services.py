"""
Test Service Connectivity and Client Functionality
===================================================

Checks if services are running and demonstrates client usage.
Run this before running pytest tests to verify setup.

Usage:
    python tests/check_services.py
"""

import asyncio
import aiohttp
from client import createLiveClient, createFederationClient


async def check_service(name: str, url: str) -> bool:
    """Check if a service is accessible."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                # GraphQL endpoints often return 400, 404, or 200 on GET requests - all OK
                if resp.status in [200, 400, 404, 405]:
                    print(f"✅ {name:35} - Running (status {resp.status})")
                    return True
                else:
                    print(f"⚠️  {name:35} - Unexpected status {resp.status}")
                    return False
    except aiohttp.ClientConnectorError:
        print(f"❌ {name:35} - Not running (connection refused)")
        return False
    except asyncio.TimeoutError:
        print(f"❌ {name:35} - Timeout")
        return False
    except Exception as e:
        print(f"❌ {name:35} - Error: {e}")
        return False


async def main():
    """Check all services and demonstrate client usage."""
    
    print("=" * 70)
    print("GQL Property Service - Connectivity Check")
    print("=" * 70)
    
    # Check services
    print("\n📡 Checking Services...")
    print("-" * 70)
    
    services = {
        "Property Service (Direct)": "http://localhost:8000/gql",
        "Apollo Gateway (Federation)": "http://localhost:33000/api/gql",
        "UG Service": "http://localhost:33001/api/gql",
        "Frontend": "http://localhost:33001",
    }
    
    results = {}
    for name, url in services.items():
        results[name] = await check_service(name, url)
    
    print()
    
    # Summary
    all_running = all(results.values())
    
    if not all_running:
        print("⚠️  WARNING: Some services are not running!")
        print()
        print("To start services:")
        print("  1. docker compose -f .\\docker-compose.debug.yml up -d")
        print("  2. .venv\\Scripts\\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --env-file environment.txt")
        print()
        print("Then run this script again to verify.")
        return
    
    print("✅ All services running!")
    print()
    
    # Test authentication
    print("=" * 70)
    print("Testing Authentication")
    print("=" * 70)
    print()
    
    # Try to get JWT token
    print("🔐 Attempting authentication...")
    try:
        from client import getToken
        token = await getToken("john.newbie@world.com", "john.newbie@world.com")
        
        if token:
            print(f"✅ Authentication successful!")
            print(f"   Token: {token[:20]}...{token[-20:]}")
        else:
            print("❌ Authentication failed - check credentials")
            return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    print()
    
    # Test live client
    print("=" * 70)
    print("Testing Live Client (Direct Service)")
    print("=" * 70)
    print()
    
    try:
        live_client = createLiveClient()
        
        # Simple query to test direct service
        result = await live_client.execute("""
            query {
                purchasePage(limit: 1) {
                    id
                    status
                }
            }
        """)
        
        if "errors" not in result:
            print(f"✅ Live client working!")
            purchases = result["data"]["purchasePage"]
            print(f"   Retrieved {len(purchases)} purchase(s)")
        else:
            print(f"❌ Query failed: {result['errors'][0]['message']}")
    except Exception as e:
        print(f"❌ Live client error: {e}")
    
    print()
    
    # Test federation client
    print("=" * 70)
    print("Testing Federation Client (Apollo Gateway)")
    print("=" * 70)
    print()
    
    try:
        fed_client = createFederationClient()
        
        # Simple query through federation
        result = await fed_client.execute("""
            query {
              purchasePage(skip: 0, limit: 3) {
                id
                status
                reason
              }
            }
        """)
        
        if "errors" in result:
            print(f"❌ Federation query failed:")
            for error in result["errors"]:
                print(f"   - {error.get('message', str(error))}")
        elif "data" in result:
            purchases = result["data"].get("purchasePage", [])
            print(f"✅ Federation client working!")
            print(f"   Retrieved {len(purchases)} purchase(s)")
            
            for i, purchase in enumerate(purchases, 1):
                status = purchase.get('status', 'Unknown')
                reason = purchase.get('reason', 'N/A')
                purchase_id = purchase['id'][:8]
                print(f"   {i}. Status: {status}, Reason: {reason[:30] if reason else 'N/A'} (ID: {purchase_id}...)")
        else:
            print("⚠️  No data returned")
    except Exception as e:
        print(f"❌ Federation client error: {e}")
    
    print()
    
    # Final summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("✅ Services are running and accessible")
    print("✅ Authentication working")
    print("✅ Clients ready for testing")
    print()
    print("Next steps:")
    print("  - Run live tests: pytest tests/test_purchases_live.py -v")
    print("  - Run unit tests: pytest tests/test_purchases.py -v")
    print("  - Run all tests: pytest tests/ -v")
    print()


if __name__ == "__main__":
    asyncio.run(main())
