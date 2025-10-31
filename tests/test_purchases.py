import os
import datetime
import pytest

from GraphTypeDefinitions import schema

from src.DBDefinitions import startEngine
from src.DBFeeder import initDB

from tests.shared import createContext


@pytest.mark.asyncio
async def test_purchase_page_returns_totals(monkeypatch):
    monkeypatch.setenv("DEMODATA", "True")
    async_session_maker = await startEngine("sqlite+aiosqlite:///:memory:", makeDrop=True, makeUp=True)
    await initDB(async_session_maker)

    context_value = createContext(async_session_maker)
    query = """
        query {
            purchases: purchasePage {
                id
                status
                totalCost
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
    assert purchases, "Expected demo data to include at least one purchase request"

    first = purchases[0]
    assert first["totalCost"] > 0
    assert all(item["totalPrice"] == pytest.approx((item["quantity"] or 0) * (item["price"] or 0)) for item in first["items"])


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
                    totalCost
                    submitted
                    subinfo {
                        name
                        quantity
                        price
                        totalPrice
                    }
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
            "submittedAt": datetime.datetime.utcnow().isoformat(),
            "subinfo": [
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
    assert payload["totalCost"] == pytest.approx(3 * 1450.0 + 2 * 1120.0)
    assert len(payload["subinfo"]) == 2

    purchase_id = payload["id"]
    follow_up = await schema.execute(
        query="""
            query($id: UUID!) {
                purchaseById(id: $id) {
                    id
                    status
                    totalCost
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
    assert result["totalCost"] == pytest.approx(payload["totalCost"])
