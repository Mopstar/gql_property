import asyncio
import os
from types import SimpleNamespace

from main import get_context
from src.GraphTypeDefinitions import schema

os.environ['DEMODATA'] = 'True'
os.environ['DEMO'] = 'True'

class DummyRequest(SimpleNamespace):
    def __init__(self):
        super().__init__(headers={}, scope={}, cookies={})

async def main():
    context = await get_context(DummyRequest())
    query = """
    query PurchasesOverview {
      purchasePage {
        id
        status
        submitted
        requestedDelivery
        reason
        description
        totalCost
        items {
          id
          name
          quantity
          price
          totalPrice
        }
      }
    }
    """
    result = await schema.execute(query, context_value=context)
    print('errors', result.errors)
    print('data', result.data)

asyncio.run(main())
