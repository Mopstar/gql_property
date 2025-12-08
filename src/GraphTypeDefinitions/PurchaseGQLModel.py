import typing
import datetime
import uuid

import strawberry
import strawberry.types

from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import (
    getLoadersFromInfo,
    PageResolver,
    VectorResolver,
    ScalarResolver,
    InputModelMixin,
    createInputs2,
)
from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension

from .BaseGQLModel import BaseGQLModel, IDType, Relation

# lazy references
PurchaseItemGQLModel = typing.Annotated["PurchaseItemGQLModel", strawberry.lazy(".PurchaseItemGQLModel")]
UserGQLModel = typing.Annotated["UserGQLModel", strawberry.lazy(".UserGQLModel")]


###########################################################################################################################
# Filters
###########################################################################################################################


@createInputs2
class PurchaseInputFilter:
    id: IDType
    path: str
    status: str
    requester_id: IDType
    approver_id: IDType


###########################################################################################################################
# Main GQL type
###########################################################################################################################


@strawberry.federation.type(description="Purchase", keys=["id"])
class PurchaseGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PurchaseModel

    path: typing.Optional[str] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    reason: typing.Optional[str] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    description: typing.Optional[str] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    correct_examples: typing.Optional[str] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    other_info_website: typing.Optional[str] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    handover_request: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    reasoning: typing.Optional[str] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    status: typing.Optional[str] = strawberry.field(
        default=None,
        description="Lifecycle status of the request (draft/submitted/approved/declined/fulfilled)",
        permission_classes=[OnlyForAuthentized],
    )
    requested_delivery: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    submitted_at: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )

    maininfo_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    requester_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )
    approver_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        permission_classes=[OnlyForAuthentized],
    )

    maininfo: typing.Optional["PurchaseGQLModel"] = strawberry.field(
        description="Parent purchase",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["PurchaseGQLModel"](fkey_field_name="maininfo_id"),
    )

    subinfo: typing.List[PurchaseItemGQLModel] = strawberry.field(
        description="Purchase items",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["PurchaseItemGQLModel"](fkey_field_name="purchase_id", whereType=None),
    )

    @strawberry.field(
        description="List of items belonging to this request (alias for subinfo)",
        permission_classes=[OnlyForAuthentized],
    )
    async def items(self, info: strawberry.types.Info) -> typing.List[PurchaseItemGQLModel]:
        loaders = getLoadersFromInfo(info)
        loader = loaders.PurchaseItem
        rows = list(await loader.filter_by(purchase_id=self.id))
        from .PurchaseItemGQLModel import PurchaseItemGQLModel as ItemModel

        return [ItemModel.from_dataclass(row) for row in rows]

    @strawberry.field(
        description="User who submitted the request",
        permission_classes=[OnlyForAuthentized],
    )
    async def requester(self, info: strawberry.types.Info) -> typing.Optional["UserGQLModel"]:
        if self.requester_id is None:
            return None
        from .UserGQLModel import UserGQLModel

        return await UserGQLModel.resolve_reference(info=info, id=self.requester_id)

    @strawberry.field(
        description="User responsible for approving the request",
        permission_classes=[OnlyForAuthentized],
    )
    async def approver(self, info: strawberry.types.Info) -> typing.Optional["UserGQLModel"]:
        if self.approver_id is None:
            return None
        from .UserGQLModel import UserGQLModel

        return await UserGQLModel.resolve_reference(info=info, id=self.approver_id)

    @strawberry.field(
        name="totalCost",
        description="Total price of all items in the request",
        permission_classes=[OnlyForAuthentized],
    )
    async def total_cost(self, info: strawberry.types.Info) -> float:
        loaders = getLoadersFromInfo(info)
        loader = loaders.PurchaseItem
        items = list(await loader.filter_by(purchase_id=self.id))
        return sum((item.price or 0.0) * (item.quantity or 0.0) for item in items)

    @strawberry.field(
        description="Timestamp when the request was sent for approval",
        permission_classes=[OnlyForAuthentized],
    )
    async def submitted(self) -> typing.Optional[datetime.datetime]:
        return self.submitted_at


###########################################################################################################################
# Input models for items and purchase
###########################################################################################################################


@strawberry.input(description="Input model for purchase item")
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


@strawberry.input(description="Input type for creating a Purchase")
class PurchaseInsertGQLModel(InputModelMixin):
    getLoader = PurchaseGQLModel.getLoader

    path: typing.Optional[str] = strawberry.field(default=None)
    reason: typing.Optional[str] = strawberry.field(default=None)
    description: typing.Optional[str] = strawberry.field(default=None)
    correct_examples: typing.Optional[str] = strawberry.field(default=None)
    other_info_website: typing.Optional[str] = strawberry.field(default=None)
    handover_request: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    reasoning: typing.Optional[str] = strawberry.field(default=None)
    maininfo_id: typing.Optional[IDType] = strawberry.field(default=None)
    subinfo: typing.Optional[typing.List[PurchaseItemInsertModel]] = strawberry.field(
        default_factory=list
    )
    status: typing.Optional[str] = strawberry.field(default="draft")
    requested_delivery: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    submitted_at: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    requester_id: typing.Optional[IDType] = strawberry.field(default=None)
    approver_id: typing.Optional[IDType] = strawberry.field(default=None)

    # system/private fields
    id: typing.Optional[IDType] = strawberry.field(default=None)
    rbacobject_id: strawberry.Private[IDType] = None
    createdby_id: strawberry.Private[IDType] = None
    changedby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Input type for updating an existing Purchase")
class PurchaseUpdateGQLModel(InputModelMixin):
    """
    Input for updating a Purchase.

    - `id` is required (must identify the purchase being updated)
    - other fields are optional and will be updated when provided (non-None)
    """

    getLoader = PurchaseGQLModel.getLoader

    id: IDType  # required for update

    path: typing.Optional[str] = None
    reason: typing.Optional[str] = None
    description: typing.Optional[str] = None
    correct_examples: typing.Optional[str] = None
    other_info_website: typing.Optional[str] = strawberry.field(default=None)
    handover_request: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    reasoning: typing.Optional[str] = strawberry.field(default=None)
    maininfo_id: typing.Optional[IDType] = strawberry.field(default=None)
    status: typing.Optional[str] = strawberry.field(
        default=None,
        description="Lifecycle status of the request (draft/submitted/approved/declined/fulfilled)",
    )
    requested_delivery: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    submitted_at: typing.Optional[datetime.datetime] = strawberry.field(default=None)
    requester_id: typing.Optional[IDType] = strawberry.field(default=None)
    approver_id: typing.Optional[IDType] = strawberry.field(default=None)

    # optimistic concurrency (if you decide to enforce it)
    lastchange: typing.Optional[datetime.datetime] = strawberry.field(default=None)

    # list of items; if provided, replaces the whole list
    subinfo: typing.Optional[typing.List[PurchaseItemInsertModel]] = strawberry.field(
        default=None,
        description=(
            "Complete list of purchase items to sync with the DB. "
            "If omitted, items are left unchanged."
        ),
    )

    # private/system fields – filled by resolvers/mutations
    rbacobject_id: strawberry.Private[IDType] = None
    createdby_id: strawberry.Private[IDType] = None
    changedby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Input type for deleting a Purchase")
class PurchaseDeleteGQLModel(InputModelMixin):
    """
    Input for deleting a Purchase.

    - `id` identifies the purchase
    - `lastchange` is used for optimistic locking in delete mutation
    """

    getLoader = PurchaseGQLModel.getLoader

    id: IDType
    lastchange: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="Timestamp of last modification, used to detect concurrent changes",
    )


###########################################################################################################################
# Queries
###########################################################################################################################


@strawberry.type(description="Purchase queries")
class PurchaseQuery:
    purchase_by_id: typing.Optional[PurchaseGQLModel] = strawberry.field(
        description="get a purchase by its id",
        permission_classes=[OnlyForAuthentized],
        resolver=PurchaseGQLModel.load_with_loader,
    )

    purchase_page: typing.List[PurchaseGQLModel] = strawberry.field(
        description="get a page of purchases",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[PurchaseGQLModel](whereType=PurchaseInputFilter),
    )


###########################################################################################################################
# Mutations
###########################################################################################################################


@strawberry.type(description="Purchase mutations")
class PurchaseMutation:
    @strawberry.mutation(
        description="Insert a purchase record",
        permission_classes=[OnlyForAuthentized],
    )
    async def purchase_insert(
        self,
        info: strawberry.Info,
        purchase: PurchaseInsertGQLModel,
    ) -> typing.Union[PurchaseGQLModel, InsertError[PurchaseGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).PurchaseModel
            from ..DBDefinitions.purchasemodel import PurchaseModel, PurchaseItem

            new_id = purchase.id or uuid.uuid4()

            purchase_data = {
                "id": new_id,
                "path": purchase.path,
                "reason": purchase.reason,
                "description": purchase.description,
                "correct_examples": purchase.correct_examples,
                "other_info_website": purchase.other_info_website,
                "handover_request": purchase.handover_request,
                "reasoning": purchase.reasoning,
                "maininfo_id": purchase.maininfo_id,
                "status": purchase.status,
                "requested_delivery": purchase.requested_delivery,
                "submitted_at": purchase.submitted_at,
                "requester_id": purchase.requester_id,
                "approver_id": purchase.approver_id,
                "rbacobject_id": purchase.rbacobject_id,
                "createdby_id": purchase.createdby_id,
                "changedby_id": purchase.changedby_id,
            }

            db_row = PurchaseModel(**purchase_data)

            session = loader.session
            session.add(db_row)

            # items
            if purchase.subinfo:
                for item_input in purchase.subinfo:
                    item_data = {
                        "id": item_input.id or uuid.uuid4(),
                        "purchase_id": new_id,
                        "name": item_input.name,
                        "quantity": item_input.quantity or 0.0,
                        "price": item_input.price or 0.0,
                        "createdby_id": item_input.createdby_id,
                    }
                    item_row = PurchaseItem(**item_data)
                    session.add(item_row)

            await session.commit()
            await session.refresh(db_row)

            return PurchaseGQLModel.from_dataclass(db_row)

        except Exception as e:
            import traceback

            traceback.print_exc()
            return InsertError[PurchaseGQLModel](msg=str(e), _input=purchase)

    @strawberry.mutation(
        description="Update a purchase record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, PurchaseGQLModel]()],
    )
    async def purchase_update(
        self,
        info: strawberry.Info,
        purchase: PurchaseUpdateGQLModel,
        db_row: typing.Any,
    ) -> typing.Union[PurchaseGQLModel, UpdateError[PurchaseGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).PurchaseModel
            session = loader.session

            # scalar fields
            if purchase.path is not None:
                db_row.path = purchase.path
            if purchase.reason is not None:
                db_row.reason = purchase.reason
            if purchase.description is not None:
                db_row.description = purchase.description
            if purchase.correct_examples is not None:
                db_row.correct_examples = purchase.correct_examples
            if purchase.other_info_website is not None:
                db_row.other_info_website = purchase.other_info_website
            if purchase.handover_request is not None:
                db_row.handover_request = purchase.handover_request
            if purchase.reasoning is not None:
                db_row.reasoning = purchase.reasoning
            if purchase.maininfo_id is not None:
                db_row.maininfo_id = purchase.maininfo_id
            if purchase.status is not None:
                db_row.status = purchase.status
            if purchase.requested_delivery is not None:
                db_row.requested_delivery = purchase.requested_delivery
            if purchase.submitted_at is not None:
                db_row.submitted_at = purchase.submitted_at
            if purchase.requester_id is not None:
                db_row.requester_id = purchase.requester_id
            if purchase.approver_id is not None:
                db_row.approver_id = purchase.approver_id

            # items replacement if provided
            if purchase.subinfo is not None:
                from ..DBDefinitions.purchasemodel import PurchaseItem

                # clear existing items (relationship has cascade delete-orphan)
                if getattr(db_row, "subinfo", None) is not None:
                    db_row.subinfo.clear()

                for item_input in purchase.subinfo:
                    item_row = PurchaseItem(
                        id=item_input.id or uuid.uuid4(),
                        purchase_id=db_row.id,
                        name=item_input.name,
                        quantity=item_input.quantity or 0.0,
                        price=item_input.price or 0.0,
                        createdby_id=item_input.createdby_id,
                    )
                    db_row.subinfo.append(item_row)

            # update lastchange timestamp
            db_row.lastchange = datetime.datetime.utcnow()

            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            return PurchaseGQLModel.from_dataclass(db_row)

        except Exception as e:
            import traceback

            traceback.print_exc()
            return UpdateError[PurchaseGQLModel](msg=str(e), _input=purchase)

    @strawberry.mutation(
        description="Delete a purchase record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, PurchaseGQLModel]()],
    )
    async def purchase_delete(
        self,
        info: strawberry.Info,
        purchase: PurchaseDeleteGQLModel,
        db_row: typing.Any,
    ) -> typing.Optional[DeleteError[PurchaseGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).PurchaseModel
            session = loader.session

            await session.delete(db_row)
            await session.commit()

            # Optionally track deleted ids in context for loaders
            deleted_ids = info.context.setdefault("deleted_purchases", set())
            deleted_ids.add(purchase.id)

            return None

        except Exception as e:
            import traceback

            traceback.print_exc()
            return DeleteError[PurchaseGQLModel](msg=str(e), _input=purchase)