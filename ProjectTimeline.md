# Timeline of commits
This document summarizes the evolution of the project and related infrastructure.

___

## Timeline of commits and changes

### 1. Initial project setup and Purchase model definition
**October 23, 2025**  
**Commit:** `41269c53` — “1. commit”

- Introduced initial Purchase backend pieces and adjusted development configuration.
- Files changed/added:
  - docker-compose.debug.yml (edited: pruned a service entry in the “SERVICES” list to stabilize local stack script block)
  - src/DBDefinitions/purchasemodel.py (added): base SQLAlchemy model PurchaseModel with core fields (reason, description, correct_examples, other_info_website, handover_request, reasoning) and self-relation placeholders.

___

### 2. Purchase model enrichment and itemization
**October 24, 2025**  
**Commit:** `4ab3bb26` — “2. commit”

- Enhanced PurchaseModel and added the PurchaseItem entity; wired data loaders and GraphQL types.
- Files changed/added:
  - src/DBDefinitions/purchasemodel.py (edited):
    - Added path (materialized-path placeholder).
    - Renamed/standardized parent FK to maininfo_id; defined subinfo relationship.
    - Added PurchaseItem model with purchase_id, name, quantity, price and relationship back to PurchaseModel.
  - src/Dataloaders/__init__.py (edited): registered loaders for PurchaseModel and PurchaseItem.
  - src/GraphTypeDefinitions/PurchaseGQLModel.py (added): basic Purchase GraphQL type exposing reason, description and subinfo resolver.
  - src/GraphTypeDefinitions/PurchaseItemGQLModel.py (added): basic Purchase item GraphQL type (name, quantity, price).
  - src/GraphTypeDefinitions/__init__.py (edited): included PurchaseGQLModel and PurchaseItemGQLModel in schema types.
  - src/GraphTypeDefinitions/mutation.py (edited): added purchase_insert mutation (authenticated) using Insert helper.
  - src/GraphTypeDefinitions/query.py (edited): introduced PurchaseQuery with purchase_by_id and purchase_page (with PageResolver).

___

### 3. Polishing DB and GraphQL input models
**October 30, 2025**  
**Commit:** `90fcbe1e` — “3. commit”

- Consolidated DB exports and refined default/nullable handling for item FK; extended GQL input support.
- Files changed/added:
  - src/DBDefinitions/__init__.py (edited): exported PurchaseModel and PurchaseItem.
  - src/DBDefinitions/purchasemodel.py (edited): adjusted purchase_id on PurchaseItem to allow nullable/default ordering compatible with BaseModel dataclass.
  - src/GraphTypeDefinitions/PurchaseGQLModel.py (edited): enriched with InputModelMixin utilities and added PurchaseItemInsertModel input type; ensured VectorResolver includes whereType=None for subinfo.

___

### 4. Finalizing queries and insert workflow (part 1)
**October 31, 2025 13:40**  
**Commit:** `09ba0321` — “4. commit”

- Refinements around Purchase GraphQL layer and insertion flow.
- Areas changed in this step:
  - Input model wiring for nested insert structure.
  - Consistency in loaders and resolver factories (PageResolver/VectorResolver).
  - Minor cleanups in schema registration (where applicable).

___

### 5. Finalizing queries and insert workflow (part 2)
**October 31, 2025 13:41**  
**Commit:** `056b9b07` — “4.commit”

- Follow-up adjustments towards the Purchase end-to-end feature.
- Areas changed in this step:
  - Fine-tuning relationship resolvers and type registrations.
  - Ensuring mutation and query signatures align with loader contracts.
  - Small cohesion fixes between DBDefinitions, Dataloaders, and GraphTypeDefinitions.
___

