import typing
import datetime
import dataclasses
import strawberry

from .BaseGQLModel import BaseGQLModel, IDType
from uoishelpers.resolvers import ScalarResolver, getLoadersFromInfo


@strawberry.federation.type(description="Purchase item", keys=["id"])
class PurchaseItemGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PurchaseItem

    @classmethod
    def from_dataclass(cls, db_row):
        payload = dataclasses.asdict(db_row)
        payload.pop("purchase_id", None)
        return cls(**payload)

    name: typing.Optional[str] = strawberry.field(default=None)
    quantity: typing.Optional[float] = strawberry.field(default=None)
    price: typing.Optional[float] = strawberry.field(default=None)

    @strawberry.field(name="totalPrice", description="Derived price = quantity * unit price")
    def total_price(self) -> float:
        return (self.quantity or 0.0) * (self.price or 0.0)

