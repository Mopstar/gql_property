import typing
import datetime
import strawberry

from .BaseGQLModel import BaseGQLModel, IDType, Relation
from uoishelpers.resolvers import ScalarResolver, VectorResolver, InputModelMixin, TreeInputStructureMixin, getLoadersFromInfo

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
        resolver=VectorResolver["PurchaseItemGQLModel"](fkey_field_name="purchase_id", whereType=None)
    )


@strawberry.input(
    description="Input model for purchase item"
)
class PurchaseItemInsertModel(InputModelMixin):
    @staticmethod
    def getLoader(info):
        return getLoadersFromInfo(info).PurchaseItem

    id: typing.Optional[IDType] = strawberry.field(default=None)
    name: typing.Optional[str] = strawberry.field(default=None)
    quantity: typing.Optional[float] = strawberry.field(default=None)
    price: typing.Optional[float] = strawberry.field(default=None)
    purchase_id: typing.Optional[IDType] = strawberry.field(default=None)
    createdby_id: strawberry.Private[IDType] = None


@strawberry.input(
    description="Input type for creating a Purchase"
)
class PurchaseInsertGQLModel(TreeInputStructureMixin):
    getLoader = PurchaseGQLModel.getLoader
    id: typing.Optional[IDType] = strawberry.field(default=None)
    reason: typing.Optional[str] = strawberry.field(default=None)
    description: typing.Optional[str] = strawberry.field(default=None)
    subinfo: typing.Optional[typing.List[PurchaseItemInsertModel]] = strawberry.field(default_factory=list)
    rbacobject_id: strawberry.Private[IDType] = None
    createdby_id: strawberry.Private[IDType] = None
