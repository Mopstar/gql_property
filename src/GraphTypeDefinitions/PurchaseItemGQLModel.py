import typing
import datetime
import strawberry

from .BaseGQLModel import BaseGQLModel, IDType
from uoishelpers.resolvers import ScalarResolver

@strawberry.federation.type(description="Purchase item", keys=["id"])
class PurchaseItemGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        from src.Dataloaders import createLoadersContext
        from uoishelpers.resolvers import getLoadersFromInfo
        return getLoadersFromInfo(info).PurchaseItem

    name: typing.Optional[str] = strawberry.field(default=None)
    quantity: typing.Optional[float] = strawberry.field(default=None)
    price: typing.Optional[float] = strawberry.field(default=None)

