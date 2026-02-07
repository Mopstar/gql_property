"""
PurchaseTypeGQLModel - GraphQL model for hierarchical purchase types
=====================================================================

Exposes PurchaseTypeModel through GraphQL API with tree navigation support.

Features:
- Query individual types by ID
- Query all types (with pagination)
- Navigate tree structure (parent/children)
- Filter by path for subtree queries
- CRUD mutations with authorization
"""

import typing
import strawberry
from typing import Optional, List

from .BaseGQLModel import BaseGQLModel, IDType
from src.DBDefinitions import PurchaseTypeModel

# Import for permission classes
from uoishelpers.resolvers import ScalarResolver, VectorResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized


@strawberry.federation.type(
    keys=["id"],
    description="Hierarchical purchase type taxonomy (číselník)"
)
class PurchaseTypeGQLModel(BaseGQLModel):
    """
    Purchase type in hierarchical tree structure.

    Enables categorization like:
    - Equipment → IT Equipment → Computers
    - Supplies → Office Supplies → Paper
    - Services → Consulting
    """

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return info.context["all"].get(PurchaseTypeModel, None)

    # Basic fields
    id: IDType = strawberry.field(
        description="Unique identifier",
        permission_classes=[OnlyForAuthentized]
    )

    name: Optional[str] = strawberry.field(
        default=None,
        description="Type name (e.g., 'IT Equipment')",
        permission_classes=[OnlyForAuthentized]
    )

    name_en: Optional[str] = strawberry.field(
        default=None,
        description="English name",
        permission_classes=[OnlyForAuthentized]
    )

    code: Optional[str] = strawberry.field(
        default=None,
        description="Short code (e.g., 'IT_EQUIP')",
        permission_classes=[OnlyForAuthentized]
    )

    description: Optional[str] = strawberry.field(
        default=None,
        description="Detailed explanation",
        permission_classes=[OnlyForAuthentized]
    )

    # Tree structure fields
    parent_id: Optional[IDType] = strawberry.field(
        default=None,
        description="Parent type ID (NULL for root)",
        permission_classes=[OnlyForAuthentized]
    )

    path: Optional[str] = strawberry.field(
        default=None,
        description="Materialized path (e.g., '/ROOT/EQUIPMENT/IT_EQUIPMENT/')",
        permission_classes=[OnlyForAuthentized]
    )

    level: Optional[int] = strawberry.field(
        default=None,
        description="Tree depth (0=root, 1=first level, etc.)",
        permission_classes=[OnlyForAuthentized]
    )

    # Configuration
    is_active: Optional[bool] = strawberry.field(
        default=None,
        description="Whether this type can be selected for new purchases",
        permission_classes=[OnlyForAuthentized]
    )

    sort_order: Optional[int] = strawberry.field(
        default=None,
        description="Display order within same parent",
        permission_classes=[OnlyForAuthentized]
    )

    # Tree navigation - parent
    @strawberry.field(
        description="Parent type (one level up)",
        permission_classes=[OnlyForAuthentized]
    )
    async def parent(
        self, info: strawberry.types.Info
    ) -> Optional["PurchaseTypeGQLModel"]:
        """Navigate to parent type."""
        result = await ScalarResolver[PurchaseTypeGQLModel](
            foreign_key_name="parent_id"
        )(self, info)
        return result

    # Tree navigation - children
    @strawberry.field(
        description="Child types (one level down)",
        permission_classes=[OnlyForAuthentized]
    )
    async def children(
        self, info: strawberry.types.Info
    ) -> List["PurchaseTypeGQLModel"]:
        """Navigate to child types."""
        result = await VectorResolver[PurchaseTypeGQLModel](
            foreign_key_name="parent_id"
        )(self, info)
        return result

    # Note: Add relationship to purchases when PurchaseModel is updated
    # @strawberry.field(description="Purchases using this type")
    # async def purchases(self, info) -> List["PurchaseGQLModel"]:
    #     result = await VectorResolver[PurchaseGQLModel](
    #         foreign_key_name="purchase_type_id"
    #     )(self, info)
    #     return result


###########################################################################################################################
#
# Query definitions
#
###########################################################################################################################

from uoishelpers.resolvers import PageResolver

@strawberry.field(
    description="Get a purchase type by its ID",
    permission_classes=[OnlyForAuthentized]
)
async def purchase_type_by_id(
    info: strawberry.types.Info,
    id: IDType
) -> Optional[PurchaseTypeGQLModel]:
    """Query single purchase type by ID."""
    result = await PurchaseTypeGQLModel.load_with_loader(info, id=id)
    return result

@strawberry.field(
    description="Get all purchase types (paginated). Use path filter for subtrees.",
    permission_classes=[OnlyForAuthentized]
)
async def purchase_type_page(
    info: strawberry.types.Info,
    skip: int = 0,
    limit: int = 100
) -> List[PurchaseTypeGQLModel]:
    """
    Query purchase types with pagination.

    Examples:
    - All types: skip=0, limit=100
    - Root types only: filter by parent_id IS NULL
    - Equipment subtree: filter by path LIKE '/ROOT/EQUIPMENT/%'
    """
    resolver = PageResolver[PurchaseTypeGQLModel](whereType=None)
    result = await resolver(info, skip=skip, limit=limit)
    return result


@strawberry.type(description="Purchase type queries")
class PurchaseTypeQuery:
    """Query interface for purchase types."""

    purchase_type_by_id = purchase_type_by_id
    purchase_type_page = purchase_type_page


###########################################################################################################################
#
# Mutation definitions (to be implemented)
#
###########################################################################################################################

# Note: Add mutations for insert/update/delete when needed
# @strawberry.interface(description="Purchase type mutations")
# class PurchaseTypeMutation:
#     @strawberry.mutation(description="Insert new purchase type")
#     async def purchase_type_insert(...) -> Union[PurchaseTypeGQLModel, InsertError]:
#         ...
#
#     @strawberry.mutation(description="Update purchase type")
#     async def purchase_type_update(...) -> Union[PurchaseTypeGQLModel, UpdateError]:
#         ...
#
#     @strawberry.mutation(description="Delete purchase type")
#     async def purchase_type_delete(...) -> Union[PurchaseTypeGQLModel, DeleteError]:
#         ...


