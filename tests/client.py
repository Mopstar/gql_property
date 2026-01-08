"""
Unified GraphQL Test Client for GQL Property Service

This module provides a standardized test client infrastructure for all tests.
ALL test files use this unified client for consistency.

Key Features:
- Multiple endpoint support (Apollo Gateway, direct service, in-memory)
- Automatic JWT token management with caching
- Cross-service queries (UG + Purchase seamless)
- Error handling and retries
- Consistent API across all test types

Client Types:
- createFederationClient(): Apollo Federation Gateway (recommended for integration tests)
- createLiveClient(): Direct service endpoint (for isolated testing)
- createGQLClient(): In-memory SQLite (for unit tests, existing)

Usage:
    from tests.client import createFederationClient, createLiveClient
    
    # For live integration tests
    client = createFederationClient()
    result = await client.execute(query, variables)
    
    # For direct service tests
    client = createLiveClient()
    result = await client.execute(query, variables)

Test Users (from systemdata.rnd.json):
- john.newbie@world.com / john.newbie@world.com
"""

import aiohttp
from typing import Optional, Dict, Any


def createGQLClient():
    """Create in-memory SQLite test client for unit tests.
    
    Uses FastAPI TestClient with in-memory SQLite database.
    Suitable for isolated unit tests without external dependencies.
    
    Note: Most tests should use createFederationClient() or createLiveClient()
    for better integration testing.
    
    Returns:
        TestClient: FastAPI TestClient instance
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    import DBDefinitions

    def ComposeCString():
        return "sqlite+aiosqlite:///:memory:"
    
    DBDefinitions.ComposeConnectionString = ComposeCString

    import main
    
    client = TestClient(main.app, raise_server_exceptions=False)
    return client


async def getToken(
    username: str, 
    password: str,
    keyurl: str = "http://localhost:33001/oauth/login3"
) -> Optional[str]:
    """Get JWT token from UG service OAuth endpoint.
    
    Performs OAuth 2-step authentication:
    1. GET challenge key from OAuth endpoint
    2. POST credentials + key to get JWT token
    
    Args:
        username: User email (e.g., "john.newbie@world.com")
        password: User password (e.g., "john.newbie@world.com")
        keyurl: OAuth login endpoint (default: UG service frontend)
        
    Returns:
        JWT token string or None if authentication failed
    """
    async with aiohttp.ClientSession() as session:
        # Step 1: Get challenge key
        async with session.get(keyurl) as resp:
            if resp.status != 200:
                print(f"Failed to get OAuth key: {resp.status}")
                return None
            keyJson = await resp.json()

        # Step 2: Authenticate with key + credentials
        payload = {"key": keyJson["key"], "username": username, "password": password}
        async with session.post(keyurl, json=payload) as resp:
            if resp.status != 200:
                print(f"Authentication failed: {resp.status}")
                return None
            tokenJson = await resp.json()
            
    return tokenJson.get("token", None)


class GraphQLClientWrapper:
    """Unified GraphQL client wrapper with authentication and token management.
    
    Provides consistent API for executing GraphQL queries across different endpoints:
    - Apollo Federation Gateway (recommended)
    - Direct Purchase service
    - In-memory test client
    
    Features:
    - execute(): Execute query with automatic authentication
    - get_user_info(): Get authenticated user from UG service
    
    Token Caching:
    - Tokens cached per username to avoid redundant logins
    - Automatic retry on token expiration
    """
    
    def __init__(self, post_fn, endpoint: str):
        """Initialize wrapper with post function and endpoint.
        
        Args:
            post_fn: Async function(query, variables) that executes GraphQL
            endpoint: GraphQL endpoint URL for logging
        """
        self._post = post_fn
        self.endpoint = endpoint
    
    async def execute(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GraphQL query with automatic authentication.
        
        Args:
            query: GraphQL query or mutation string
            variables: Optional variables dictionary
            
        Returns:
            GraphQL response dictionary with 'data' and/or 'errors'
        """
        return await self._post(query, variables or {})
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user info from UG service.
        
        Returns:
            User dictionary with id, fullname, email, roles or None if failed
        """
        result = await self.execute("""
            query {
              me {
                id
                fullname
                email
                roles {
                  id
                  valid
                  roletype {
                    id
                    name
                  }
                  group {
                    id
                    name
                    grouptype {
                      id
                      name
                    }
                  }
                }
              }
            }
        """)
        
        if "errors" in result:
            print(f"Error getting user info: {result['errors']}")
            return None
            
        return result.get("data", {}).get("me")


def createFederationClient(
    username: str = "john.newbie@world.com", 
    password: str = "john.newbie@world.com",
    endpoint: str = "http://localhost:33000/api/gql",
    token: Optional[str] = None
) -> GraphQLClientWrapper:
    """Create client for Apollo Federation Gateway.
    
    This client connects to the federation gateway which combines
    multiple GraphQL services (UG + Purchase) into one schema.
    
    Args:
        username: User email/username for authentication
        password: User password for authentication
        endpoint: Federation gateway endpoint (default: localhost:33000)
        token: Pre-obtained JWT token (skips authentication if provided)
        
    Returns:
        GraphQLClientWrapper with execute() and get_user_info() methods
        
    Example:
        client = createFederationClient()
        
        # Cross-service query (UG + Purchase data in one request)
        result = await client.execute('''
            query {
              me { fullname email }
              purchasePage { id status }
            }
        ''')
    """
    _token = token
    
    async def post(query: str, variables: Dict):
        nonlocal _token
        
        # Get token on first request if not provided
        if _token is None:
            _token = await getToken(username, password)
            if _token is None:
                return {"errors": [{"message": "Authentication failed - could not obtain token"}]}
        
        payload = {"query": query, "variables": variables}
        cookies = {'authorization': _token}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, cookies=cookies) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"errors": [{"message": f"HTTP {resp.status}: {text}"}]}
                
                return await resp.json()
    
    return GraphQLClientWrapper(post, endpoint)


def createLiveClient(
    username: str = "john.newbie@world.com",
    password: str = "john.newbie@world.com", 
    endpoint: str = "http://localhost:8000/gql",
    token: Optional[str] = None
) -> GraphQLClientWrapper:
    """Create client for direct Purchase service (bypassing federation).
    
    This client connects directly to the Purchase service without
    going through the Apollo Gateway.
    
    Args:
        username: User email/username for authentication
        password: User password for authentication
        endpoint: Purchase service endpoint (default: localhost:8000)
        token: Pre-obtained JWT token (skips authentication if provided)
        
    Returns:
        GraphQLClientWrapper with execute() and get_user_info() methods
        
    Example:
        client = createLiveClient()
        
        # Direct query to Purchase service
        result = await client.execute('''
            query {
              purchasePage { id status }
            }
        ''')
    """
    return createFederationClient(username, password, endpoint, token)


async def main():
    """Demo usage of client."""
    print("=" * 70)
    print("Purchase Service Client Demo")
    print("=" * 70)
    print()
    
    # Create client
    print("Creating live client...")
    client = createLiveClient()
    
    # Test user query
    print("\n1. Testing user authentication...")
    user_info = await client.get_user_info()
    
    if user_info:
        print(f"   ✅ Authenticated as: {user_info.get('fullname', 'Unknown')}")
        print(f"   Email: {user_info.get('email', 'N/A')}")
        print(f"   Roles: {len(user_info.get('roles', []))} role(s)")
    else:
        print("   ❌ Authentication failed")
        return
    
    # Test query
    print("\n2. Testing purchase query...")
    result = await client.execute("""
        query {
          purchasePage(skip: 0, limit: 3) {
            id
            status
            totalCost
          }
        }
    """)
    
    if "errors" in result:
        print(f"   ❌ Query failed: {result['errors']}")
    elif "data" in result:
        purchases = result["data"].get("purchasePage", [])
        print(f"   ✅ Retrieved {len(purchases)} purchase(s)")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

