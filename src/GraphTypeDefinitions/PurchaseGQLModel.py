import typing
import datetime
import strawberry
import strawberry.types

from uoishelpers.gqlpermissions import (
    OnlyForAuthentized,
    SimpleInsertPermission,
    SimpleUpdatePermission,
    SimpleDeletePermission
)
from .authz_extensions import (
    create_insert_permissions,
    create_update_permissions,
    create_delete_permissions,
    filter_by_permissions,
    VIEWER_ROLES,
    EDITOR_ROLES,
    ADMIN_ROLES
)
from uoishelpers.resolvers import (
    getLoadersFromInfo,
    getUserFromInfo,
    PageResolver,
    VectorResolver,
    ScalarResolver,
    createInputs2,
    Insert,
    InsertError,
    Update,
    UpdateError,
    Delete,
    DeleteError,
    TreeInputStructureMixin,
)
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.RbacInsertProviderExtension import RbacInsertProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension
from uoishelpers.gqlpermissions.UserAccessControlExtension import UserAccessControlExtension

from .BaseGQLModel import BaseGQLModel, IDType, Relation

# lazy refs
PurchaseItemGQLModel = typing.Annotated[
    "PurchaseItemGQLModel", strawberry.lazy(".PurchaseItemGQLModel")
]
PurchaseItemInputFilter = typing.Annotated[
    "PurchaseItemInputFilter", strawberry.lazy(".PurchaseItemGQLModel")
]
UserGQLModel = typing.Annotated[
    "UserGQLModel", strawberry.lazy(".UserGQLModel")
]


###################################################################################################
# Filters
###################################################################################################

@createInputs2
class PurchaseInputFilter:
    id: IDType
    path: str
    status: str
    requester_id: IDType
    approver_id: IDType
    name: str
    valid: bool


###################################################################################################
# Main type
###################################################################################################

@strawberry.federation.type(
    description="Purchase request entity",
    keys=["id"]
)
class PurchaseGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PurchaseModel

    path: typing.Optional[str] = strawberry.field(
        default=None,
        description="Materialized path representing the purchase's hierarchical location",
        permission_classes=[OnlyForAuthentized]
    )

    name: typing.Optional[str] = strawberry.field(
        default=None,
        description="Purchase request name",
        permission_classes=[OnlyForAuthentized]
    )

    reason: typing.Optional[str] = strawberry.field(
        default=None,
        description="Reason for the purchase request",
        permission_classes=[OnlyForAuthentized]
    )

    description: typing.Optional[str] = strawberry.field(
        default=None,
        description="Detailed description of the purchase",
        permission_classes=[OnlyForAuthentized]
    )

    correct_examples: typing.Optional[str] = strawberry.field(
        default=None,
        description="Examples or specifications",
        permission_classes=[OnlyForAuthentized]
    )

    other_info_website: typing.Optional[str] = strawberry.field(
        default=None,
        description="Additional information or website link",
        permission_classes=[OnlyForAuthentized]
    )

    handover_request: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="Requested handover date",
        permission_classes=[OnlyForAuthentized]
    )

    reasoning: typing.Optional[str] = strawberry.field(
        default=None,
        description="Additional reasoning for the purchase",
        permission_classes=[OnlyForAuthentized]
    )

    status: typing.Optional[str] = strawberry.field(
        default=None,
        description="Purchase request status (draft, submitted, approved, rejected, completed)",
        permission_classes=[OnlyForAuthentized]
    )

    requested_delivery: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="Requested delivery date",
        permission_classes=[OnlyForAuthentized]
    )

    submitted_at: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="Date when the purchase was submitted",
        permission_classes=[OnlyForAuthentized]
    )

    requester_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="ID of the user who requested the purchase",
        permission_classes=[OnlyForAuthentized]
    )

    approver_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="ID of the user who approves/approved the purchase",
        permission_classes=[OnlyForAuthentized]
    )

    masterpurchase_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="Parent purchase request id",
        permission_classes=[OnlyForAuthentized]
    )

    maininfo_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="Main info reference ID",
        permission_classes=[OnlyForAuthentized]
    )

    valid: typing.Optional[bool] = strawberry.field(
        name="valid_raw",
        description="If the purchase is currently valid/active",
        default=None,
        permission_classes=[OnlyForAuthentized]
    )

    # Relationships
    items: typing.List[PurchaseItemGQLModel] = strawberry.field(
        description="Purchase items",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["PurchaseItemGQLModel"](
            fkey_field_name="purchase_id",
            whereType=PurchaseItemInputFilter
        )
    )

    requester: typing.Optional["UserGQLModel"] = strawberry.field(
        description="User who requested the purchase",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["UserGQLModel"](fkey_field_name="requester_id")
    )

    approver: typing.Optional["UserGQLModel"] = strawberry.field(
        description="User who approves/approved the purchase",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["UserGQLModel"](fkey_field_name="approver_id")
    )

    masterpurchase: typing.Optional["PurchaseGQLModel"] = strawberry.field(
        name="masterPurchase",
        description="Parent purchase request",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["PurchaseGQLModel"](fkey_field_name="masterpurchase_id")
    )

    subpurchases: typing.List["PurchaseGQLModel"] = strawberry.field(
        name="subPurchases",
        description="Sub-purchase requests",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["PurchaseGQLModel"](
            fkey_field_name="masterpurchase_id",
            whereType=PurchaseInputFilter
        )
    )

    @strawberry.field(
        name="valid",
        description="Check if purchase is currently valid based on status",
        permission_classes=[OnlyForAuthentized]
    )
    def valid_(self) -> typing.Optional[bool]:
        if self.valid is not None:
            return self.valid
        # Purchase is valid if it's in an active status
        active_statuses = ["draft", "submitted", "approved"]
        return self.status in active_statuses if self.status else False

    @strawberry.field(
        description="Sensitive purchase information, only visible to authenticated users",
        permission_classes=[OnlyForAuthentized]
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
        return "sensitive purchase information" if has_identity else None


###################################################################################################
# Queries
###################################################################################################

@strawberry.interface(description="Purchase queries")
class PurchaseQuery:
    purchase_by_id: typing.Optional[PurchaseGQLModel] = strawberry.field(
        description="Get a purchase by its id",
        resolver=PurchaseGQLModel.load_with_loader,
        permission_classes=[OnlyForAuthentized],
    )

    @strawberry.field(
        description="Get purchases (filtered by creator ownership or group permissions)",
        permission_classes=[OnlyForAuthentized]
    )
    async def purchase_page(
        self, 
        info: strawberry.types.Info, 
        skip: int = 0, 
        limit: int = 10
    ) -> typing.List[PurchaseGQLModel]:
        resolver = PageResolver[PurchaseGQLModel](whereType=PurchaseInputFilter)
        all_results = await resolver(self, info, skip=skip, limit=limit)
        # Filter by permissions: creator ownership OR group role
        filtered_results = await filter_by_permissions(
            info, all_results, required_roles=VIEWER_ROLES
        )
        return filtered_results


###################################################################################################
# Inputs
###################################################################################################

@strawberry.input(description="Insert Purchase")
class PurchaseInsertGQLModel(TreeInputStructureMixin):
    getLoader = PurchaseGQLModel.getLoader

    masterpurchase_id: typing.Optional[IDType] = strawberry.field(
        description="Parent purchase id",
        default=None
    )
    name: typing.Optional[str] = strawberry.field(
        description="Purchase request name",
        default=None
    )
    path: typing.Optional[str] = None
    reason: typing.Optional[str] = None
    description: typing.Optional[str] = None
    correct_examples: typing.Optional[str] = None
    other_info_website: typing.Optional[str] = None
    handover_request: typing.Optional[datetime.datetime] = None
    reasoning: typing.Optional[str] = None
    status: typing.Optional[str] = "draft"
    requested_delivery: typing.Optional[datetime.datetime] = None
    submitted_at: typing.Optional[datetime.datetime] = None
    requester_id: typing.Optional[IDType] = None
    approver_id: typing.Optional[IDType] = None

    id: typing.Optional[IDType] = None
    subpurchases: typing.Optional[typing.List["PurchaseInsertGQLModel"]] = strawberry.field(
        description="Sub-purchases",
        default_factory=list
    )

    rbacobject_id: strawberry.Private[IDType] = None
    createdby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Update Purchase")
class PurchaseUpdateGQLModel:
    id: IDType = strawberry.field(
        description="Purchase id"
    )
    lastchange: datetime.datetime = strawberry.field(
        description="Timestamp"
    )

    name: typing.Optional[str] = None
    path: typing.Optional[str] = None
    reason: typing.Optional[str] = None
    description: typing.Optional[str] = None
    correct_examples: typing.Optional[str] = None
    other_info_website: typing.Optional[str] = None
    handover_request: typing.Optional[datetime.datetime] = None
    reasoning: typing.Optional[str] = None
    status: typing.Optional[str] = None
    requested_delivery: typing.Optional[datetime.datetime] = None
    submitted_at: typing.Optional[datetime.datetime] = None
    requester_id: typing.Optional[IDType] = None
    approver_id: typing.Optional[IDType] = None

    changedby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Delete Purchase")
class PurchaseDeleteGQLModel:
    id: IDType = strawberry.field(
        description="Purchase id"
    )
    lastchange: datetime.datetime = strawberry.field(
        description="Last change timestamp"
    )


###################################################################################################
# Mutations
###################################################################################################

@strawberry.interface(description="Purchase mutations")
class PurchaseMutation:

    @strawberry.mutation(
        description="Create purchase - user becomes creator with permanent access",
        extensions=create_insert_permissions(
            InsertError[PurchaseGQLModel],
            PurchaseGQLModel,
            required_roles=EDITOR_ROLES
        )
    )
    async def purchase_insert(
            self,
            info: strawberry.Info,
            purchase: PurchaseInsertGQLModel,
    ) -> typing.Union[PurchaseGQLModel, InsertError[PurchaseGQLModel]]:
        return await Insert[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)

    @strawberry.mutation(
        description="Update purchase - creator or group editor can modify",
        extensions=create_update_permissions(
            UpdateError[PurchaseGQLModel],
            PurchaseGQLModel,
            required_roles=EDITOR_ROLES
        )
    )
    async def purchase_update(
            self,
            info: strawberry.Info,
            purchase: PurchaseUpdateGQLModel,
    ) -> typing.Union[PurchaseGQLModel, UpdateError[PurchaseGQLModel]]:
        return await Update[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)

    @strawberry.mutation(
        description="Delete purchase - creator or group admin can remove",
        extensions=create_delete_permissions(
            DeleteError[PurchaseGQLModel],
            PurchaseGQLModel,
            required_roles=ADMIN_ROLES
        )
    )
    async def purchase_delete(
            self,
            info: strawberry.Info,
            purchase: PurchaseDeleteGQLModel,
    ) -> typing.Optional[DeleteError[PurchaseGQLModel]]:
        return await Delete[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)