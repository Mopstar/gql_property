"""
EventTypeGQLModel - GraphQL model for hierarchical event types
===============================================================

Exposes EventTypeModel through GraphQL API with tree navigation support.

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
from src.DBDefinitions import EventTypeModel

# Import for permission classes
from uoishelpers.resolvers import ScalarResolver, VectorResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized


@strawberry.federation.type(
    keys=["id"],
    description="Hierarchical event type taxonomy (číselník)"
)
class EventTypeGQLModel(BaseGQLModel):
    """
    Event type in hierarchical tree structure.

    Enables categorization like:
    - Academic → Conference → International Conference
    - Administrative → Meeting → Board Meeting
    - Social → Networking Event
    """

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return info.context["all"].get(EventTypeModel, None)

    # Basic fields
    id: IDType = strawberry.field(
        description="Unique identifier",
        permission_classes=[OnlyForAuthentized]
    )

    name: Optional[str] = strawberry.field(
        default=None,
        description="Type name (e.g., 'Conference')",
        permission_classes=[OnlyForAuthentized]
    )

    name_en: Optional[str] = strawberry.field(
        default=None,
        description="English name",
        permission_classes=[OnlyForAuthentized]
    )

    code: Optional[str] = strawberry.field(
        default=None,
        description="Short code (e.g., 'CONF')",
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
        description="Materialized path (e.g., '/ROOT/ACADEMIC/CONFERENCE/')",
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
        description="Whether this type can be selected for new events",
        permission_classes=[OnlyForAuthentized]
    )

    sort_order: Optional[int] = strawberry.field(
        default=None,
        description="Display order within same parent",
        permission_classes=[OnlyForAuthentized]
    )

    default_duration_minutes: Optional[int] = strawberry.field(
        default=None,
        description="Suggested event duration in minutes",
        permission_classes=[OnlyForAuthentized]
    )

    # Tree navigation - parent
    @strawberry.field(
        description="Parent type (one level up)",
        permission_classes=[OnlyForAuthentized]
    )
    async def parent(
        self, info: strawberry.types.Info
    ) -> Optional["EventTypeGQLModel"]:
        """Navigate to parent type."""
        result = await ScalarResolver[EventTypeGQLModel](
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
    ) -> List["EventTypeGQLModel"]:
        """Navigate to child types."""
        result = await VectorResolver[EventTypeGQLModel](
            foreign_key_name="parent_id"
        )(self, info)
        return result

    # Note: Add relationship to events when EventModel is updated
    # @strawberry.field(description="Events using this type")
    # async def events(self, info) -> List["EventGQLModel"]:
    #     result = await VectorResolver[EventGQLModel](
    #         foreign_key_name="event_type_id"
    #     )(self, info)
    #     return result


###########################################################################################################################
#
# Query definitions
#
###########################################################################################################################

from uoishelpers.resolvers import PageResolver

@strawberry.field(
    description="Get an event type by its ID",
    permission_classes=[OnlyForAuthentized]
)
async def event_type_by_id(
    info: strawberry.types.Info,
    id: IDType
) -> Optional[EventTypeGQLModel]:
    """Query single event type by ID."""
    result = await EventTypeGQLModel.load_with_loader(info, id=id)
    return result

@strawberry.field(
    description="Get all event types (paginated). Use path filter for subtrees.",
    permission_classes=[OnlyForAuthentized]
)
async def event_type_page(
    info: strawberry.types.Info,
    skip: int = 0,
    limit: int = 100
) -> List[EventTypeGQLModel]:
    """
    Query event types with pagination.

    Examples:
    - All types: skip=0, limit=100
    - Root types only: filter by parent_id IS NULL
    - Academic subtree: filter by path LIKE '/ROOT/ACADEMIC/%'
    """
    resolver = PageResolver[EventTypeGQLModel](whereType=None)
    result = await resolver(info, skip=skip, limit=limit)
    return result


@strawberry.type(description="Event type queries")
class EventTypeQuery:
    """Query interface for event types."""

    event_type_by_id = event_type_by_id
    event_type_page = event_type_page


###########################################################################################################################
#
# Mutation definitions (to be implemented)
#
###########################################################################################################################

# Note: Add mutations for insert/update/delete when needed
# @strawberry.interface(description="Event type mutations")
# class EventTypeMutation:
#     @strawberry.mutation(description="Insert new event type")
#     async def event_type_insert(...) -> Union[EventTypeGQLModel, InsertError]:
#         ...
#
#     @strawberry.mutation(description="Update event type")
#     async def event_type_update(...) -> Union[EventTypeGQLModel, UpdateError]:
#         ...
#
#     @strawberry.mutation(description="Delete event type")
#     async def event_type_delete(...) -> Union[EventTypeGQLModel, DeleteError]:
#         ...


