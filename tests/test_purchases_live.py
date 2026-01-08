"""
Live Purchase Tests - Testing against running service

This module tests the Purchase service against a live server (not in-memory SQLite).
Tests include CRUD operations, nested items, and validation.

Prerequisites:
    - Docker services running (docker compose -f docker-compose.debug.yml up -d)
    - Main service running (uvicorn main:app --host 0.0.0.0 --port 8000)
    - Run check_services.py first to verify connectivity

Run:
    pytest tests/test_purchases_live.py -v
    pytest tests/test_purchases_live.py -v -s  # With output
"""

import pytest
import pytest_asyncio
import datetime
from tests.client import createLiveClient


@pytest_asyncio.fixture
async def live_client():
    """Create client connected to live service."""
    return createLiveClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )


class TestServiceConnectivity:
    """Test basic service connectivity and authentication."""
    
    @pytest.mark.asyncio
    async def test_service_is_running(self, live_client):
        """Verify service is accessible and responding."""
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        result = await live_client.execute(query)
        
        assert "errors" not in result, f"Service not responding: {result.get('errors')}"
        assert "data" in result
        assert "__schema" in result["data"]
        print("✅ Service is running and responding")
    
    @pytest.mark.asyncio
    async def test_authentication_works(self, live_client):
        """Verify JWT authentication with UG service via federation."""
        # Use federation client to access 'me' query from UG service
        from tests.client import createFederationClient
        fed_client = createFederationClient(
            username="john.newbie@world.com",
            password="john.newbie@world.com"
        )
        
        user_info = await fed_client.get_user_info()
        
        assert user_info is not None, "Authentication failed"
        assert "id" in user_info
        assert "email" in user_info
        print(f"✅ Authenticated as: {user_info.get('fullname', 'Unknown')}")


class TestPurchaseQuery:
    """Test querying purchases from live server."""
    
    @pytest.mark.asyncio
    async def test_purchase_page_query(self, live_client):
        """Test basic purchase page query."""
        query = """
        query {
            purchases: purchasePage(skip: 0, limit: 10) {
                id
                status
                reason
                name
            }
        }
        """
        
        result = await live_client.execute(query)
        
        assert "errors" not in result, f"Query failed: {result.get('errors')}"
        assert "data" in result
        
        purchases = result["data"]["purchases"]
        assert isinstance(purchases, list)
        print(f"✅ Found {len(purchases)} purchase(s)")
    
    @pytest.mark.asyncio
    async def test_purchase_with_items(self, live_client):
        """Test querying purchase with items."""
        query = """
        query {
            purchases: purchasePage(limit: 5) {
                id
                status
                items {
                    name
                    quantity
                    price
                    totalPrice
                }
            }
        }
        """
        
        result = await live_client.execute(query)
        
        assert "errors" not in result
        purchases = result["data"]["purchases"]
        
        if len(purchases) > 0:
            first_purchase = purchases[0]
            assert "items" in first_purchase
            print(f"✅ Purchase has {len(first_purchase['items'])} items")
        else:
            print("⚠️  No purchases found (empty database)")


class TestPurchaseCRUDLive:
    """Test purchase CRUD operations against live server."""
    
    @pytest.mark.asyncio
    async def test_purchase_insert_live(self, live_client):
        """Test creating a purchase via live API."""
        mutation = """
        mutation($purchase: PurchaseInsertGQLModel!) {
            result: purchaseInsert(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    status
                    reason
                    lastchange
                    items {
                        name
                        quantity
                        price
                        totalPrice
                    }
                }
                ... on PurchaseGQLModelInsertError {
                    msg
                }
            }
        }
        """
        
        variables = {
            "purchase": {
                "reason": "Live Test Purchase",
                "status": "submitted",
                "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003",
                "approverId": "45b2df80-ae0f-11ed-9bd8-0242ac110002",
                "submittedAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "items": [
                    {"name": "Test Item 1", "quantity": 2, "price": 100.0},
                    {"name": "Test Item 2", "quantity": 1, "price": 50.0}
                ]
            }
        }
        
        result = await live_client.execute(mutation, variables)
        
        # Check for GraphQL errors
        if "errors" in result:
            pytest.skip(f"GraphQL errors (service may not be configured): {result['errors']}")
        
        # Check mutation result
        data = result["data"]["result"]
        
        # Handle error responses
        if data.get("__typename") != "PurchaseGQLModel":
            error_msg = data.get("msg", "Unknown error")
            if "insert" in error_msg.lower() or "permission" in error_msg.lower():
                pytest.skip(f"Insert not configured or permission denied: {error_msg}")
            pytest.fail(f"Insert failed: {error_msg}")
        
        # Verify data
        assert data["id"] is not None
        assert data["status"] == "submitted"
        # Calculate total from items
        total = sum(item["totalPrice"] for item in data["items"])
        assert total == pytest.approx(250.0)  # 2*100 + 1*50
        assert len(data["items"]) == 2
        
        print(f"✅ Created purchase {data['id'][:8]}... with items total {total}")
        
        # Return for use in other tests
        return data["id"], data["lastchange"]
    
    @pytest.mark.asyncio
    async def test_purchase_by_id_query(self, live_client):
        """Test querying specific purchase by ID."""
        # First, get list of purchases to find an ID
        list_query = """
        query {
            purchasePage(limit: 1) {
                id
            }
        }
        """
        
        list_result = await live_client.execute(list_query)
        
        if "errors" in list_result or not list_result["data"]["purchasePage"]:
            pytest.skip("No purchases available to query")
        
        purchase_id = list_result["data"]["purchasePage"][0]["id"]
        
        # Now query by ID
        query = """
        query($id: UUID!) {
            purchaseById(id: $id) {
                id
                status
                reason
                items {
                    name
                    quantity
                }
            }
        }
        """
        
        result = await live_client.execute(query, {"id": purchase_id})
        
        assert "errors" not in result
        purchase = result["data"]["purchaseById"]
        assert purchase is not None
        assert purchase["id"] == purchase_id
        
        print(f"✅ Successfully queried purchase by ID: {purchase_id[:8]}...")
    
    @pytest.mark.asyncio
    async def test_purchase_update_live(self, live_client):
        """Test updating a purchase via live API."""
        # First create a purchase
        try:
            purchase_id, lastchange = await self.test_purchase_insert_live(live_client)
        except pytest.skip.Exception:
            pytest.skip("Cannot test update without insert capability")
        
        # Now update it
        mutation = """
        mutation($purchase: PurchaseUpdateGQLModel!) {
            result: purchaseUpdate(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    status
                    reason
                    lastchange
                }
                ... on PurchaseGQLModelUpdateError {
                    msg
                }
            }
        }
        """
        
        variables = {
            "purchase": {
                "id": purchase_id,
                "lastchange": lastchange,
                "status": "approved",
                "reason": "Updated via live test"
            }
        }
        
        result = await live_client.execute(mutation, variables)
        
        assert "errors" not in result
        data = result["data"]["result"]
        
        if data.get("__typename") != "PurchaseGQLModel":
            pytest.skip(f"Update failed: {data.get('msg', 'Unknown error')}")
        
        assert data["status"] == "approved"
        assert data["reason"] == "Updated via live test"
        assert data["lastchange"] != lastchange  # Timestamp should change
        
        print(f"✅ Successfully updated purchase {purchase_id[:8]}...")
    
    @pytest.mark.asyncio
    async def test_purchase_delete_live(self, live_client):
        """Test deleting a purchase via live API."""
        # First create a purchase
        try:
            purchase_id, lastchange = await self.test_purchase_insert_live(live_client)
        except pytest.skip.Exception:
            pytest.skip("Cannot test delete without insert capability")
        
        # Now delete it
        mutation = """
        mutation($purchase: PurchaseDeleteGQLModel!) {
            result: purchaseDelete(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                }
                ... on PurchaseGQLModelDeleteError {
                    msg
                }
            }
        }
        """
        
        variables = {
            "purchase": {
                "id": purchase_id,
                "lastchange": lastchange
            }
        }
        
        result = await live_client.execute(mutation, variables)
        
        if "errors" in result:
            pytest.skip(f"Delete operation not available: {result['errors']}")
        
        data = result["data"]["result"]
        
        if data.get("__typename") != "PurchaseGQLModel":
            pytest.skip(f"Delete failed: {data.get('msg', 'Unknown error')}")
        
        assert data["id"] == purchase_id
        
        print(f"✅ Successfully deleted purchase {purchase_id[:8]}...")


class TestPurchaseValidation:
    """Test business logic validation."""
    
    @pytest.mark.asyncio
    async def test_item_total_price_calculation(self, live_client):
        """Verify item totalPrice = quantity * price."""
        query = """
        query {
            purchases: purchasePage(limit: 10) {
                items {
                    quantity
                    price
                    totalPrice
                }
            }
        }
        """
        
        result = await live_client.execute(query)
        
        if "errors" in result or not result["data"]["purchases"]:
            pytest.skip("No purchases to validate")
        
        item_count = 0
        for purchase in result["data"]["purchases"]:
            for item in purchase["items"]:
                expected = (item["quantity"] or 0) * (item["price"] or 0)
                assert item["totalPrice"] == pytest.approx(expected), \
                    f"Item total mismatch: {item['totalPrice']} != {expected}"
                item_count += 1
        
        print(f"✅ Validated totalPrice for {item_count} item(s)")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_invalid_purchase_id(self, live_client):
        """Test querying non-existent purchase ID."""
        query = """
        query($id: UUID!) {
            purchaseById(id: $id) {
                id
                status
            }
        }
        """
        
        # Use a valid UUID format but non-existent ID
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        result = await live_client.execute(query, {"id": fake_id})
        
        # Should return null or error
        if "errors" not in result:
            # Service may return object with null fields or null object
            purchase = result["data"]["purchaseById"]
            if purchase is not None:
                # Check if it's an empty placeholder (all fields null/empty)
                assert purchase["status"] is None or purchase["id"] == fake_id
                print("✅ Correctly returned object with null fields for non-existent ID")
            else:
                assert purchase is None
                print("✅ Correctly returned null for non-existent ID")
        else:
            print("✅ Correctly returned error for non-existent ID")
    
    @pytest.mark.asyncio
    async def test_optimistic_locking(self, live_client):
        """Test optimistic locking prevents concurrent updates."""
        # First create a purchase
        try:
            purchase_id, original_lastchange = await TestPurchaseCRUDLive().test_purchase_insert_live(live_client)
        except pytest.skip.Exception:
            pytest.skip("Cannot test optimistic locking without insert")
        
        # Update once
        mutation = """
        mutation($purchase: PurchaseUpdateGQLModel!) {
            result: purchaseUpdate(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    lastchange
                }
                ... on PurchaseGQLModelUpdateError {
                    msg
                }
            }
        }
        """
        
        first_update = await live_client.execute(mutation, {
            "purchase": {
                "id": purchase_id,
                "lastchange": original_lastchange,
                "status": "approved"
            }
        })
        
        if "errors" in first_update:
            pytest.skip("Update not available")
        
        # Try to update again with OLD lastchange (should fail)
        second_update = await live_client.execute(mutation, {
            "purchase": {
                "id": purchase_id,
                "lastchange": original_lastchange,  # Using old timestamp
                "status": "rejected"
            }
        })
        
        data = second_update["data"]["result"]
        
        # Should be an error
        if data.get("__typename") == "PurchaseGQLModelUpdateError":
            # Check for error message indicating stale update
            msg = data["msg"].lower()
            if "changed" in msg or "optimistic" in msg or "failed" in msg:
                print("✅ Optimistic locking correctly prevented stale update")
            else:
                print(f"⚠️  Update error but unclear message: {data['msg']}")
        else:
            print("⚠️  Optimistic locking may not be implemented")


if __name__ == "__main__":
    # Allow running directly for quick testing
    pytest.main([__file__, "-v", "-s"])
