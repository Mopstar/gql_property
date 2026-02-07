"""
EventTypeModel - Hierarchical event type taxonomy
==================================================

Implements event types as a tree structure (číselník as tree).
Enables categorization of events for better organization.

Example hierarchy:
ROOT
├── ACADEMIC
│   ├── CONFERENCE
│   │   ├── INTERNATIONAL_CONFERENCE
│   │   ├── NATIONAL_CONFERENCE
│   │   └── REGIONAL_CONFERENCE
│   ├── SEMINAR
│   │   ├── RESEARCH_SEMINAR
│   │   └── EDUCATIONAL_SEMINAR
│   ├── WORKSHOP
│   │   ├── TECHNICAL_WORKSHOP
│   │   └── METHODOLOGICAL_WORKSHOP
│   └── LECTURE
│       ├── PUBLIC_LECTURE
│       └── GUEST_LECTURE
├── ADMINISTRATIVE
│   ├── MEETING
│   │   ├── BOARD_MEETING
│   │   ├── DEPARTMENT_MEETING
│   │   ├── TEAM_MEETING
│   │   └── PROJECT_MEETING
│   ├── REVIEW
│   │   ├── ANNUAL_REVIEW
│   │   ├── QUARTERLY_REVIEW
│   │   └── PROJECT_REVIEW
│   └── PLANNING
│       ├── STRATEGIC_PLANNING
│       └── OPERATIONAL_PLANNING
├── SOCIAL
│   ├── NETWORKING_EVENT
│   │   ├── RECEPTION
│   │   └── MIXER
│   ├── CELEBRATION
│   │   ├── GRADUATION
│   │   ├── ANNIVERSARY
│   │   └── AWARDS_CEREMONY
│   └── TEAM_BUILDING
└── TRAINING
    ├── PROFESSIONAL_DEVELOPMENT
    │   ├── SKILLS_TRAINING
    │   └── LEADERSHIP_TRAINING
    ├── TECHNICAL_TRAINING
    │   ├── SOFTWARE_TRAINING
    │   └── EQUIPMENT_TRAINING
    └── COMPLIANCE_TRAINING
        ├── SAFETY_TRAINING
        └── ETHICS_TRAINING

Database Design:
- Self-referential tree with parent_id
- Materialized path for efficient subtree queries
- Level tracking for tree depth
- Default duration in minutes for planning
- Cascade delete of children when parent deleted

Usage:
    # In EventModel, add:
    event_type_id: UUID = ForeignKey("eventtypes.id")
    event_type: Relationship["EventTypeModel"]
"""

import typing
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType


class EventTypeModel(BaseModel):
    """
    Hierarchical event type taxonomy (číselník as tree).

    Represents types of events in a tree structure allowing
    nested categorization (type -> subtype -> sub-subtype).

    Attributes:
        name: Type name (e.g., "Conference", "Board Meeting")
        name_en: English name for internationalization
        code: Short code (e.g., "CONF", "BOARD_MTG")
        description: Detailed explanation of this event type
        parent_id: Parent type ID (NULL for root types)
        path: Materialized path (e.g., "/ACADEMIC/CONFERENCE/INTERNATIONAL/")
        level: Tree depth (0 = root, 1 = first level, etc.)
        is_active: Whether this type can be selected for new events
        sort_order: Display order within same parent
        default_duration_minutes: Suggested duration for this event type

    Relationships:
        parent: Parent EventTypeModel (many-to-one)
        children: Child EventTypeModel list (one-to-many)
        events: Events using this type (one-to-many)

    Tree Operations:
        - Find all descendants: WHERE path LIKE parent.path || '%'
        - Find ancestors: Parse path and load each level
        - Level determination: COUNT(/) in path
        - Leaf nodes: WHERE NOT EXISTS (SELECT 1 FROM children)
    """

    __tablename__ = "eventtypes"

    # Tree structure attribute names for TreeInputStructureMixin
    path_attribute_name = "path"
    parent_attribute_name = "parent"
    parent_id_attribute_name = "parent_id"
    children_attribute_name = "children"

    # Type identification
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        default="",
        comment="Type name (e.g., 'Conference', 'Board Meeting')"
    )

    name_en: Mapped[typing.Optional[str]] = mapped_column(
        String,
        default=None,
        comment="English name for internationalization"
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        default="",
        comment="Unique short code (e.g., 'CONF', 'BOARD_MTG')"
    )

    description: Mapped[typing.Optional[str]] = mapped_column(
        String,
        default=None,
        comment="Detailed explanation of this event type"
    )

    # Tree structure
    parent_id: Mapped[typing.Optional[IDType]] = mapped_column(
        ForeignKey("eventtypes.id", ondelete="CASCADE"),
        index=True,
        default=None,
        comment="Parent type ID (NULL for root types)"
    )

    path: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="/",
        index=True,
        comment="Materialized path like '/ROOT/ACADEMIC/CONFERENCE/'"
    )

    level: Mapped[int] = mapped_column(
        default=0,
        comment="Tree depth: 0=root, 1=first level, etc."
    )

    # Configuration
    is_active: Mapped[bool] = mapped_column(
        default=True,
        comment="Whether this type can be selected for new events"
    )

    sort_order: Mapped[int] = mapped_column(
        default=0,
        comment="Display order within same parent level"
    )

    default_duration_minutes: Mapped[typing.Optional[int]] = mapped_column(
        Integer,
        default=None,
        comment="Suggested event duration in minutes (e.g., 60 for 1-hour meeting)"
    )

    # Relationships
    parent: Mapped[typing.Optional["EventTypeModel"]] = relationship(
        "EventTypeModel",
        remote_side="EventTypeModel.id",
        back_populates="children",
        foreign_keys=[parent_id],
        init=False
    )

    children: Mapped[typing.List["EventTypeModel"]] = relationship(
        "EventTypeModel",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="EventTypeModel.sort_order",
        init=False
    )

    # Note: Relationship to EventModel will be added when EventModel is updated
    # events: Mapped[typing.List["EventModel"]] = relationship(...)

    def __repr__(self):
        return f"<EventType(code={self.code}, name={self.name}, path={self.path})>"

    def get_full_path_names(self) -> typing.List[str]:
        """
        Get list of type names from root to this type.

        Returns:
            ["Academic", "Conference", "International Conference"] for a leaf node
        """
        # Parse path like "/ROOT/ACADEMIC/CONFERENCE/" -> ["ROOT", "ACADEMIC", "CONFERENCE"]
        parts = [p for p in self.path.split("/") if p]
        return parts

    def is_leaf(self) -> bool:
        """Check if this is a leaf node (has no children)."""
        return len(self.children) == 0

    def is_root(self) -> bool:
        """Check if this is a root node (has no parent)."""
        return self.parent_id is None

    def get_ancestors_count(self) -> int:
        """Get number of ancestors (tree depth)."""
        return self.level

