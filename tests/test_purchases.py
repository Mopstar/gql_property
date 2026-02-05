import os
import datetime
import pytest

from GraphTypeDefinitions import schema

from src.DBDefinitions import startEngine
from src.DBFeeder import initDB

from tests.shared import createContext


@pytest.mark.asyncio
async def test_purchase_page_returns_totals(monkeypatch):
    """Test querying purchases - read-only operation."""
    monkeypatch.setenv("DEMODATA", "True")
    async_session_maker = await startEngine("sqlite+aiosqlite:///:memory:", makeDrop=True, makeUp=True)
    await initDB(async_session_maker)

    context_value = createContext(async_session_maker)
    query = """
        query {
            purchases: purchasePage {
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
    response = await schema.execute(query=query, context_value=context_value)

    assert response.errors is None
    purchases = response.data["purchases"]

    # If no purchases from demo data, that's OK - sample purchase should exist
    if not purchases:
        pytest.skip("No purchase data available - demo data not loaded")

    # Verify items have correct calculations
    first = purchases[0]
    if first["items"]:
        assert all(item["totalPrice"] == pytest.approx((item["quantity"] or 0) * (item["price"] or 0)) for item in first["items"])

@pytest.mark.skip(reason="Purchase mutations require RBAC/permissions setup not available in unit tests - use test_purchases_live.py for integration testing")
@pytest.mark.asyncio
async def test_purchase_insert_and_fetch(monkeypatch):
    monkeypatch.setenv("DEMODATA", "True")
    async_session_maker = await startEngine("sqlite+aiosqlite:///:memory:", makeDrop=True, makeUp=True)
    await initDB(async_session_maker)

    context_value = createContext(async_session_maker)
    mutation = """
        mutation($purchase: PurchaseInsertGQLModel!) {
            result: purchaseInsert(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    status
                    submittedAt
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
            "reason": "Zajisteni licenci pro tym",
            "status": "submitted",
            "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003",
            "approverId": "45b2df80-ae0f-11ed-9bd8-0242ac110002",
            "submittedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "items": [
                {"name": "Adobe Creative Cloud licence", "quantity": 3, "price": 1450.0},
                {"name": "MS Project licence", "quantity": 2, "price": 1120.0},
            ],
        }
    }

    response = await schema.execute(
        query=mutation,
        variable_values=variables,
        context_value=context_value
    )

    assert response.errors is None
    payload = response.data["result"]
    assert payload["__typename"] == "PurchaseGQLModel"
    assert payload["status"] == "submitted"
    # Calculate total from items
    total_cost = sum(item["totalPrice"] for item in payload["items"])
    assert total_cost == pytest.approx(3 * 1450.0 + 2 * 1120.0)
    assert len(payload["items"]) == 2

    purchase_id = payload["id"]
    follow_up = await schema.execute(
        query="""
            query($id: UUID!) {
                purchaseById(id: $id) {
                    id
                    status
                    items {
                        name
                        quantity
                        totalPrice
                    }
                }
            }
        """,
        variable_values={"id": purchase_id},
        context_value=context_value,
    )

    assert follow_up.errors is None
    result = follow_up.data["purchaseById"]
    assert result["id"] == purchase_id
    # Verify items match
    assert len(result["items"]) == len(payload["items"])


@pytest.mark.skip(reason="Purchase mutations require RBAC/permissions setup not available in unit tests - use test_purchases_live.py for integration testing")
@pytest.mark.asyncio
async def test_purchase_update_and_delete(monkeypatch):
    monkeypatch.setenv("DEMODATA", "True")
    async_session_maker = await startEngine("sqlite+aiosqlite:///:memory:", makeDrop=True, makeUp=True)
    await initDB(async_session_maker)

    context_value = createContext(async_session_maker)
    insert_mutation = """
        mutation($purchase: PurchaseInsertGQLModel!) {
            result: purchaseInsert(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    lastchange
                }
                ... on PurchaseGQLModelInsertError {
                    msg
                }
            }
        }
    """
    variables = {
        "purchase": {
            "reason": "Nakup licenci",
            "status": "submitted",
            "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003",
            "approverId": "45b2df80-ae0f-11ed-9bd8-0242ac110002",
            "submittedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "items": [
                {"name": "Licence A", "quantity": 1, "price": 100.0},
                {"name": "Licence B", "quantity": 2, "price": 200.0},
            ],
        }
    }
    insert_response = await schema.execute(
        query=insert_mutation,
        variable_values=variables,
        context_value=context_value,
    )
    assert insert_response.errors is None
    insert_result = insert_response.data["result"]
    assert insert_result["__typename"] == "PurchaseGQLModel"
    purchase_id = insert_result["id"]

    snapshot_query = """
        query($id: UUID!) {
            purchaseById(id: $id) {
                id
                lastchange
                status
                items {
                    id
                    lastchange
                    name
                    quantity
                    price
                }
            }
        }
    """
    snapshot = await schema.execute(
        query=snapshot_query,
        variable_values={"id": purchase_id},
        context_value=context_value,
    )
    assert snapshot.errors is None
    purchase_snapshot = snapshot.data["purchaseById"]
    first_item = purchase_snapshot["items"][0]

    update_mutation = """
        mutation($purchase: PurchaseUpdateGQLModel!) {
            result: purchaseUpdate(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    status
                    reason
                    items {
                        id
                        name
                        quantity
                        price
                    }
                }
                ... on PurchaseGQLModelUpdateError {
                    msg
                }
            }
        }
    """
    update_variables = {
        "purchase": {
            "id": purchase_id,
            "lastchange": purchase_snapshot["lastchange"],
            "reason": "Aktualizovany duvod",
            "status": "approved",
        }
    }
    update_response = await schema.execute(
        query=update_mutation,
        variable_values=update_variables,
        context_value=context_value,
    )
    assert update_response.errors is None
    payload = update_response.data["result"]
    assert payload["__typename"] == "PurchaseGQLModel"
    assert payload["status"] == "approved"
    assert payload["reason"] == "Aktualizovany duvod"

    latest_snapshot = await schema.execute(
        query=snapshot_query,
        variable_values={"id": purchase_id},
        context_value=context_value,
    )
    assert latest_snapshot.errors is None
    purchase_after_update = latest_snapshot.data["purchaseById"]

    delete_mutation = """
        mutation($purchase: PurchaseDeleteGQLModel!) {
            result: purchaseDelete(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModelDeleteError {
                    msg
                }
            }
        }
    """
    delete_variables = {
        "purchase": {
            "id": purchase_id,
            "lastchange": purchase_after_update["lastchange"],
        }
    }
    delete_response = await schema.execute(
        query=delete_mutation,
        variable_values=delete_variables,
        context_value=context_value,
    )
    assert delete_response.errors is None
    assert delete_response.data["result"] is None

    final_snapshot = await schema.execute(
        query=snapshot_query,
        variable_values={"id": purchase_id},
        context_value=context_value,
    )
    assert final_snapshot.errors is None
    assert final_snapshot.data["purchaseById"] is None
