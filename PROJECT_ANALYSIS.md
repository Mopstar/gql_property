# Complete Project Analysis - GQL Property Management System

## Executive Summary

**Project Type**: GraphQL-based Purchase/Event Management System with Advanced RBAC  
**Tech Stack**: Strawberry GraphQL, FastAPI, PostgreSQL, Docker, Apollo Federation  
**Primary Purpose**: Multi-tenant property/purchase request management with hierarchical group permissions  
**Key Innovation**: Creator ownership + role-based access with hierarchical group inheritance  
**Deployment**: Docker Compose orchestrating 8 microservices  

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                               │
│  - Web browsers, Mobile apps, API consumers                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              FRONTEND (Port 3000)                               │
│  - React/Next.js authentication UI                              │
│  - User login/registration                                       │
│  - Bearer token generation                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│          APOLLO GATEWAY (Port 3001)                             │
│  - Federation router                                             │
│  - Query planning & execution                                    │
│  - Schema composition from multiple subgraphs                    │
└────────┬───────────────┴────────────────────┬───────────────────┘
         │                                    │
         │                                    │
┌────────▼────────────────────┐   ┌──────────▼──────────────────┐
│  MAIN SERVICE (Port 8000)   │   │  GQL_UG (Port 33001)        │
│  - Purchase management       │   │  - User management          │
│  - Event management          │   │  - Group hierarchy          │
│  - Authorization logic       │   │  - Role assignments         │
│  - Creator ownership         │   │  - Membership tracking      │
│  - RBAC enforcement          │   │                             │
└────────┬────────────────────┘   └──────────┬──────────────────┘
         │                                    │
         │                                    │
┌────────▼─────────────┐         ┌───────────▼─────────────────┐
│  postgres_credentials│         │  postgres_gql               │
│  - Auth data          │         │  - User/Group data          │
│  - Session storage    │         │  - systemdata.rnd.json      │
└──────────────────────┘         └─────────────────────────────┘
```

### Service Topology

| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| **frontend** | 3000 | Authentication UI | postgres_credentials |
| **apollo** | 3001 | Federation gateway | main service, gql_ug |
| **main service** | 8000 | Purchase/Event API (THIS PROJECT) | postgres_credentials, gql_ug |
| **gql_ug** | 33001 | User/Group service | postgres_gql |
| **proxy** | 8010 | Reverse proxy | apollo |
| **analytics** | 8020 | Analytics service | - |
| **pgadmin** | 5050 | DB admin UI | postgres_gql, postgres_credentials |
| **postgres_gql** | 5432 | Primary database | - |
| **postgres_credentials** | 5433 | Auth database | - |

---

## 📂 Project Structure

```
gql_property/
├── main.py                          # FastAPI entry point + context setup
├── docker-compose.debug.yml         # Full stack orchestration
├── environment.txt                  # Environment configuration
├── requirements.txt                 # Python dependencies
├── systemdata.rnd.json             # Test data (152 groups, 1720 users, 159 roles)
│
├── src/                             # Main application code
│   ├── DBDefinitions/               # SQLAlchemy ORM models
│   │   ├── BaseModel.py            # Base entity with RBAC fields
│   │   ├── purchasemodel.py        # Purchase entity (138 lines)
│   │   ├── EventDBModel.py         # Event entity
│   │   ├── EventInvitationModel.py # Event invitations
│   │   └── uuid.py                 # UUID utilities
│   │
│   ├── GraphTypeDefinitions/        # Strawberry GraphQL schema
│   │   ├── authz_extensions.py     # ⭐ Authorization system (773 lines)
│   │   ├── BaseGQLModel.py         # Base GraphQL type
│   │   ├── PurchaseGQLModel.py     # Purchase queries/mutations (435 lines)
│   │   ├── EventGQLModel.py        # Event queries/mutations
│   │   ├── UserGQLModel.py         # User federation extension
│   │   ├── mutation.py             # Root mutation aggregation
│   │   ├── query.py                # Root query aggregation
│   │   └── TimeUnit.py             # Custom scalar types
│   │
│   ├── Dataloaders/                 # DataLoader pattern for N+1 prevention
│   │   └── __init__.py
│   │
│   ├── Utils/                       # Utility functions
│   │   ├── explain_query.py        # SQL query explanation
│   │   ├── gql_client.py           # GraphQL client helper
│   │   └── GraphQLQueryBuilder.py  # Query builder utilities
│   │
│   └── Htmls/                       # Static HTML tools
│       ├── livedata.html           # GraphQL playground
│       ├── liveschema.html         # Schema explorer
│       ├── tests.html              # Test UI
│       └── voyager.html            # GraphQL Voyager
│
├── DBDefinitions/                   # Legacy DB definitions (deprecated)
├── GraphTypeDefinitions/            # Legacy GQL definitions (deprecated)
│
├── tests/                           # Test suite
│   ├── test_purchases.py           # Purchase tests
│   ├── test_gt_definitions.py      # GraphQL type tests
│   ├── test_dbdefinitions.py       # DB model tests
│   └── test_dataloaders.py         # DataLoader tests
│
├── proxy/                           # Nginx reverse proxy
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
└── Documentation/                   # Project documentation
    ├── CREATOR_OWNERSHIP_GUIDE.md   # Authorization system guide
    ├── TROUBLESHOOTING_EMPTY_ROLES.md # Docker/UG debugging
    ├── TEST_QUERIES.md              # GraphQL test queries
    ├── QUICK_START_AUTH.md          # Quick auth guide
    └── .copilot-instructions.md     # This AI's instruction manual
```

---

## 🔒 Authorization System (Deep Dive)

### File: `src/GraphTypeDefinitions/authz_extensions.py` (773 lines)

This is the **MOST CRITICAL** file in the system. It implements a sophisticated 3-tier authorization model.

#### Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│              Strawberry Permission Extensions                    │
│  (Execute BEFORE resolver, can block access)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐  ┌──────────▼──────────┐  ┌──────▼─────────┐
│ LoadData      │  │ Ownership           │  │ UserRole       │
│ Extension     │  │ Permission          │  │ Provider       │
│               │  │ Extension           │  │ Extension      │
│ (Loads entity)│  │ (Checks access)     │  │ (Loads roles)  │
└───────────────┘  └─────────────────────┘  └────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
              ┌─────▼───┐ ┌───▼────┐ ┌─▼────────┐
              │Creator  │ │Root    │ │Group     │
              │Owner?   │ │Admin?  │ │Role?     │
              └─────────┘ └────────┘ └──────────┘
```

#### Key Functions & Logic

##### 1. `OwnershipPermissionExtension.resolve_async()` (Lines ~240-350)
**Purpose**: Main authorization gate for all protected operations

**Authorization Checks**:
```python
# CHECK 1: Creator Ownership
if user_id == entity.createdby_id:
    return ALLOW  # Permanent access

# CHECK 2: Root Admin
if user has admin role in group with mastergroupId=NULL:
    return ALLOW  # Universal access

# CHECK 3: Group Role
if user has required_role in entity.rbacobject_id OR parent_groups:
    return ALLOW  # Hierarchical access

# OTHERWISE:
return DENY
```

**Critical Code Pattern**:
```python
async def resolve_async(
    self,
    next_: typing.Callable,
    source: typing.Any,
    info: Info,
    **kwargs: typing.Any,
) -> typing.Any:
    # Extract context
    user_id = info.context.get('user', {}).get('id')
    user_roles = info.context.get('user', {}).get('roles', [])
    
    # Load entity (if update/delete operation)
    entity = await self._load_entity(source, info, kwargs)
    
    # CHECK 1: Creator ownership
    if entity and getattr(entity, 'createdby_id', None) == user_id:
        return await next_(source, info, **kwargs)
    
    # CHECK 2: Root admin
    if await check_root_admin(info, user_roles):
        return await next_(source, info, **kwargs)
    
    # CHECK 3: Group permissions
    rbacobject_id = getattr(entity, 'rbacobject_id', None) or kwargs.get('rbacobject_id')
    if rbacobject_id and user_roles:
        accessible_groups = await get_accessible_groups(info, user_roles, self.required_roles)
        if str(rbacobject_id) in [str(g) for g in accessible_groups]:
            return await next_(source, info, **kwargs)
    
    # DENY
    raise PermissionDenied(...)
```

##### 2. `get_accessible_groups()` (Lines ~487-513)
**Purpose**: Calculate which groups user can access based on roles

**Logic**:
```python
accessible = []
for role in user_roles:
    if role.roletype.name in required_roles:
        # Add the group where user has role
        accessible.append(role.group.id)
        
        # Add ALL child groups (hierarchical inheritance)
        children = await get_group_children(info, role.group.id)
        accessible.extend(children)

return list(set(accessible))  # Deduplicate
```

**Example**:
```
User is admin in "Fakulta" (Faculty)
├── Accessible groups:
│   ├── Fakulta (direct role)
│   ├── Katedra 1 (child)
│   ├── Katedra 2 (child)
│   └── Lab under Katedra 1 (grandchild)
```

##### 3. `get_group_children()` (Lines ~416-465)
**Purpose**: Recursively fetch all descendant groups

**GraphQL Query**:
```graphql
query($id: UUID!) {
  groupById(id: $id) {
    id
    subgroups {
      id
      subgroups {
        id
        subgroups { id }
      }
    }
  }
}
```

**Recursion Pattern**:
```python
def extract_ids(group):
    ids = []
    for subgroup in group.get('subgroups', []):
        ids.append(subgroup['id'])
        ids.extend(extract_ids(subgroup))  # Recursive call
    return ids
```

##### 4. `check_root_admin()` (Lines ~467-485)
**Purpose**: Identify users with universal access

**Detection Logic**:
```python
for role in user_roles:
    if role.roletype.name in ADMIN_ROLES:
        if role.group.mastergroupId is None:
            return True  # Admin in root group = root admin
return False
```

**Group Hierarchy**:
```
Univerzita (mastergroupId=NULL) ← Root group
└── Fakulta (mastergroupId=Univerzita)
    └── Katedra (mastergroupId=Fakulta)
```

##### 5. `filter_by_permissions()` (Lines ~597-665)
**Purpose**: Filter entity lists by user permissions

**Use Case**: Query endpoints that return lists (e.g., `purchasePage`)

**Algorithm**:
```python
filtered = []
for entity in entities:
    # Check 1: User created it
    if entity.createdby_id == user_id:
        filtered.append(entity)
        continue
    
    # Check 2: User has role in entity's group
    if entity.rbacobject_id in accessible_groups:
        filtered.append(entity)
        continue
    
    # Otherwise: skip (deny access)

return filtered
```

#### Extension Factories

These functions create standardized permission pipelines:

##### `create_insert_permissions()` (Lines ~674-697)
```python
def create_insert_permissions(error_type, model_type, required_roles=EDITOR_ROLES):
    return [
        PermissionFilterExtension(error_type),           # Filter kwargs (executes LAST)
        OwnershipPermissionExtension(required_roles),    # Check permissions
        UserRoleProviderExtension(),                     # Load user roles
        AutoGroupAssignmentExtension(),                  # Auto-assign rbacobject_id
    ]
```

**Pipeline Order** (executes right-to-left):
```
1. AutoGroupAssignmentExtension → Sets rbacobject_id if missing
2. UserRoleProviderExtension → Loads roles from UG service
3. OwnershipPermissionExtension → Checks if user can insert
4. PermissionFilterExtension → Validates/filters input
```

##### `create_update_permissions()` (Lines ~699-717)
```python
def create_update_permissions(error_type, model_type, required_roles=EDITOR_ROLES):
    return [
        PermissionFilterExtension(error_type),
        OwnershipPermissionExtension(required_roles, model_type=model_type),
        UserRoleProviderExtension(),
        LoadDataExtension(model_type),  # Load existing entity
    ]
```

##### `create_delete_permissions()` (Lines ~719-737)
```python
def create_delete_permissions(error_type, model_type, required_roles=ADMIN_ROLES):
    return [
        PermissionFilterExtension(error_type),
        OwnershipPermissionExtension(required_roles, model_type=model_type),
        UserRoleProviderExtension(),
        LoadDataExtension(model_type),
    ]
```

### Role Definitions (Lines ~35-40)

```python
VIEWER_ROLES = ['viewer', 'pozorovatel', 'reader', 'čitateľ']
EDITOR_ROLES = ['editor', 'editor', 'writer', 'pisateľ']  
ADMIN_ROLES = ['administrator', 'administrátor', 'admin']
```

**Internationalization**: Supports English + Slovak role names

---

## 🗄️ Database Models

### Base Model (`src/DBDefinitions/BaseModel.py`)

**Key RBAC Fields**:
```python
class BaseModel:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # RBAC Fields
    createdby_id: Mapped[UUID] = mapped_column(
        comment="Creator user ID - for permanent ownership"
    )
    rbacobject_id: Mapped[UUID] = mapped_column(
        comment="Group ID - for role-based permissions"
    )
    
    # Audit fields
    created: Mapped[datetime] = mapped_column(default=datetime.now)
    lastchange: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
    changedby_id: Mapped[UUID] = mapped_column(nullable=True)
    valid: Mapped[bool] = mapped_column(default=True)
```

### Purchase Model (`src/DBDefinitions/purchasemodel.py`)

```python
class PurchaseModel(BaseModel):
    __tablename__ = "purchases_evolution"
    
    # Hierarchical structure
    path: Mapped[str]  # Materialized path (e.g., "/123/456/")
    masterpurchase_id: Mapped[UUID] = ForeignKey("purchases_evolution.id")
    
    # Purchase data
    name: Mapped[str]
    reason: Mapped[str]
    description: Mapped[str]
    status: Mapped[str]  # pending, approved, rejected, completed
    
    # Workflow
    requester_id: Mapped[UUID]
    approver_id: Mapped[UUID]
    submitted: Mapped[datetime]
    approved: Mapped[datetime]
    
    # Financial
    totalCost: Mapped[float]
    
    # Relationships
    items: Mapped[List["PurchaseItemModel"]] = relationship(back_populates="purchase")
    subpurchases: Mapped[List["PurchaseModel"]] = relationship(...)
```

### Purchase Item Model

```python
class PurchaseItemModel(BaseModel):
    __tablename__ = "purchase_items"
    
    purchase_id: Mapped[UUID] = ForeignKey("purchases_evolution.id")
    
    name: Mapped[str]
    description: Mapped[str]
    quantity: Mapped[int]
    price: Mapped[float]
    totalPrice: Mapped[float]  # quantity * price
    
    # Relationships
    purchase: Mapped["PurchaseModel"] = relationship(back_populates="items")
```

---

## 🌐 GraphQL Schema

### Purchase GraphQL Model (`src/GraphTypeDefinitions/PurchaseGQLModel.py`)

#### Type Definition (Lines ~68-180)

```python
@strawberry.federation.type(
    description="Purchase request entity",
    keys=["id"]
)
class PurchaseGQLModel(BaseGQLModel):
    
    # Basic fields
    path: Optional[str]
    name: Optional[str]
    reason: Optional[str]
    description: Optional[str]
    status: Optional[str]
    
    # Relationships
    @strawberry.field(permission_classes=[OnlyForAuthentized])
    async def createdby(self, info: Info) -> Optional[UserGQLModel]:
        return await UserGQLModel.load_with_loader(info, id=self.createdby_id)
    
    @strawberry.field(permission_classes=[OnlyForAuthentized])
    async def items(self, info: Info) -> List[PurchaseItemGQLModel]:
        loader = getLoadersFromInfo(info).PurchaseItemModel
        result = await loader.filter_by(purchase_id=self.id)
        return result
    
    @strawberry.field(permission_classes=[OnlyForAuthentized])
    async def subpurchases(self, info: Info) -> List["PurchaseGQLModel"]:
        loader = self.getLoader(info)
        result = await loader.filter_by(masterpurchase_id=self.id)
        return result
```

#### Queries (Lines ~257-294)

```python
class PurchaseQuery:
    
    @strawberry.field(
        description="Get a purchase by its id (filtered by permissions)",
        permission_classes=[OnlyForAuthentized]
    )
    async def purchase_by_id(
        self,
        info: Info,
        id: UUID
    ) -> Optional[PurchaseGQLModel]:
        purchase = await PurchaseGQLModel.load_with_loader(info, id=id)
        if purchase is None:
            return None
        
        # Filter by permissions
        filtered = await filter_by_permissions(
            info, [purchase], required_roles=VIEWER_ROLES
        )
        return filtered[0] if filtered else None
    
    @strawberry.field(
        description="Get purchases (filtered by permissions)",
        permission_classes=[OnlyForAuthentized]
    )
    async def purchase_page(
        self, 
        info: Info, 
        skip: int = 0, 
        limit: int = 10
    ) -> List[PurchaseGQLModel]:
        resolver = PageResolver[PurchaseGQLModel](whereType=PurchaseInputFilter)
        all_results = await resolver(self, info, skip=skip, limit=limit)
        
        # CRITICAL: Filter by user permissions
        filtered_results = await filter_by_permissions(
            info, all_results, required_roles=VIEWER_ROLES
        )
        return filtered_results
```

#### Mutations (Lines ~310-400)

```python
@strawberry.input(description="Insert Purchase")
class PurchaseInsertGQLModel(TreeInputStructureMixin):
    masterpurchase_id: Optional[UUID] = None
    name: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = "pending"
    # ...

@strawberry.input(description="Update Purchase")  
class PurchaseUpdateGQLModel:
    id: UUID
    name: Optional[str] = strawberry.UNSET
    reason: Optional[str] = strawberry.UNSET
    # ...

class PurchaseMutation:
    
    @strawberry.mutation(
        description="Insert new purchase",
        extensions=[
            *create_insert_permissions(
                InsertError[PurchaseGQLModel],
                PurchaseGQLModel, 
                EDITOR_ROLES
            )
        ]
    )
    async def purchase_insert(
        self, info: Info, purchase: PurchaseInsertGQLModel
    ) -> Union[PurchaseGQLModel, InsertError[PurchaseGQLModel]]:
        return await Insert[PurchaseGQLModel].handle(info, purchase)
    
    @strawberry.mutation(
        description="Update purchase",
        extensions=[
            *create_update_permissions(
                UpdateError[PurchaseGQLModel],
                PurchaseGQLModel,
                EDITOR_ROLES
            )
        ]
    )
    async def purchase_update(
        self, info: Info, purchase: PurchaseUpdateGQLModel
    ) -> Union[PurchaseGQLModel, UpdateError[PurchaseGQLModel]]:
        return await Update[PurchaseGQLModel].handle(info, purchase)
    
    @strawberry.mutation(
        description="Delete purchase",
        extensions=[
            *create_delete_permissions(
                DeleteError[PurchaseGQLModel],
                PurchaseGQLModel,
                ADMIN_ROLES
            )
        ]
    )
    async def purchase_delete(
        self, info: Info, id: UUID
    ) -> Union[PurchaseGQLModel, DeleteError[PurchaseGQLModel]]:
        return await Delete[PurchaseGQLModel].handle(info, id)
```

---

## 🔧 FastAPI Application (`main.py`)

### Context Setup (Lines ~100-250)

**Most Important Function**:
```python
async def get_context(request: Request) -> dict:
    """
    Create GraphQL context for each request.
    
    Extracts user from Bearer token and fetches roles from UG service.
    """
    # Extract Bearer token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token_data = json.loads(auth_header[7:])  # Remove "Bearer "
        user_id = token_data.get('id')
        username = token_data.get('username')
    
    # Initialize UG client
    async def ug_client(query: str, variables: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GQLUG_ENDPOINT_URL,
                json={'query': query, 'variables': variables}
            )
            return response.json()
    
    # Fetch user roles from UG service
    user_roles = []
    if user_id:
        resp = await ug_client('''
            query($userId: UUID!) {
                userById(id: $userId) {
                    id
                    roles {
                        id
                        roletype { id name }
                        group { 
                            id 
                            name 
                            mastergroupId 
                        }
                    }
                }
            }
        ''', {'userId': user_id})
        
        user_data = resp.get('data', {}).get('userById', {})
        user_roles = user_data.get('roles', [])
    
    # Build context
    return {
        'user': {
            'id': user_id,
            'username': username,
            'roles': user_roles
        },
        'ug_client': ug_client,
        'request': request
    }
```

### GraphQL Router Setup (Lines ~250-280)

```python
# Create Strawberry schema
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True  # Enable GraphiQL playground
)

app.include_router(
    graphql_app,
    prefix="/gql",
    tags=["GraphQL"]
)
```

---

## 🐳 Docker Configuration

### docker-compose.debug.yml Structure

```yaml
version: '3.8'

services:
  # Primary Database (UG Service data)
  postgres_gql:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: example
      POSTGRES_DB: data
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  # Authentication Database
  postgres_credentials:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: example
      POSTGRES_DB: credentials
    ports:
      - "5433:5432"
  
  # User-Group Service
  gql_ug:
    image: hrbolek/gql_ug:latest
    ports:
      - "33001:8000"
    environment:
      POSTGRES_HOST: postgres_gql
      POSTGRES_PORT: 5432
      DEMO: "True"
      DEMODATA: "True"
    volumes:
      - ./systemdata.rnd.json:/app/systemdata.json  # ⚠️ CRITICAL MOUNT
    depends_on:
      - postgres_gql
  
  # Frontend (Authentication)
  frontend:
    image: hrbolek/gql_core_ui:latest
    ports:
      - "3000:3000"
    depends_on:
      - postgres_credentials
  
  # Apollo Federation Gateway
  apollo:
    image: apollo-router:latest
    ports:
      - "3001:80"
    depends_on:
      - gql_ug
  
  # Reverse Proxy
  proxy:
    build: ./proxy
    ports:
      - "8010:80"
    depends_on:
      - apollo
  
  # Analytics Service
  analytics:
    image: analytics:latest
    ports:
      - "8020:8000"
  
  # PgAdmin (DB Management UI)
  pgadmin:
    image: dpage/pgadmin4:latest
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
    depends_on:
      - postgres_gql
      - postgres_credentials

volumes:
  pgdata:
```

### Critical Volume Mount

**Line 120-121**:
```yaml
volumes:
  - ./systemdata.rnd.json:/app/systemdata.json
```

**Why Critical**: Without this mount, gql_ug service has no data and returns empty roles arrays, breaking all authorization.

---

## 📊 Data Model

### Test Data (`systemdata.rnd.json`)

**Statistics**:
- **Groups**: 152 (universities, faculties, departments, labs)
- **Users**: 1720 (students, staff, administrators)
- **Role Assignments**: 159 (explicit role grants)
- **Group Types**: 8 (university, faculty, department, lab, etc.)
- **Role Types**: 3 (viewer, editor, administrator)

**Sample Group Hierarchy**:
```json
{
  "groups": [
    {
      "id": "d75d64a4-bf5f-43c5-9c14-8fda7aff6c09",
      "name": "Univerzita",
      "abbr": "UNI",
      "mastergroup_id": null,  // Root group
      "grouptype_id": "cd49e152-610c-11ed-bf19-001a7dda7110"
    },
    {
      "id": "be0e6b0b-7e5f-4b7a-9d9b-daf3f23bcd7a",
      "name": "Fakulta vojenské matematiky",
      "abbr": "FVM",
      "mastergroup_id": "d75d64a4-bf5f-43c5-9c14-8fda7aff6c09",  // Parent: Univerzita
      "grouptype_id": "cd49e153-610c-11ed-bf19-001a7dda7110"
    },
    {
      "id": "f2f2d33c-38ee-4f31-9426-f364bc488032",
      "name": "Katedra teoretické matematiky",
      "abbr": "K101",
      "mastergroup_id": "be0e6b0b-7e5f-4b7a-9d9b-daf3f23bcd7a",  // Parent: Fakulta
      "grouptype_id": "cd49e155-610c-11ed-844e-001a7dda7110"
    }
  ]
}
```

**Sample Role Assignment**:
```json
{
  "roles": [
    {
      "id": "role-uuid-1",
      "user_id": "76dac14f-7114-4bb2-882d-0d762eab6f4a",  // Estera
      "group_id": "f2f2d33c-38ee-4f31-9426-f364bc488032",  // Katedra
      "roletype_id": "cd49e391-610c-11ed-9177-001a7dda7110"  // editor
    }
  ]
}
```

---

## 🧪 Testing Strategy

### Test Files

1. **`tests/test_purchases.py`** - Purchase functionality
2. **`tests/test_gt_definitions.py`** - GraphQL type tests
3. **`tests/test_dbdefinitions.py`** - Database model tests
4. **`tests/test_dataloaders.py`** - DataLoader efficiency tests

### Manual Testing Queries

**File**: `TEST_QUERIES.md`

#### Query as Specific User:
```graphql
# Authorization Header:
# Bearer {"id": "76dac14f-7114-4bb2-882d-0d762eab6f4a", "username": "Estera.Luckova@world.com"}

query TestEsteraAccess {
  purchasePage {
    id
    name
    status
    createdby {
      id
      fullname
    }
    rbacobjectId
  }
}
```

#### Verify User Roles:
```graphql
query CheckMyRoles {
  me {
    id
    fullname
    email
    roles {
      id
      roletype {
        id
        name
      }
      group {
        id
        name
        mastergroupId
        subgroups {
          id
          name
        }
      }
    }
  }
}
```

#### Test Creator Ownership:
```graphql
# Create as Estera
mutation {
  purchaseInsert(purchase: {
    name: "Test Purchase"
    reason: "Testing creator ownership"
    status: "pending"
  }) {
    ... on PurchaseGQLModel {
      id
      name
      createdby { id fullname }
      rbacobjectId
    }
    ... on InsertError {
      msg
    }
  }
}

# Try to access as different user (should be denied)
# Change Authorization header to Oliver
query {
  purchaseById(id: "uuid-from-above") {
    id
    name
  }
}
```

---

## 🚀 Deployment & Operations

### Local Development

```powershell
# 1. Start Docker services
docker-compose -f docker-compose.debug.yml up -d

# 2. Wait for services to be healthy (30-60 seconds)
docker-compose -f docker-compose.debug.yml ps

# 3. Start development server
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --env-file environment.txt --reload

# 4. Access GraphiQL playground
# http://localhost:8000/gql
```

### Production Deployment

**Docker Compose** (recommended):
```bash
docker-compose -f docker-compose.yml up -d --scale main_service=3
```

**Kubernetes** (future):
```yaml
# k8s deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gql-property-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gql-property
  template:
    metadata:
      labels:
        app: gql-property
    spec:
      containers:
      - name: main
        image: gql-property:latest
        ports:
        - containerPort: 8000
        env:
        - name: GQLUG_ENDPOINT_URL
          value: "http://gql-ug-service:8000/gql"
```

### Monitoring

**Log Aggregation**:
```python
# main.py uses SysLog handler
SYSLOGHOST = os.getenv("SYSLOGHOST", "localhost:514")
handler = logging.handlers.SysLogHandler(
    address=(address, port),
    socktype=socket.SOCK_DGRAM
)
```

**Health Check Endpoint**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## 🔐 Security Considerations

### Current Protections

1. ✅ **Authorization at Resolver Level** - Permission extensions on every protected field
2. ✅ **Creator Ownership** - Permanent access to own content
3. ✅ **Hierarchical RBAC** - Group-based permissions with inheritance
4. ✅ **Root Admin Detection** - Special handling for top-level admins
5. ✅ **Entity Filtering** - Lists filtered by permissions
6. ✅ **Bearer Token Authentication** - User identity verification

### Potential Vulnerabilities & Mitigations

#### 1. Token Security
**Risk**: Bearer tokens in JSON format could be intercepted
**Mitigation**: 
```python
# TODO: Implement JWT with signature verification
import jwt
token = jwt.encode({'user_id': user_id}, SECRET_KEY, algorithm='HS256')
decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
```

#### 2. SQL Injection
**Status**: ✅ Protected by SQLAlchemy ORM
**Verification**:
```python
# All queries use parameterized statements
result = await session.execute(
    select(PurchaseModel).where(PurchaseModel.id == id)
)
```

#### 3. GraphQL Depth Attacks
**Risk**: Malicious queries with deep nesting
**Mitigation**:
```python
# TODO: Add query depth limiting
from strawberry.extensions import QueryDepthLimiter
schema = strawberry.Schema(
    query=Query,
    extensions=[QueryDepthLimiter(max_depth=10)]
)
```

#### 4. Rate Limiting
**Status**: ⚠️ Not implemented
**TODO**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.route("/gql")
@limiter.limit("100/minute")
async def graphql_endpoint():
    ...
```

---

## 📈 Performance Optimizations

### DataLoader Pattern

**Purpose**: Prevent N+1 query problems

**Implementation** (`src/Dataloaders/`):
```python
from uoishelpers.dataloaders import createIdLoader

async def createLoaders(asyncSessionMaker):
    return {
        'PurchaseModel': createIdLoader(asyncSessionMaker, PurchaseModel),
        'PurchaseItemModel': createIdLoader(asyncSessionMaker, PurchaseItemModel),
        'EventModel': createIdLoader(asyncSessionMaker, EventModel),
    }
```

**Usage in Resolvers**:
```python
@strawberry.field
async def items(self, info: Info) -> List[PurchaseItemGQLModel]:
    loader = getLoadersFromInfo(info).PurchaseItemModel
    # Batches multiple item requests into single query
    return await loader.filter_by(purchase_id=self.id)
```

### Database Indexing

**Critical Indexes** (`src/DBDefinitions/purchasemodel.py`):
```python
class PurchaseModel(BaseModel):
    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    createdby_id: Mapped[UUID] = mapped_column(index=True)  # Creator lookups
    rbacobject_id: Mapped[UUID] = mapped_column(index=True)  # Group filtering
    path: Mapped[str] = mapped_column(index=True)  # Hierarchical queries
```

### Connection Pooling

**Configuration** (`main.py`):
```python
engine = create_async_engine(
    connectionString,
    pool_size=20,          # Concurrent connections
    max_overflow=10,       # Additional connections under load
    pool_pre_ping=True,    # Verify connections before use
    echo=False             # Disable query logging in production
)
```

---

## 🛠️ Development Workflow

### Adding New Feature

1. **Define DB Model** (`src/DBDefinitions/`)
2. **Create GraphQL Type** (`src/GraphTypeDefinitions/`)
3. **Add Query/Mutation** with permission extensions
4. **Write Tests** (`tests/`)
5. **Update Documentation** (`.copilot-instructions.md`, relevant guides)
6. **Test Authorization** with multiple user roles
7. **Deploy**

### Code Review Checklist

- [ ] All mutations have appropriate permission extensions
- [ ] Queries use `filter_by_permissions()` for lists
- [ ] New entities include `createdby_id` and `rbacobject_id`
- [ ] Tests cover authorization scenarios
- [ ] Documentation updated
- [ ] No SQL injection vulnerabilities
- [ ] DataLoader used for N+1 prevention
- [ ] Hierarchical access tested (parent→child ✅, child→parent ❌)

---

## 📚 Key Takeaways

### What Makes This System Unique

1. **Dual Authorization Model**
   - Creator ownership (permanent)
   - + Group RBAC (hierarchical)
   - = Flexible yet secure

2. **Hierarchical Permission Inheritance**
   - Parent group admins manage child content
   - One-way flow prevents privilege escalation
   - Automatic group child discovery

3. **Federation Architecture**
   - User/Group service separate from business logic
   - Allows independent scaling
   - Clear separation of concerns

4. **Permission Extensions Pattern**
   - Reusable authorization components
   - Consistent across all operations
   - Easy to test and maintain

### Critical Success Factors

✅ **systemdata.rnd.json must be mounted** to gql_ug service  
✅ **Hierarchical access is one-way** (parent→child only)  
✅ **Creator ownership is permanent** (survives role changes)  
✅ **All entity lists must be filtered** by permissions  
✅ **Root admin is special** (admin in group with no parent)  

### Common Mistakes to Avoid

❌ Bypassing permission extensions  
❌ Adding implicit access without explicit roles  
❌ Forgetting to mount systemdata volume  
❌ Allowing child→parent access  
❌ Hardcoding user IDs  
❌ Not using DataLoaders (N+1 problems)  

---

## 🔮 Future Enhancements

### Planned Features

1. **Query Depth Limiting** - Prevent abuse
2. **Rate Limiting** - Per-user API limits
3. **JWT Token Signatures** - Enhanced security
4. **Caching Layer** - Redis for permission checks
5. **Audit Logging** - Track all authorization decisions
6. **GraphQL Subscriptions** - Real-time updates
7. **Fine-Grained Permissions** - Field-level access control

### Technical Debt

1. Legacy `DBDefinitions/` and `GraphTypeDefinitions/` folders (unused)
2. Materialized path not fully implemented in PurchaseModel
3. Missing integration tests for full authorization flows
4. No performance benchmarks

---

## 📞 Support & Resources

### Documentation Files
- `.copilot-instructions.md` - AI assistant guide
- `CREATOR_OWNERSHIP_GUIDE.md` - Authorization explanation
- `TROUBLESHOOTING_EMPTY_ROLES.md` - Docker debugging
- `TEST_QUERIES.md` - GraphQL examples

### External Resources
- [Strawberry GraphQL Docs](https://strawberry.rocks/)
- [Apollo Federation](https://www.apollographql.com/docs/federation/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

---

**Generated**: January 7, 2026  
**Project Version**: 1.0  
**Last Updated**: After removing implicit viewer access feature
