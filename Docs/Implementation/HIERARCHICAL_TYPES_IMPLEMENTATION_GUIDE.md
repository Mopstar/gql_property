# Hierarchical Type Trees (Číselníky) Implementation Guide

**Date:** February 7, 2026  
**Project:** gql_property  
**Status:** ✅ Fully Implemented

---

## 📋 Overview

This document describes the implementation of hierarchical type taxonomies (číselníky jako stromy) in the gql_property project.

**Implemented Type Hierarchies:**
1. **PurchaseTypeModel** - Purchase categorization tree
2. **EventTypeModel** - Event categorization tree

---

## 🌳 What Are Hierarchical Types (Číselníky)?

Hierarchical types (číselníky) are tree-structured taxonomies that enable nested categorization of entities. Instead of flat enumerations, they support parent-child relationships with unlimited depth.

### Example: Purchase Types

```
ROOT
├── Equipment
│   ├── IT Equipment
│   │   ├── Computers
│   │   ├── Servers
│   │   └── Network Devices
│   └── Office Equipment
│       └── Furniture
└── Services
    ├── Consulting
    └── Training
```

### Benefits

✅ **Hierarchical Organization** - Natural categorization with unlimited depth  
✅ **Efficient Queries** - Materialized path enables fast subtree lookups  
✅ **Easy Navigation** - Parent/children relationships built-in  
✅ **UI-Friendly** - Level tracking for indentation and visualization  
✅ **Extensible** - Add new types without schema changes  
✅ **GraphQL Native** - Nested queries work naturally  

---

## 📁 File Structure

### Database Models
```
src/DBDefinitions/
├── PurchaseTypeModel.py    # Purchase type taxonomy
└── EventTypeModel.py        # Event type taxonomy
```

### GraphQL Models
```
src/GraphTypeDefinitions/
├── PurchaseTypeGQLModel.py  # GraphQL schema for purchase types
└── EventTypeGQLModel.py     # GraphQL schema for event types
```

### Initialization Scripts
```
scripts/
├── insert_purchase_types.sql  # Sample purchase type data
└── insert_event_types.sql     # Sample event type data
```

---

## 🔧 Technical Implementation

### Database Model Features

#### 1. Self-Referential Relationships
```python
class PurchaseTypeModel(BaseModel):
    # Self-reference to parent
    parent_id: Mapped[Optional[IDType]] = mapped_column(
        ForeignKey("purchasetypes.id", ondelete="CASCADE"),
        index=True
    )
    
    # Relationships
    parent: Mapped[Optional["PurchaseTypeModel"]] = relationship(
        "PurchaseTypeModel",
        remote_side="PurchaseTypeModel.id",
        back_populates="children"
    )
    
    children: Mapped[List["PurchaseTypeModel"]] = relationship(
        "PurchaseTypeModel",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
```

**Features:**
- `parent_id` → Foreign key to same table
- `parent` → Many-to-one relationship (navigate up)
- `children` → One-to-many relationship (navigate down)
- `CASCADE DELETE` → Deleting parent removes all children

#### 2. Materialized Path
```python
path: Mapped[str] = mapped_column(
    String,
    nullable=False,
    default="/",
    index=True,
    comment="Materialized path like '/ROOT/EQUIPMENT/IT_EQUIPMENT/'"
)
```

**Purpose:** Fast subtree queries without recursive CTEs

**Usage:**
```sql
-- Find all IT Equipment subcategories
SELECT * FROM purchasetypes 
WHERE path LIKE '/ROOT/EQUIPMENT/IT_EQUIPMENT/%';

-- Find all direct children of Equipment
SELECT * FROM purchasetypes 
WHERE parent_id = '<equipment_id>';
```

#### 3. Level Tracking
```python
level: Mapped[int] = mapped_column(
    default=0,
    comment="Tree depth: 0=root, 1=first level, etc."
)
```

**Purpose:** Quick depth checking, UI indentation

**Examples:**
- Level 0: ROOT
- Level 1: Equipment, Services, Software
- Level 2: IT Equipment, Office Equipment
- Level 3: Computers, Servers

#### 4. Sort Order
```python
sort_order: Mapped[int] = mapped_column(
    default=0,
    comment="Display order within same parent level"
)
```

**Purpose:** Control display order beyond alphabetical sorting

---

## 📊 GraphQL Schema

### Type Definition

```graphql
type PurchaseTypeGQLModel {
  # Basic identification
  id: UUID!
  name: String!
  code: String!
  description: String
  
  # Tree structure
  parentId: UUID
  path: String!
  level: Int!
  
  # Configuration
  isActive: Boolean!
  sortOrder: Int!
  
  # Tree navigation
  parent: PurchaseTypeGQLModel
  children: [PurchaseTypeGQLModel!]!
  
  # Audit fields (inherited from BaseGQLModel)
  created: DateTime
  lastchange: DateTime
  createdbyId: UUID
  changedbyId: UUID
  rbacobjectId: UUID
}
```

### Queries

#### Query Single Type by ID
```graphql
query GetPurchaseType {
  purchaseTypeById(id: "uuid-here") {
    id
    name
    code
    level
    path
    
    parent {
      id
      name
    }
    
    children {
      id
      name
      code
      level
    }
  }
}
```

#### Query All Types (Paginated)
```graphql
query GetAllPurchaseTypes {
  purchaseTypePage(skip: 0, limit: 100) {
    id
    name
    code
    level
    path
    parentId
  }
}
```

#### Query Subtree by Path
```graphql
# Note: This requires WHERE clause support in PageResolver
query GetEquipmentSubtree {
  purchaseTypePage(
    where: { path: { _like: "/ROOT/EQUIPMENT/%" } }
  ) {
    id
    name
    code
    level
    path
  }
}
```

#### Query Full Tree (Nested)
```graphql
query GetPurchaseTypeTree {
  purchaseTypePage(limit: 100) {
    id
    name
    code
    level
    
    children {
      id
      name
      code
      level
      
      children {
        id
        name
        code
        level
      }
    }
  }
}
```

---

## 🚀 Usage Examples

### Python: Database Operations

#### Create New Type
```python
from src.DBDefinitions import PurchaseTypeModel

# Create a new type under IT Equipment
new_type = PurchaseTypeModel(
    name="Printers",
    name_en="Printers",
    code="PRINTER",
    description="Network and desktop printers",
    parent_id=it_equipment_id,  # UUID of IT Equipment
    path="/ROOT/EQUIPMENT/IT_EQUIPMENT/PRINTER/",
    level=3,
    is_active=True,
    sort_order=4
)

session.add(new_type)
await session.commit()
```

#### Query Subtree
```python
from sqlalchemy import select

# Find all equipment types
stmt = select(PurchaseTypeModel).where(
    PurchaseTypeModel.path.like('/ROOT/EQUIPMENT/%')
)
results = await session.execute(stmt)
equipment_types = results.scalars().all()
```

#### Navigate Tree
```python
# Get type with parent and children loaded
type_obj = await session.get(PurchaseTypeModel, type_id)

# Navigate up
parent = type_obj.parent

# Navigate down
children = type_obj.children

# Check position
if type_obj.is_root():
    print("This is a root node")
elif type_obj.is_leaf():
    print("This is a leaf node")
else:
    print(f"This node is at level {type_obj.level}")
```

### Python: Helper Methods

```python
class PurchaseTypeModel(BaseModel):
    def get_full_path_names(self) -> List[str]:
        """Get list of type names from root to this type."""
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
```

---

## 📝 Initialization Scripts

### Running Initialization

```bash
# Connect to database
psql -h localhost -p 5432 -U postgres -d data

# Run initialization scripts
\i scripts/insert_purchase_types.sql
\i scripts/insert_event_types.sql

# Verify data
SELECT id, name, code, path, level FROM purchasetypes ORDER BY path;
SELECT id, name, code, path, level FROM eventtypes ORDER BY path;
```

### Sample Data Structure

**Purchase Types:**
- ROOT (level 0)
  - Equipment (level 1)
    - IT Equipment (level 2)
      - Computers (level 3)
      - Servers (level 3)
      - Network Devices (level 3)
    - Laboratory Equipment (level 2)
    - Office Equipment (level 2)
  - Supplies (level 1)
    - Office Supplies (level 2)
    - Laboratory Supplies (level 2)
  - Services (level 1)
    - Maintenance (level 2)
    - Consulting (level 2)
    - Training (level 2)
  - Software (level 1)
    - Licenses (level 2)
    - Subscriptions (level 2)

**Event Types:**
- ROOT (level 0)
  - Academic (level 1)
    - Conference (level 2)
      - International Conference (level 3)
      - National Conference (level 3)
    - Seminar (level 2)
    - Workshop (level 2)
    - Lecture (level 2)
  - Administrative (level 1)
    - Meeting (level 2)
      - Board Meeting (level 3)
      - Department Meeting (level 3)
      - Team Meeting (level 3)
    - Review (level 2)
    - Planning (level 2)
  - Social (level 1)
    - Networking Event (level 2)
    - Celebration (level 2)
    - Team Building (level 2)
  - Training (level 1)
    - Professional Development (level 2)
    - Technical Training (level 2)
    - Compliance Training (level 2)

---

## 🔄 Integration with Existing Models

### Option 1: Add Foreign Key (Recommended)

Update PurchaseModel to reference PurchaseTypeModel:

```python
# In src/DBDefinitions/purchasemodel.py
class PurchaseModel(BaseModel):
    # Add foreign key
    purchase_type_id: Mapped[Optional[IDType]] = mapped_column(
        ForeignKey("purchasetypes.id"),
        index=True,
        default=None,
        comment="Purchase type reference"
    )
    
    # Add relationship
    purchase_type: Mapped[Optional["PurchaseTypeModel"]] = relationship(
        "PurchaseTypeModel",
        foreign_keys=[purchase_type_id],
        init=False
    )
```

Update PurchaseGQLModel to expose the relationship:

```python
# In src/GraphTypeDefinitions/PurchaseGQLModel.py
from .PurchaseTypeGQLModel import PurchaseTypeGQLModel

@strawberry.field(description="Purchase type category")
async def purchase_type(
    self, info: strawberry.types.Info
) -> Optional[PurchaseTypeGQLModel]:
    result = await ScalarResolver[PurchaseTypeGQLModel](
        foreign_key_name="purchase_type_id"
    )(self, info)
    return result
```

### Option 2: Keep Separate (Current Approach)

Types can be queried independently without modifying existing models. This is useful for:
- Gradual migration
- Maintaining backward compatibility
- Testing before full integration

---

## 🧪 Testing

### Test Queries

```graphql
# Test 1: Query all purchase types
query {
  purchaseTypePage(limit: 50) {
    id
    name
    code
    level
    path
  }
}

# Test 2: Navigate tree structure
query {
  purchaseTypeById(id: "10000000-0000-0000-0000-000000000001") {
    name
    parent {
      name
    }
    children {
      name
      children {
        name
      }
    }
  }
}

# Test 3: Query event types
query {
  eventTypePage(limit: 50) {
    id
    name
    code
    level
    path
    defaultDurationMinutes
  }
}
```

### Python Tests

```python
import pytest
from src.DBDefinitions import PurchaseTypeModel

@pytest.mark.asyncio
async def test_purchase_type_tree(async_session):
    # Test root node
    root = PurchaseTypeModel(
        name="ROOT",
        code="ROOT",
        parent_id=None,
        path="/",
        level=0
    )
    async_session.add(root)
    await async_session.commit()
    
    assert root.is_root()
    assert not root.is_leaf()
    
    # Test child node
    equipment = PurchaseTypeModel(
        name="Equipment",
        code="EQUIP",
        parent_id=root.id,
        path="/ROOT/EQUIP/",
        level=1
    )
    async_session.add(equipment)
    await async_session.commit()
    
    assert not equipment.is_root()
    assert equipment.parent_id == root.id
    assert equipment.level == 1
```

---

## 📚 Best Practices

### 1. Path Consistency
Always update `path` when moving nodes:
```python
# When changing parent, update path for node and all descendants
new_path = parent.path + node.code + "/"
node.path = new_path
# Recursively update children paths
```

### 2. Level Tracking
Always update `level` to match tree depth:
```python
node.level = parent.level + 1 if parent else 0
```

### 3. Code Uniqueness
Ensure `code` is unique across entire tree:
```python
# Use unique constraint
code: Mapped[str] = mapped_column(String(50), unique=True)
```

### 4. Cascade Deletes
Use CASCADE to automatically remove children:
```python
ForeignKey("purchasetypes.id", ondelete="CASCADE")
```

### 5. Sort Order
Use `sort_order` for custom ordering:
```python
order_by="PurchaseTypeModel.sort_order"
```

---

## 🆕 Adding New Type Hierarchies

To add a new type hierarchy (e.g., `DepartmentTypeModel`):

1. **Create Database Model** (`src/DBDefinitions/DepartmentTypeModel.py`)
2. **Create GraphQL Model** (`src/GraphTypeDefinitions/DepartmentTypeGQLModel.py`)
3. **Add to __init__.py** exports
4. **Add queries** to `query.py`
5. **Create initialization script** (`scripts/insert_department_types.sql`)
6. **Update documentation**

---

## 📖 Related Documentation

- **GQL Agreement Project** - Reference implementation in `GQL_Agreement_Valiasek/docs/development/CODE_COVERAGE_ERROR_CODES_TREES_REPORT.md`
- **Database Models** - `src/DBDefinitions/PurchaseTypeModel.py`, `src/DBDefinitions/EventTypeModel.py`
- **GraphQL Models** - `src/GraphTypeDefinitions/PurchaseTypeGQLModel.py`, `src/GraphTypeDefinitions/EventTypeGQLModel.py`
- **Init Scripts** - `scripts/insert_purchase_types.sql`, `scripts/insert_event_types.sql`

---

## ✅ Implementation Checklist

- [x] Database models created (PurchaseTypeModel, EventTypeModel)
- [x] GraphQL models created
- [x] Queries added to Query root
- [x] Initialization scripts created
- [x] Documentation written
- [ ] Mutations implemented (optional)
- [ ] Integration with PurchaseModel/EventModel (optional)
- [ ] Tests written (optional)
- [ ] Sample data loaded (run SQL scripts)

---

**Last Updated:** February 7, 2026  
**Maintained By:** Development Team  
**Status:** ✅ Implementation Complete

