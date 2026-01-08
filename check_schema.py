import asyncio
from tests.client import createLiveClient

async def check_schema():
    client = createLiveClient()
    
    # Check PurchaseGQLModel fields
    result = await client.execute("""
        query {
            purchase: __type(name: "PurchaseGQLModel") {
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
            item: __type(name: "PurchaseItemGQLModel") {
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
    """)
    
    print("PurchaseGQLModel fields:")
    if "errors" not in result and result["data"]["purchase"]:
        for field in result["data"]["purchase"]["fields"]:
            print(f"  - {field['name']}: {field['type']['name'] or field['type']['kind']}")
    else:
        print("  ERROR:", result.get("errors", "Type not found"))
    
    print("\nPurchaseItemGQLModel fields:")
    if "errors" not in result and result["data"]["item"]:
        for field in result["data"]["item"]["fields"]:
            print(f"  - {field['name']}: {field['type']['name'] or field['type']['kind']}")
    else:
        print("  ERROR:", result.get("errors", "Type not found"))

asyncio.run(check_schema())
