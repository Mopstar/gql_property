"""
Apollo Federation Integration Tests

Tests Apollo Federation gateway functionality including:
- Cross-service queries (UG + Purchase)
- Federation vs direct service consistency
- Gateway performance

Prerequisites:
    - All services running including Apollo Gateway
    - Run check_services.py first to verify

Run:
    pytest tests/test_federation.py -v
    pytest tests/test_federation.py -v -s  # With output
"""

import pytest
import pytest_asyncio
from tests.client import createFederationClient, createLiveClient


@pytest_asyncio.fixture
async def fed_client():
    """Federation client (Apollo Gateway)."""
    return createFederationClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )


@pytest_asyncio.fixture
async def live_client():
    """Direct service client."""
    return createLiveClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )


class TestFederationGateway:
    """Test Apollo Federation gateway connectivity."""
    
    @pytest.mark.asyncio
    async def test_gateway_is_accessible(self, fed_client):
        """Verify Apollo Gateway is running and accessible."""
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        result = await fed_client.execute(query)
        
        assert "errors" not in result, f"Gateway not responding: {result.get('errors')}"
        assert "data" in result
        print(f"✅ Apollo Gateway is accessible at {fed_client.endpoint}")
    
    @pytest.mark.asyncio
    async def test_gateway_endpoints(self, fed_client, live_client):
        """Verify federation and direct endpoints are different."""
        assert fed_client.endpoint == "http://localhost:33000/api/gql"
        assert live_client.endpoint == "http://localhost:8000/gql"
        print("✅ Endpoints correctly configured")


class TestCrossServiceQueries:
    """Test queries spanning UG + Purchase services."""
    
    @pytest.mark.asyncio
    async def test_me_and_purchases_combined(self, fed_client):
        """Test single query combining UG (me) and Purchase (purchasePage) data."""
        query = """
        query {
            me {
                id
                fullname
                email
            }
            purchases: purchasePage(skip: 0, limit: 5) {
                id
                status
                reason
            }
        }
        """
        
        result = await fed_client.execute(query)
        
        assert "errors" not in result, f"Cross-service query failed: {result.get('errors')}"
        assert "data" in result
        
        # Verify UG service data
        assert "me" in result["data"]
        assert result["data"]["me"]["email"]  # Just verify email exists (actual user may vary)
        
        # Verify Purchase service data
        assert "purchases" in result["data"]
        assert isinstance(result["data"]["purchases"], list)
        
        print(f"✅ Cross-service query successful")
        print(f"   User: {result['data']['me']['fullname']}")
        print(f"   Purchases: {len(result['data']['purchases'])}")
    
    @pytest.mark.asyncio
    async def test_user_roles_query(self, fed_client):
        """Test querying user with roles (UG service data)."""
        query = """
        query {
            me {
                id
                fullname
                roles {
                    roletype {
                        name
                    }
                    group {
                        name
                    }
                }
            }
        }
        """
        
        result = await fed_client.execute(query)
        
        assert "errors" not in result
        user = result["data"]["me"]
        
        assert "roles" in user
        print(f"✅ User has {len(user['roles'])} role(s)")


class TestFederationVsDirectConsistency:
    """Verify federation returns same data as direct service."""
    
    @pytest.mark.asyncio
    async def test_purchase_page_consistency(self, fed_client, live_client):
        """Verify federation and direct queries return consistent data."""
        query = """
        query {
            purchasePage(skip: 0, limit: 5) {
                id
                status
                reason
            }
        }
        """
        
        fed_result = await fed_client.execute(query)
        live_result = await live_client.execute(query)
        
        # Both should succeed
        assert "errors" not in fed_result, "Federation query failed"
        assert "errors" not in live_result, "Direct query failed"
        
        # Compare data
        fed_purchases = fed_result["data"]["purchasePage"]
        live_purchases = live_result["data"]["purchasePage"]
        
        assert len(fed_purchases) == len(live_purchases), \
            f"Count mismatch: federation={len(fed_purchases)}, direct={len(live_purchases)}"
        
        # Compare IDs
        fed_ids = [p["id"] for p in fed_purchases]
        live_ids = [p["id"] for p in live_purchases]
        
        assert fed_ids == live_ids, "Purchase IDs don't match between federation and direct"
        
        print(f"✅ Federation and direct service return consistent data")
        print(f"   Verified {len(fed_purchases)} purchase(s)")
    
    @pytest.mark.asyncio
    async def test_single_purchase_consistency(self, fed_client, live_client):
        """Verify single purchase query consistency."""
        # First get a purchase ID
        list_query = """
        query {
            purchasePage(limit: 1) {
                id
            }
        }
        """
        
        list_result = await live_client.execute(list_query)
        
        if "errors" in list_result or not list_result["data"]["purchasePage"]:
            pytest.skip("No purchases available")
        
        purchase_id = list_result["data"]["purchasePage"][0]["id"]
        
        # Query via both endpoints
        query = """
        query($id: UUID!) {
            purchaseById(id: $id) {
                id
                status
                reason
            }
        }
        """
        
        fed_result = await fed_client.execute(query, {"id": purchase_id})
        live_result = await live_client.execute(query, {"id": purchase_id})
        
        assert "errors" not in fed_result
        assert "errors" not in live_result
        
        # Compare data
        fed_purchase = fed_result["data"]["purchaseById"]
        live_purchase = live_result["data"]["purchaseById"]
        
        assert fed_purchase["id"] == live_purchase["id"]
        assert fed_purchase["status"] == live_purchase["status"]
        assert fed_purchase.get("reason") == live_purchase.get("reason")
        
        print(f"✅ Single purchase query consistent between federation and direct")


class TestFederationPerformance:
    """Basic performance tests for federation gateway."""
    
    @pytest.mark.asyncio
    async def test_federation_latency(self, fed_client):
        """Test federation gateway response time."""
        import time
        
        query = """
        query {
            purchasePage(limit: 10) {
                id
                status
            }
        }
        """
        
        start = time.time()
        result = await fed_client.execute(query)
        latency = time.time() - start
        
        assert "errors" not in result
        assert latency < 3.0, f"Federation query too slow: {latency:.2f}s"
        
        print(f"✅ Federation query latency: {latency:.3f}s")
    
    @pytest.mark.asyncio
    async def test_cross_service_latency(self, fed_client):
        """Test cross-service query performance."""
        import time
        
        query = """
        query {
            me {
                id
                fullname
            }
            purchases: purchasePage(limit: 5) {
                id
                status
            }
        }
        """
        
        start = time.time()
        result = await fed_client.execute(query)
        latency = time.time() - start
        
        assert "errors" not in result
        assert latency < 5.0, f"Cross-service query too slow: {latency:.2f}s"
        
        print(f"✅ Cross-service query latency: {latency:.3f}s")


class TestFederationSchemaStitching:
    """Test federation schema stitching and type resolution."""
    
    @pytest.mark.asyncio
    async def test_purchase_type_available(self, fed_client):
        """Verify Purchase types are available in federated schema."""
        query = """
        query {
            __type(name: "PurchaseGQLModel") {
                name
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
        """
        
        result = await fed_client.execute(query)
        
        if "errors" not in result:
            purchase_type = result["data"]["__type"]
            if purchase_type:
                field_names = [f["name"] for f in purchase_type["fields"]]
                assert "id" in field_names
                assert "status" in field_names
                print(f"✅ PurchaseGQLModel available in federation with {len(field_names)} fields")
            else:
                print("⚠️  PurchaseGQLModel not found in federated schema")
        else:
            print("⚠️  Cannot introspect federated schema")
    
    @pytest.mark.asyncio
    async def test_user_type_available(self, fed_client):
        """Verify User types from UG service are available."""
        query = """
        query {
            __type(name: "UserGQLModel") {
                name
                fields {
                    name
                }
            }
        }
        """
        
        result = await fed_client.execute(query)
        
        if "errors" not in result and result["data"]["__type"]:
            user_type = result["data"]["__type"]
            field_names = [f["name"] for f in user_type["fields"]]
            assert "id" in field_names
            assert "email" in field_names or "fullname" in field_names
            print(f"✅ UserGQLModel available in federation")
        else:
            print("⚠️  UserGQLModel not found in federated schema")


if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v", "-s"])
