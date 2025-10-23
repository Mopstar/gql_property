import typing
import datetime
import strawberry

from .BaseGQLModel import BaseGQLModel, IDType, Relation
from uoishelpers.resolvers import ScalarResolver, VectorResolver

PurchaseItemGQLModel = typing.Annotated["PurchaseItemGQLModel", strawberry.lazy(".PurchaseItemGQLModel")]

@strawberry.federation.type(description="Purchase", keys=["id"])
class PurchaseGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        from uoishelpers.resolvers import getLoadersFromInfo
        return getLoadersFromInfo(info).PurchaseModel

    reason: typing.Optional[str] = strawberry.field(default=None)
    description: typing.Optional[str] = strawberry.field(default=None)

    subinfo: typing.List[PurchaseItemGQLModel] = strawberry.field(
        description="Purchase items",
        resolver=VectorResolver["PurchaseItemGQLModel"](fkey_field_name="purchase_id")
    )
