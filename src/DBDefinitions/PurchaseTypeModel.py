"""
PurchaseTypeModel - Hierarchical purchase type taxonomy
========================================================

Implements purchase types as a tree structure (číselník as tree).
Enables categorization of purchases for better organization.

Example hierarchy:
ROOT
├── EQUIPMENT
│   ├── IT_EQUIPMENT
│   │   ├── COMPUTERS
│   │   ├── SERVERS
│   │   └── NETWORK_DEVICES
│   ├── LABORATORY_EQUIPMENT
│   │   ├── MICROSCOPES
│   │   └── MEASUREMENT_DEVICES
│   └── OFFICE_EQUIPMENT
│       ├── FURNITURE
│       └── PRINTERS
├── SUPPLIES
│   ├── OFFICE_SUPPLIES
│   │   ├── PAPER
│   │   └── STATIONERY
│   └── LABORATORY_SUPPLIES
│       ├── CHEMICALS
│       └── CONSUMABLES
├── SERVICES
│   ├── MAINTENANCE
│   │   ├── IT_MAINTENANCE
│   │   └── FACILITY_MAINTENANCE
│   ├── CONSULTING
│   └── TRAINING
└── SOFTWARE
    ├── LICENSES
    │   ├── OFFICE_SOFTWARE
    │   └── DEVELOPMENT_TOOLS
    └── SUBSCRIPTIONS
        ├── CLOUD_SERVICES
        └── DATABASE_SERVICES

Database Design:
- Self-referential tree with parent_id
- Materialized path for efficient subtree queries
- Level tracking for tree depth
- Name uniqueness within same parent
- Cascade delete of children when parent deleted

Tree Operations:
- Find all descendants: WHERE path LIKE parent.path || '%'
- Find ancestors: Parse path and load each level
- Level determination: COUNT(/) in path
- Leaf nodes: WHERE NOT EXISTS (SELECT 1 FROM children)

Usage:
    # In PurchaseModel, add:
    purchase_type_id: UUID = ForeignKey("purchasetypes.id")
    purchase_type: Relationship["PurchaseTypeModel"]
"""

import typing
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType


class PurchaseTypeModel(BaseModel):
    """
    Hierarchical purchase type taxonomy (číselník as tree).

    Represents types of purchases in a tree structure allowing
    nested categorization (type -> subtype -> sub-subtype).

    Attributes:
        name: Type name (e.g., "Equipment", "IT Equipment", "Computers")
        name_en: English name for internationalization
        code: Short code (e.g., "EQUIP", "IT_EQUIP", "COMP")
        description: Detailed explanation of this purchase type
        parent_id: Parent type ID (NULL for root types)
        path: Materialized path (e.g., "/EQUIPMENT/IT_EQUIPMENT/COMPUTERS/")
        level: Tree depth (0 = root, 1 = first level, etc.)
        is_active: Whether this type can be selected for new purchases
        sort_order: Display order within same parent

    Relationships:
        parent: Parent PurchaseTypeModel (many-to-one)
        children: Child PurchaseTypeModel list (one-to-many)
        purchases: Purchases using this type (one-to-many)

    Tree Operations:
        - Find all descendants: WHERE path LIKE parent.path || '%'
        - Find ancestors: Parse path and load each level
        - Level determination: COUNT(/) in path
        - Leaf nodes: WHERE NOT EXISTS (SELECT 1 FROM children)
    """

    __tablename__ = "purchasetypes"

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
        comment="Type name (e.g., 'IT Equipment', 'Computers')"
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
        comment="Unique short code (e.g., 'IT_EQUIP', 'COMP')"
    )

    description: Mapped[typing.Optional[str]] = mapped_column(
        String,
        default=None,
        comment="Detailed explanation of this purchase type"
    )

    # Tree structure
    parent_id: Mapped[typing.Optional[IDType]] = mapped_column(
        ForeignKey("purchasetypes.id", ondelete="CASCADE"),
        index=True,
        default=None,
        comment="Parent type ID (NULL for root types)"
    )

    path: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="/",
        index=True,
        comment="Materialized path like '/ROOT/EQUIPMENT/IT_EQUIPMENT/'"
    )

    level: Mapped[int] = mapped_column(
        default=0,
        comment="Tree depth: 0=root, 1=first level, etc."
    )

    # Configuration
    is_active: Mapped[bool] = mapped_column(
        default=True,
        comment="Whether this type can be selected for new purchases"
    )

    sort_order: Mapped[int] = mapped_column(
        default=0,
        comment="Display order within same parent level"
    )

    # Relationships
    parent: Mapped[typing.Optional["PurchaseTypeModel"]] = relationship(
        "PurchaseTypeModel",
        remote_side="PurchaseTypeModel.id",
        back_populates="children",
        foreign_keys=[parent_id],
        init=False
    )

    children: Mapped[typing.List["PurchaseTypeModel"]] = relationship(
        "PurchaseTypeModel",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="PurchaseTypeModel.sort_order",
        init=False
    )

    # Note: Relationship to PurchaseModel will be added when PurchaseModel is updated
    # purchases: Mapped[typing.List["PurchaseModel"]] = relationship(...)

    def __repr__(self):
        return f"<PurchaseType(code={self.code}, name={self.name}, path={self.path})>"

    def get_full_path_names(self) -> typing.List[str]:
        """
        Get list of type names from root to this type.

        Returns:
            ["Equipment", "IT Equipment", "Computers"] for a leaf node
        """
        # Parse path like "/ROOT/EQUIPMENT/IT_EQUIPMENT/" -> ["ROOT", "EQUIPMENT", "IT_EQUIPMENT"]
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

