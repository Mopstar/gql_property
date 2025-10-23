import strawberry


from .EventGQLModel import EventMutation
from .EventInvitationGQLModel import EventInvitationMutation
from .PurchaseGQLModel import PurchaseGQLModel
from uoishelpers.resolvers import Insert, InsertError
from uoishelpers.gqlpermissions import OnlyForAuthentized
import typing
import strawberry


@strawberry.type(description="""Type for mutation root""")
class Mutation(EventMutation, EventInvitationMutation):
    @strawberry.mutation(
        description="Insert a Purchase",
        permission_classes=[OnlyForAuthentized]
    )
    async def purchase_insert(self, info: strawberry.Info, purchase: typing.Any) -> typing.Union[PurchaseGQLModel, InsertError[PurchaseGQLModel]]:
        return await Insert[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)

