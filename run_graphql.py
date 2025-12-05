import argparse
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


async def run_sample_query():
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


def main():
    parser = argparse.ArgumentParser(description="Utility helpers for the GraphQL schema")
    parser.add_argument("--print-sdl", action="store_true", help="Print federated SDL for this subgraph")
    args = parser.parse_args()

    if args.print_sdl:
        print(schema.as_str())
        return

    asyncio.run(run_sample_query())


if __name__ == "__main__":
    main()
