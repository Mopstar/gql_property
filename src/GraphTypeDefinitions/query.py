import strawberry
import typing
from uoishelpers.resolvers import PageResolver

from .EventGQLModel import EventQuery
from .EventInvitationGQLModel import EventInvitationQuery
from .PurchaseGQLModel import PurchaseGQLModel

@strawberry.interface(
    description="Purchase queries"
)
class PurchaseQuery:
    purchase_by_id: typing.Optional[PurchaseGQLModel] = strawberry.field(
        description="get a purchase by its id",
        resolver=PurchaseGQLModel.load_with_loader
    )

    purchase_page: typing.List[PurchaseGQLModel] = strawberry.field(
        description="get a page of purchases",
        resolver=PageResolver[PurchaseGQLModel](whereType=None)
    )

@strawberry.type(description="""Type for query root""")
class Query(EventQuery, EventInvitationQuery, PurchaseQuery):
    @strawberry.field(
        description="""Returns hello world"""
        )
    async def hello(
        self,
        info: strawberry.types.Info,
    ) -> str:
        return "hello world"
