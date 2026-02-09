# Error Codes Dictionary / Slovník chybových kódů

**Projekt:** gql_property - Purchase Management GraphQL Service  
**Datum vytvoření:** 11. ledna 2026  
**Verze:** 1.0

---

## Přehled

Tento dokument obsahuje **kompletní slovník všech UUID chybových kódů** používaných v GraphQL API. Každá chyba vrácená v resolverech obsahuje unikátní UUID kód pro strojové zpracování a detailní popis pro diagnostiku.

**Formát chybové odpovědi:**
```graphql
type PurchaseGQLModelInsertError {
  msg: String!           # Lidsky čitelná zpráva
  code: ID               # UUID chybového kódu
  location: String       # Resolver, kde k chybě došlo
  failed: Boolean!       # Vždy true
  input: JSON            # Původní vstupní data
}
```

---

## Error Codes - Kategorie

### 1. Authentication & Authorization Errors (Autentizace a Autorizace)

#### AUTH-001: User Not Authenticated
- **UUID:** `e1a2b3c4-5d6e-7f8g-9h0i-1j2k3l4m5n6o` *(placeholder - zatím neimplementováno)*
- **Message:** "User not authenticated"
- **Description:** Uživatel není přihlášen, ale pokouší se o operaci vyžadující autentizaci
- **Kdy nastává:** Chybí valid JWT token v Authorization header
- **Řešení:** Přihlásit se pomocí `/gql/login` nebo zajistit platný token

#### AUTH-002: Permission Denied - No Required Role
- **UUID:** `f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e` *(extrahováno z chybové hlášky uživatele)*
- **Message:** "Permission denied. User '{fullname}' (ID: {user_id}) cannot create this entity. Required roles: [{roles}]. Your current roles: [{current_roles}]."
- **Description:** Uživatel nemá požadovanou roli v žádné skupině pro vytvoření entity
- **Kdy nastává:** 
  - Pokus o INSERT bez editační role (editor, administrátor, atd.)
  - Uživatel má pouze viewer roli nebo žádnou roli
- **Řešení:** 
  - Kontaktovat správce pro přidělení editační role
  - Získat roli: editor, garant, vedoucí katedry, děkan, atd.
- **Implementace:** `src/GraphTypeDefinitions/authz_extensions.py:249`

#### AUTH-003: Permission Denied - Creator or Group Editor Required
- **UUID:** *(zatím neimplementováno, používá PermissionError)*
- **Message:** "Permission denied for {user_fullname}. You must be the creator or have one of these roles [{roles}] in the entity's group."
- **Description:** Uživatel není tvůrcem entity a nemá požadovanou roli ve skupině entity
- **Kdy nastává:** Pokus o UPDATE/DELETE cizí entity bez patřičné role
- **Řešení:** 
  - Upravovat pouze vlastní vytvořený obsah
  - Nebo získat editační/admin roli ve skupině entity
- **Implementace:** `src/GraphTypeDefinitions/authz_extensions.py:383`

---

### 2. Insert Operation Errors (Chyby vytváření)

#### INSERT-001: Insert Failed (Generic)
- **UUID:** `ca8b4531-9419-4b87-badd-823d364f6c9b`
- **Message:** "insert failed"
- **Description:** Obecná chyba při ukládání entity do databáze (loader.insert vrátil None)
- **Kdy nastává:**
  - Databázové omezení (constraint violation)
  - Foreign key referenční chyba
  - Unikátní constraint porušen
- **Řešení:** Zkontrolovat vstupní data, databázové logy
- **Implementace:** `uoishelpers.resolvers.Insert.DoItSafeWay`

#### INSERT-002: Insert Exception
- **UUID:** `7163dd9c-752c-4d1d-a89e-0bdbc7988a8e`
- **Message:** "{exception details}"
- **Description:** Neočekávaná výjimka při insert operaci
- **Kdy nastává:** 
  - Python exception (TypeError, ValueError, atd.)
  - Síťová chyba databáze
  - Validační chyba SQLAlchemy
- **Řešení:** Analyzovat msg field pro konkrétní exception
- **Implementace:** `uoishelpers.resolvers.Insert.DoItSafeWay`

---

### 3. Update Operation Errors (Chyby aktualizace)

#### UPDATE-001: Update Failed (Generic)
- **UUID:** `{podobně jako INSERT-001, zatím neověřeno}`
- **Message:** "update failed"
- **Description:** Obecná chyba při aktualizaci entity
- **Kdy nastává:**
  - Entity s daným ID neexistuje
  - Optimistic locking failure (lastchange se změnil)
  - Permission denied (není tvůrce ani editor)
- **Řešení:** Ověřit ID a lastchange timestamp

#### UPDATE-002: Not Authorized (Event Invitation Accept/Decline)
- **UUID:** `48f0a626-f31a-4429-9e53-819ca865786d`
- **Message:** "You are not authorized"
- **Description:** Uživatel není účastníkem události a nemůže přijmout/odmítnout pozvánku
- **Kdy nastává:** `event_invitation_accept_decline` - user_id se neshoduje s invitation.user_id
- **Řešení:** Můžete měnit pouze své vlastní pozvánky
- **Implementace:** `src/GraphTypeDefinitions/EventInvitationGQLModel.py:253`

#### UPDATE-003: Not Organizer (Event Invitation Update)
- **UUID:** `ae30e32b-94ec-4d59-9c1e-7eca3b75701e`
- **Message:** "You are not organizer"
- **Description:** Uživatel není organizátorem události a nemůže upravovat pozvánky
- **Kdy nastává:** `event_invitation_update` - user není organizer dané události
- **Řešení:** Pouze organizátoři mohou měnit pozvánky
- **Implementace:** `src/GraphTypeDefinitions/EventInvitationGQLModel.py:290`

---

### 4. Delete Operation Errors (Chyby mazání)

#### DELETE-001: Delete Failed (Generic)
- **UUID:** `{zatím neověřeno}`
- **Message:** "delete failed"
- **Description:** Obecná chyba při mazání entity
- **Kdy nastává:**
  - Entity s daným ID neexistuje
  - Permission denied (není tvůrce ani admin)
  - Cascade delete omezení
- **Řešení:** Ověřit permissions a existenci entity

---

## Role Requirements Summary (Přehled požadovaných rolí)

| Operace | Required Roles | Error Code když selže |
|---------|----------------|----------------------|
| **CREATE** (Insert) | `EDITOR_ROLES` (15 rolí: editor, garant, děkan, vedoucí katedry, atd.) | AUTH-002 (`f42da7e9...`) |
| **UPDATE** | Creator ownership OR `EDITOR_ROLES` | AUTH-003 |
| **DELETE** | Creator ownership OR `ADMIN_ROLES` (5 rolí: administrátor, admin, rektor, děkan, proděkan) | AUTH-003 |
| **READ** | Creator ownership OR `VIEWER_ROLES` (20 rolí: všechny role včetně viewer, čtenář) | AUTH-003 |

**Creator Ownership Philosophy:**
- Pokud jste vytvořili entitu (Purchase, Event, atd.), máte k ní **permanent access** (CRUD)
- I když vaše role později klesne na "viewer", stále můžete editovat/mazat svoje entity
- Admins ve skupině entity také mohou spravovat obsah

---

## Implementační Status

### ✅ Implementováno
1. **InsertError/UpdateError/DeleteError typy** - obsahují `code: ID` field
2. **UUID kódy v uoishelpers** - knihovna vrací error kódy pro insert failures
3. **Custom error kódy** - EventInvitation má 2 UUID kódy pro custom logiku
4. **PermissionError exceptions** - authz_extensions generuje popisné chyby

### ⚠️ Částečně implementováno
1. **Error kódy pro PermissionError** - zatím se nekonvertují na UUID
2. **Centrální slovník** - tento dokument je první verze

### ❌ Chybí
1. **Standardizované UUID pro všechny PermissionError případy**
2. **Update/Delete operation specific UUID kódy** (kromě custom EventInvitation)
3. **Validační error kódy** (např. invalid input format)
4. **Database constraint error mapping** (foreign key, unique, atd.)

---

## Doporučení pro implementaci

### 1. Vytvořit centrální error_codes.py

```python
# src/error_codes.py
from typing import Dict, NamedTuple
from uuid import UUID

class ErrorCode(NamedTuple):
    uuid: str
    code: str
    message: str
    description: str
    resolution: str

ERROR_CODES: Dict[str, ErrorCode] = {
    "AUTH_NO_ROLE_CREATE": ErrorCode(
        uuid="f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e",
        code="AUTH-002",
        message="Permission denied - no required role for creation",
        description="User lacks editor role in any group",
        resolution="Contact admin to get editor, garant, or leadership role"
    ),
    # ... více error kódů
}

def get_error(code: str) -> ErrorCode:
    """Get error details by code"""
    return ERROR_CODES.get(code)
```

### 2. Integrovat error kódy do authz_extensions.py

```python
# Místo:
raise PermissionError("Permission denied...")

# Použít:
from src.error_codes import ERROR_CODES
error = ERROR_CODES["AUTH_NO_ROLE_CREATE"]
raise PermissionError(f"{error.message}: {error.description}")
```

### 3. Vytvořit custom error typy s UUID

```python
@strawberry.type
class AuthorizationError:
    msg: str
    code: str  # UUID
    error_type: str  # "PERMISSION_DENIED"
    required_roles: typing.List[str]
    user_roles: typing.List[str]
```

---

## Testování error kódů

Každý error kód by měl mít test:

```python
def test_insert_without_role_returns_auth_error():
    """User without editor role should get AUTH-002 error"""
    client = get_test_client(user_with_no_roles)
    result = client.purchase_insert(...)
    
    assert result["errors"][0]["extensions"]["code"] == "f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e"
    assert "Permission denied" in result["errors"][0]["message"]
```

---

## Závěr

**Odpověď na otázku zadání:**

✅ **ANO, projekt obsahuje implementaci error kódů UUID:**
1. Error typy (`InsertError`, `UpdateError`, `DeleteError`) mají `code: ID` field
2. Některé resolvery již vrací UUID kódy (např. `ca8b4531...`, `48f0a626...`)
3. Chybové zprávy jsou popisné a obsahují context (user ID, roles, required roles)

⚠️ **ALE existují oblasti k vylepšení:**
1. Chybí centrální slovník error kódů (tento dokument je první krok)
2. Ne všechny chyby mají unikátní UUID (některé používají generické exception)
3. Chybí standardizované mapování PermissionError → UUID kód

**Pro plné splnění požadavků zadání (10 bodů) doporučuji:**
1. ✅ Vytvořit `src/error_codes.py` s centrálním slovníkem
2. ✅ Vytvořit tento `ERROR_CODES.md` dokument (HOTOVO)
3. ⚠️ Přidat UUID kódy pro všechny PermissionError případy v authz_extensions.py
4. ⚠️ Rozšířit testy pro validaci error kódů

**Hodnocení:** 7/10 bodů (70%) - základní infrastruktura existuje, chybí kompletní coverage a centrální slovník

