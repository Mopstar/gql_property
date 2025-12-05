import typing
import datetime
import strawberry

import strawberry.types
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import (
    getLoadersFromInfo,
    PageResolver,
    VectorResolver,
    ScalarResolver,  
    InputModelMixin,
)

from .BaseGQLModel import BaseGQLModel, IDType, Relation

PurchaseItemGQLModel = typing.Annotated["PurchaseItemGQLModel", strawberry.lazy(".PurchaseItemGQLModel")]
UserGQLModel = typing.Annotated["UserGQLModel", strawberry.lazy(".UserGQLModel")]


@strawberry.federation.type(description="Purchase", keys=["id"])
class PurchaseGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PurchaseModel

    path: typing.Optional[str] = strawberry.field(default=None) 
    reason: typing.Optional[str] = strawberry.field(default=None)
    description: typing.Optional[str] = strawberry.field(default=None)
    correct_examples: typing.Optional[str] = strawberry.field(default=None)
    other_info_website: typing.Optional[str] = strawberry.field(default=None)
    handover_request: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    reasoning: typing.Optional[str] = strawberry.field(default=None)
    status: typing.Optional[str] = strawberry.field(
        default=None,
        description="Lifecycle status of the request (draft/submitted/approved/declined/fulfilled)"
    )
    requested_delivery: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    submitted_at: typing.Optional[datetime.datetime] = strawberry.field(default=None)

    maininfo_id: typing.Optional[IDType] = strawberry.field(default=None)
    requester_id: typing.Optional[IDType] = strawberry.field(default=None)
    approver_id: typing.Optional[IDType] = strawberry.field(default=None)

    maininfo: typing.Optional["PurchaseGQLModel"] = strawberry.field(
        description="Parent purchase",
        resolver=ScalarResolver["PurchaseGQLModel"](fkey_field_name="maininfo_id")
    )

    subinfo: typing.List[PurchaseItemGQLModel] = strawberry.field(
        description="Purchase items",
        resolver=VectorResolver["PurchaseItemGQLModel"](fkey_field_name="purchase_id", whereType=None)
    )

    @strawberry.field(description="List of items belonging to this request (alias for subinfo)")
    async def items(self, info: strawberry.types.Info) -> typing.List[PurchaseItemGQLModel]:
        loaders = getLoadersFromInfo(info)
        loader = loaders.PurchaseItem
        rows = list(await loader.filter_by(purchase_id=self.id))
        from .PurchaseItemGQLModel import PurchaseItemGQLModel as ItemModel
        return [
            ItemModel(
                id=row.id,
                created=row.created,
                lastchange=row.lastchange,
                createdby_id=row.createdby_id,
                changedby_id=row.changedby_id,
                rbacobject_id=row.rbacobject_id,
                name=row.name,
                quantity=row.quantity,
                price=row.price,
            )
            for row in rows
        ]

    @strawberry.field(description="User who submitted the request")
    async def requester(self, info: strawberry.types.Info) -> typing.Optional["UserGQLModel"]:
        if self.requester_id is None:
            return None
        from .UserGQLModel import UserGQLModel
        return await UserGQLModel.resolve_reference(info=info, id=self.requester_id)

    @strawberry.field(description="User responsible for approving the request")
    async def approver(self, info: strawberry.types.Info) -> typing.Optional["UserGQLModel"]:
        if self.approver_id is None:
            return None
        from .UserGQLModel import UserGQLModel
        return await UserGQLModel.resolve_reference(info=info, id=self.approver_id)

    @strawberry.field(name="totalCost", description="Total price of all items in the request")
    async def total_cost(self, info: strawberry.types.Info) -> float:
        loaders = getLoadersFromInfo(info)
        loader = loaders.PurchaseItem
        items = list(await loader.filter_by(purchase_id=self.id))
        return sum((item.price or 0.0) * (item.quantity or 0.0) for item in items)

    @strawberry.field(description="Timestamp when the request was sent for approval")
    async def submitted(self) -> typing.Optional[datetime.datetime]:
        return self.submitted_at


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
class PurchaseInsertGQLModel(InputModelMixin):
    getLoader = PurchaseGQLModel.getLoader
    id: typing.Optional[IDType] = strawberry.field(default=None)
    path: typing.Optional[str] = strawberry.field(default=None)
    reason: typing.Optional[str] = strawberry.field(default=None)
    description: typing.Optional[str] = strawberry.field(default=None)
    correct_examples: typing.Optional[str] = strawberry.field(default=None)
    other_info_website: typing.Optional[str] = strawberry.field(default=None)
    handover_request: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    reasoning: typing.Optional[str] = strawberry.field(default=None)
    maininfo_id: typing.Optional[IDType] = strawberry.field(default=None)
    subinfo: typing.Optional[typing.List[PurchaseItemInsertModel]] = strawberry.field(default_factory=list)
    status: typing.Optional[str] = strawberry.field(default="draft")
    requested_delivery: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    submitted_at: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    requester_id: typing.Optional[IDType] = strawberry.field(default=None)
    approver_id: typing.Optional[IDType] = strawberry.field(default=None)
    rbacobject_id: strawberry.Private[IDType] = None
    createdby_id: strawberry.Private[IDType] = None


@strawberry.interface(description="Purchase queries")
class PurchaseQuery:
    purchase_by_id: typing.Optional[PurchaseGQLModel] = strawberry.field(
        description="get a purchase by its id",
        permission_classes=[OnlyForAuthentized],
        resolver=PurchaseGQLModel.load_with_loader,
    )

    purchase_page: typing.List[PurchaseGQLModel] = strawberry.field(
        description="get a page of purchases",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[PurchaseGQLModel](whereType=None),
    )
