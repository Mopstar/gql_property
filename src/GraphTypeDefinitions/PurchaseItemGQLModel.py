import typing
import datetime
import dataclasses
import strawberry
import strawberry.types

from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import (
    getLoadersFromInfo,
    getUserFromInfo,
    ScalarResolver,
    VectorResolver,
    PageResolver,
    createInputs2,
    Insert,
    InsertError,
    Update,
    UpdateError,
    Delete,
    DeleteError,
    InputModelMixin,
)
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension
from uoishelpers.gqlpermissions.UserAccessControlExtension import UserAccessControlExtension

from .BaseGQLModel import BaseGQLModel, IDType, Relation

# Lazy refs
PurchaseGQLModel = typing.Annotated[
    "PurchaseGQLModel", strawberry.lazy(".PurchaseGQLModel")
]


###################################################################################################
# Filters
###################################################################################################

@createInputs2
class PurchaseItemInputFilter:
    id: IDType
    name: str
    purchase_id: IDType
    quantity: float
    price: float


###################################################################################################
# Main type
###################################################################################################

@strawberry.federation.type(
    description="Purchase item entity representing individual items in a purchase request",
    keys=["id"]
)
class PurchaseItemGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PurchaseItemModel

    @classmethod
    def from_dataclass(cls, db_row):
        payload = dataclasses.asdict(db_row)
        payload.pop("purchase_id", None)
        return cls(**payload)

    name: typing.Optional[str] = strawberry.field(
        default=None,
        description="Name of the purchased item",
        permission_classes=[OnlyForAuthentized]
    )

    description: typing.Optional[str] = strawberry.field(
        default=None,
        description="Detailed description of the item",
        permission_classes=[OnlyForAuthentized]
    )

    quantity: typing.Optional[float] = strawberry.field(
        default=None,
        description="Quantity of items to purchase",
        permission_classes=[OnlyForAuthentized]
    )

    price: typing.Optional[float] = strawberry.field(
        default=None,
        description="Unit price of the item",
        permission_classes=[OnlyForAuthentized]
    )

    unit: typing.Optional[str] = strawberry.field(
        default=None,
        description="Unit of measurement (e.g., pcs, kg, m)",
        permission_classes=[OnlyForAuthentized]
    )

    purchase_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="ID of the parent purchase request",
        permission_classes=[OnlyForAuthentized]
    )

    # Relationships
    purchase: typing.Optional["PurchaseGQLModel"] = strawberry.field(
        description="Parent purchase request",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["PurchaseGQLModel"](fkey_field_name="purchase_id")
    )

    @strawberry.field(
        name="totalPrice",
        description="Calculated total price (quantity × unit price)",
        permission_classes=[OnlyForAuthentized]
    )
    def total_price(self) -> float:
        return (self.quantity or 0.0) * (self.price or 0.0)

    @strawberry.field(
        description="Sensitive item information, only visible to authenticated users"
    )
    async def sensitive_msg(self, info: strawberry.types.Info) -> typing.Optional[str]:
        try:
            user = getUserFromInfo(info)
        except (AssertionError, AttributeError, KeyError, TypeError):
            user = None
        if isinstance(user, dict):
            has_identity = user.get("id") is not None
        else:
            has_identity = bool(user)
        return "sensitive item information" if has_identity else None


###################################################################################################
# Queries
###################################################################################################

@strawberry.interface(description="Purchase item queries")
class PurchaseItemQuery:
    purchase_item_by_id: typing.Optional[PurchaseItemGQLModel] = strawberry.field(
        description="Get a purchase item by its id",
        resolver=PurchaseItemGQLModel.load_with_loader,
        permission_classes=[OnlyForAuthentized],
    )

    purchase_item_page: typing.List[PurchaseItemGQLModel] = strawberry.field(
        description="Get a page of purchase items",
        resolver=PageResolver[PurchaseItemGQLModel](whereType=PurchaseItemInputFilter),
        permission_classes=[OnlyForAuthentized],
    )


###################################################################################################
# Inputs
###################################################################################################

@strawberry.input(description="Insert Purchase Item")
class PurchaseItemInsertGQLModel(InputModelMixin):

    @staticmethod
    def getLoader(info):
        return getLoadersFromInfo(info).PurchaseItemModel

    name: typing.Optional[str] = strawberry.field(
        description="Name of the purchased item",
        default=None
    )
    description: typing.Optional[str] = strawberry.field(
        description="Detailed description of the item",
        default=None
    )
    quantity: typing.Optional[float] = strawberry.field(
        description="Quantity of items",
        default=None
    )
    price: typing.Optional[float] = strawberry.field(
        description="Unit price",
        default=None
    )
    unit: typing.Optional[str] = strawberry.field(
        description="Unit of measurement",
        default=None
    )
    purchase_id: IDType = strawberry.field(
        description="Parent purchase request ID"
    )
    id: typing.Optional[IDType] = strawberry.field(
        description="Purchase item id",
        default=None
    )

    createdby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Update Purchase Item")
class PurchaseItemUpdateGQLModel:
    id: IDType = strawberry.field(
        description="Purchase item id"
    )
    lastchange: datetime.datetime = strawberry.field(
        description="Timestamp"
    )

    name: typing.Optional[str] = None
    description: typing.Optional[str] = None
    quantity: typing.Optional[float] = None
    price: typing.Optional[float] = None
    unit: typing.Optional[str] = None

    changedby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Delete Purchase Item")
class PurchaseItemDeleteGQLModel:
    id: IDType = strawberry.field(
        description="Purchase item id"
    )
    lastchange: datetime.datetime = strawberry.field(
        description="Last change timestamp"
    )


###################################################################################################
# Batch operations
###################################################################################################

@strawberry.input(description="Model for batch operations on purchase items")
class PurchaseEnsureItemsModel:
    @staticmethod
    def getLoader(info):
        return getLoadersFromInfo(info).PurchaseModel

    id: IDType = strawberry.field(
        description="Purchase request id"
    )
    items: typing.Optional[typing.List[PurchaseItemInsertGQLModel]] = strawberry.field(
        description="List of purchase items to ensure",
        default_factory=list
    )


###################################################################################################
# Mutations
###################################################################################################

@strawberry.interface(description="Purchase item mutations")
class PurchaseItemMutation:

    @strawberry.mutation(
        description="Insert a Purchase Item",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserAccessControlExtension[InsertError, PurchaseItemGQLModel](
                roles=["nákupní administrátor"]
            ),
            UserRoleProviderExtension[InsertError, PurchaseItemGQLModel](),
            RbacProviderExtension[InsertError, PurchaseItemGQLModel](),
            LoadDataExtension[InsertError, PurchaseItemGQLModel](
                getLoader=PurchaseItemGQLModel.getLoader,
                primary_key_name="purchase_id"
            )
        ],
    )
    async def purchase_item_insert(
            self,
            info: strawberry.Info,
            item: PurchaseItemInsertGQLModel,
            db_row: typing.Any,
            rbacobject_id: IDType,
            user_roles: typing.List[dict],
    ) -> typing.Union[PurchaseItemGQLModel, InsertError[PurchaseItemGQLModel]]:
        return await Insert[PurchaseItemGQLModel].DoItSafeWay(info=info, entity=item)

    @strawberry.mutation(
        description="Update a Purchase Item",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserAccessControlExtension[UpdateError, PurchaseItemGQLModel](
                roles=["nákupní administrátor"]
            ),
            UserRoleProviderExtension[UpdateError, PurchaseItemGQLModel](),
            RbacProviderExtension[UpdateError, PurchaseItemGQLModel](),
            LoadDataExtension[UpdateError, PurchaseItemGQLModel]()
        ],
    )
    async def purchase_item_update(
            self,
            info: strawberry.Info,
            item: PurchaseItemUpdateGQLModel,
            db_row: typing.Any,
            rbacobject_id: IDType,
            user_roles: typing.List[dict],
    ) -> typing.Union[PurchaseItemGQLModel, UpdateError[PurchaseItemGQLModel]]:
        return await Update[PurchaseItemGQLModel].DoItSafeWay(info=info, entity=item)

    @strawberry.mutation(
        description="Delete a Purchase Item",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserAccessControlExtension[DeleteError, PurchaseItemGQLModel](
                roles=["nákupní administrátor"]
            ),
            UserRoleProviderExtension[DeleteError, PurchaseItemGQLModel](),
            RbacProviderExtension[DeleteError, PurchaseItemGQLModel](),
            LoadDataExtension[DeleteError, PurchaseItemGQLModel]()
        ],
    )
    async def purchase_item_delete(
            self,
            info: strawberry.Info,
            item: PurchaseItemDeleteGQLModel,
            db_row: typing.Any,
            rbacobject_id: IDType,
            user_roles: typing.List[dict],
    ) -> typing.Optional[DeleteError[PurchaseItemGQLModel]]:
        return await Delete[PurchaseItemGQLModel].DoItSafeWay(info=info, entity=item)

    @strawberry.mutation(
        description="Accepts multiple items and if they do not exist they are created",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserRoleProviderExtension[UpdateError, PurchaseGQLModel](),
            RbacProviderExtension[UpdateError, PurchaseGQLModel](),
            LoadDataExtension[UpdateError, PurchaseGQLModel]()
        ]
    )
    async def purchase_ensure_items(
            self,
            info: strawberry.Info,
            purchase: PurchaseEnsureItemsModel,
            rbacobject_id: IDType,
            user_roles: typing.List[dict],
            db_row: typing.Any
    ) -> typing.Union[UpdateError[PurchaseGQLModel], PurchaseGQLModel]:
        from .PurchaseGQLModel import PurchaseGQLModel as _PurchaseGQLModel
        return _PurchaseGQLModel.from_dataclass(db_row)