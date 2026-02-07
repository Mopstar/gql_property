"""
Error Codes Registry - Centrální slovník UUID chybových kódů

Tento modul obsahuje všechny UUID error kódy používané v GraphQL API.
Pro použití importujte konstanty ERROR_CODES nebo funkce get_error_code().

Příklad použití:
    from src.error_codes import ERROR_CODES, ERROR_CODE_DETAILS, format_error_response

    # V resolver - základní použití
    error = ERROR_CODE_DETAILS["AUTH_NO_REQUIRED_ROLE"]
    raise PermissionError(f"[{error.code}] {error.message}")

    # V resolver - s detaily
    error_response = format_error_response(
        "AUTH_NO_REQUIRED_ROLE",
        details={"user_id": user_id, "required_roles": ["editor"]}
    )
    raise PermissionError(f"[{error_response['code']}] {error_response['message']}")

    # Pro dokumentaci
    error_info = get_error_info("AUTH_NO_REQUIRED_ROLE")
    print(error_info.description)
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(str, Enum):
    """Error categories for classification.

    Categories help organize errors by their nature and make it easier
    to filter and handle specific types of errors.
    """
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    DATABASE = "DATABASE"
    BUSINESS = "BUSINESS"
    CONCURRENCY = "CONCURRENCY"
    INTERNAL = "INTERNAL"


@dataclass
class ErrorCodeInfo:
    """Informace o chybovém kódu.

    Attributes:
        uuid: UUID kód pro strojové zpracování (zachováno pro kompatibilitu)
        code: Lidsky čitelný kód (např. "AUTH-002")
        name: Programový název (např. "AUTH_NO_REQUIRED_ROLE")
        message: Krátká chybová zpráva
        description: Detailní popis chyby
        resolution: Jak uživatel může problém vyřešit
        category: Kategorie chyby (ErrorCategory enum)
    """
    uuid: str
    code: str
    name: str
    message: str
    description: str
    resolution: str
    category: ErrorCategory


# ===========================================================================================
# ERROR CODES - Definice všech UUID kódů
# ===========================================================================================

ERROR_CODES: Dict[str, str] = {
    # Authentication & Authorization (AUTH-xxx)
    "AUTH_NOT_AUTHENTICATED": "e1a2b3c4-5d6e-7f8g-9h0i-1j2k3l4m5n6o",
    "AUTH_NO_REQUIRED_ROLE": "f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e",
    "AUTH_NOT_CREATOR_OR_EDITOR": "a8f3d7b2-4e9c-4d3a-9b2f-7c6e8d5f9a1b",

    # Insert Operation Errors (INSERT-xxx)
    "INSERT_FAILED_DB": "ca8b4531-9419-4b87-badd-823d364f6c9b",
    "INSERT_EXCEPTION": "7163dd9c-752c-4d1d-a89e-0bdbc7988a8e",

    # Update Operation Errors (UPDATE-xxx)
    "UPDATE_FAILED_DB": "d8e9f2a3-6b7c-4e5f-8a9b-2c3d4e5f6a7b",
    "UPDATE_EXCEPTION": "e9f0a1b2-7c8d-5f6e-9b0c-3d4e5f6a7b8c",
    "UPDATE_NOT_AUTHORIZED": "48f0a626-f31a-4429-9e53-819ca865786d",  # Event invitation specific
    "UPDATE_NOT_ORGANIZER": "ae30e32b-94ec-4d59-9c1e-7eca3b75701e",  # Event invitation specific
    "UPDATE_STALE_DATA": "c7d8e9f0-a1b2-4c5d-8e9f-0a1b2c3d4e5f",

    # Delete Operation Errors (DELETE-xxx)
    "DELETE_FAILED_DB": "f0a1b2c3-8d9e-5f6a-9b0c-1d2e3f4a5b6c",
    "DELETE_EXCEPTION": "a1b2c3d4-9e0f-6a7b-0c1d-2e3f4a5b6c7d",
    "DELETE_HAS_DEPENDENCIES": "b2c3d4e5-0f1a-7b8c-1d2e-3f4a5b6c7d8e",

    # Validation Errors (VALIDATION-xxx)
    "VALIDATION_INVALID_INPUT": "c3d4e5f6-1a2b-8c9d-2e3f-4a5b6c7d8e9f",
    "VALIDATION_MISSING_REQUIRED": "d4e5f6a7-2b3c-9d0e-3f4a-5b6c7d8e9f0a",
    "VALIDATION_FOREIGN_KEY": "e5f6a7b8-3c4d-0e1f-4a5b-6c7d8e9f0a1b",

    # Business Logic Errors (BUSINESS-xxx)
    "BUSINESS_INVALID_STATE": "f6a7b8c9-4d5e-1f2a-5b6c-7d8e9f0a1b2c",
    "BUSINESS_DUPLICATE_ENTRY": "a7b8c9d0-5e6f-2a3b-6c7d-8e9f0a1b2c3d",

    # Not Found Errors (NF-xxx) - NEW
    "NF_ENTITY_NOT_FOUND": "b8c9d0e1-6f7a-3b4c-7d8e-9f0a1b2c3d4e",
    "NF_PARENT_NOT_FOUND": "c9d0e1f2-7a8b-4c5d-8e9f-0a1b2c3d4e5f",

    # Internal Errors (INT-xxx) - NEW
    "INT_UNEXPECTED_ERROR": "d0e1f2a3-8b9c-5d6e-9f0a-1b2c3d4e5f6a",
    "INT_LOADER_FAILED": "e1f2a3b4-9c0d-6e7f-0a1b-2c3d4e5f6a7b",
    "INT_EXTENSION_FAILED": "f2a3b4c5-0d1e-7f8a-1b2c-3d4e5f6a7b8c",
}


# ===========================================================================================
# ERROR CODE DETAILS - Detailní informace o každém kódu
# ===========================================================================================

ERROR_CODE_DETAILS: Dict[str, ErrorCodeInfo] = {
    "AUTH_NOT_AUTHENTICATED": ErrorCodeInfo(
        uuid=ERROR_CODES["AUTH_NOT_AUTHENTICATED"],
        code="AUTH-001",
        name="AUTH_NOT_AUTHENTICATED",
        message="User not authenticated",
        description="Uživatel není přihlášen, ale pokouší se o operaci vyžadující autentizaci",
        resolution="Přihlásit se pomocí /gql/login nebo zajistit platný JWT token",
        category=ErrorCategory.AUTHENTICATION
    ),

    "AUTH_NO_REQUIRED_ROLE": ErrorCodeInfo(
        uuid=ERROR_CODES["AUTH_NO_REQUIRED_ROLE"],
        code="AUTH-002",
        name="AUTH_NO_REQUIRED_ROLE",
        message="Permission denied - no required role for creation",
        description="Uživatel nemá požadovanou roli v žádné skupině pro vytvoření entity. "
                   "Vyžaduje se alespoň jedna z editačních rolí (editor, garant, vedoucí, děkan, atd.)",
        resolution="Kontaktovat správce pro přidělení editační role ve skupině",
        category=ErrorCategory.AUTHORIZATION
    ),

    "AUTH_NOT_CREATOR_OR_EDITOR": ErrorCodeInfo(
        uuid=ERROR_CODES["AUTH_NOT_CREATOR_OR_EDITOR"],
        code="AUTH-003",
        name="AUTH_NOT_CREATOR_OR_EDITOR",
        message="Permission denied - not creator or group editor",
        description="Uživatel není tvůrcem entity a nemá požadovanou roli ve skupině entity. "
                   "Pro úpravu/mazání je potřeba být buď tvůrcem, nebo mít editační/admin roli ve skupině.",
        resolution="Upravovat pouze vlastní vytvořený obsah nebo získat editační roli ve skupině entity",
        category=ErrorCategory.AUTHORIZATION
    ),

    "INSERT_FAILED_DB": ErrorCodeInfo(
        uuid=ERROR_CODES["INSERT_FAILED_DB"],
        code="INSERT-001",
        name="INSERT_FAILED_DB",
        message="Insert operation failed",
        description="Databázová operace insert selhala. Loader vrátil None, což indikuje constraint violation "
                   "nebo jiné databázové omezení (foreign key, unique, not null).",
        resolution="Zkontrolovat vstupní data, databázové logy a constraint definice",
        category=ErrorCategory.DATABASE
    ),

    "INSERT_EXCEPTION": ErrorCodeInfo(
        uuid=ERROR_CODES["INSERT_EXCEPTION"],
        code="INSERT-002",
        name="INSERT_EXCEPTION",
        message="Insert operation raised exception",
        description="Neočekávaná výjimka během insert operace. Může jít o Python exception "
                   "(TypeError, ValueError), síťovou chybu databáze, nebo validační chybu SQLAlchemy.",
        resolution="Analyzovat pole 'msg' pro konkrétní exception details",
        category=ErrorCategory.INTERNAL
    ),

    "UPDATE_FAILED_DB": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_FAILED_DB"],
        code="UPDATE-001",
        name="UPDATE_FAILED_DB",
        message="Update operation failed",
        description="Databázová operace update selhala. Entity s daným ID neexistuje, "
                   "nebo došlo k optimistic locking failure (lastchange timestamp se změnil).",
        resolution="Ověřit existenci entity a aktuálnost lastchange timestamp",
        category=ErrorCategory.DATABASE
    ),

    "UPDATE_EXCEPTION": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_EXCEPTION"],
        code="UPDATE-002",
        name="UPDATE_EXCEPTION",
        message="Update operation raised exception",
        description="Neočekávaná výjimka během update operace.",
        resolution="Analyzovat pole 'msg' pro konkrétní exception details",
        category=ErrorCategory.INTERNAL
    ),

    "UPDATE_NOT_AUTHORIZED": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_NOT_AUTHORIZED"],
        code="UPDATE-003",
        name="UPDATE_NOT_AUTHORIZED",
        message="You are not authorized to accept/decline this invitation",
        description="Uživatel není účastníkem události a nemůže přijmout/odmítnout pozvánku. "
                   "User ID se neshoduje s invitation.user_id.",
        resolution="Můžete měnit pouze své vlastní pozvánky",
        category=ErrorCategory.AUTHORIZATION
    ),

    "UPDATE_NOT_ORGANIZER": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_NOT_ORGANIZER"],
        code="UPDATE-004",
        name="UPDATE_NOT_ORGANIZER",
        message="You are not organizer of this event",
        description="Uživatel není organizátorem události a nemůže upravovat pozvánky ostatních účastníků.",
        resolution="Pouze organizátoři mohou měnit pozvánky",
        category=ErrorCategory.AUTHORIZATION
    ),

    "UPDATE_STALE_DATA": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_STALE_DATA"],
        code="UPDATE-005",
        name="UPDATE_STALE_DATA",
        message="Stale data - entity was modified by another user",
        description="Optimistic locking failure. Entity byla změněna jiným uživatelem mezi načtením a ukládáním.",
        resolution="Znovu načíst aktuální data a provést změny znovu",
        category=ErrorCategory.CONCURRENCY
    ),

    "DELETE_FAILED_DB": ErrorCodeInfo(
        uuid=ERROR_CODES["DELETE_FAILED_DB"],
        code="DELETE-001",
        name="DELETE_FAILED_DB",
        message="Delete operation failed",
        description="Databázová operace delete selhala. Entity neexistuje nebo má závislosti.",
        resolution="Ověřit existenci entity a případné závislosti",
        category=ErrorCategory.DATABASE
    ),

    "DELETE_EXCEPTION": ErrorCodeInfo(
        uuid=ERROR_CODES["DELETE_EXCEPTION"],
        code="DELETE-002",
        name="DELETE_EXCEPTION",
        message="Delete operation raised exception",
        description="Neočekávaná výjimka během delete operace.",
        resolution="Analyzovat pole 'msg' pro konkrétní exception details",
        category=ErrorCategory.INTERNAL
    ),

    "DELETE_HAS_DEPENDENCIES": ErrorCodeInfo(
        uuid=ERROR_CODES["DELETE_HAS_DEPENDENCIES"],
        code="DELETE-003",
        name="DELETE_HAS_DEPENDENCIES",
        message="Cannot delete - entity has dependencies",
        description="Entity nemůže být smazána, protože na ni odkazují jiné entity. "
                   "Foreign key constraint zabraňuje odstranění.",
        resolution="Nejprve odstranit závislé entity nebo nastavit valid=False místo delete",
        category=ErrorCategory.BUSINESS
    ),

    "VALIDATION_INVALID_INPUT": ErrorCodeInfo(
        uuid=ERROR_CODES["VALIDATION_INVALID_INPUT"],
        code="VALIDATION-001",
        name="VALIDATION_INVALID_INPUT",
        message="Invalid input format",
        description="Vstupní data mají neplatný formát nebo hodnotu.",
        resolution="Zkontrolovat formát vstupních dat podle schema",
        category=ErrorCategory.VALIDATION
    ),

    "VALIDATION_MISSING_REQUIRED": ErrorCodeInfo(
        uuid=ERROR_CODES["VALIDATION_MISSING_REQUIRED"],
        code="VALIDATION-002",
        name="VALIDATION_MISSING_REQUIRED",
        message="Required field is missing",
        description="Povinné pole chybí ve vstupních datech.",
        resolution="Doplnit všechny povinná pole",
        category=ErrorCategory.VALIDATION
    ),

    "VALIDATION_FOREIGN_KEY": ErrorCodeInfo(
        uuid=ERROR_CODES["VALIDATION_FOREIGN_KEY"],
        code="VALIDATION-003",
        name="VALIDATION_FOREIGN_KEY",
        message="Foreign key constraint violation",
        description="Odkazovaná entita neexistuje. Foreign key reference je neplatná.",
        resolution="Zkontrolovat existenci odkazované entity",
        category=ErrorCategory.VALIDATION
    ),

    # NOT_FOUND category - NEW
    "NF_ENTITY_NOT_FOUND": ErrorCodeInfo(
        uuid=ERROR_CODES["NF_ENTITY_NOT_FOUND"],
        code="NF-001",
        name="NF_ENTITY_NOT_FOUND",
        message="Entity not found",
        description="Požadovaná entita s daným ID neexistuje v databázi nebo byla smazána.",
        resolution="Ověřit správnost ID entity a že entita nebyla smazána",
        category=ErrorCategory.NOT_FOUND
    ),

    "NF_PARENT_NOT_FOUND": ErrorCodeInfo(
        uuid=ERROR_CODES["NF_PARENT_NOT_FOUND"],
        code="NF-002",
        name="NF_PARENT_NOT_FOUND",
        message="Parent entity not found",
        description="Nelze provést operaci - nadřazená entita neexistuje.",
        resolution="Zkontrolovat existenci nadřazené entity před vytvořením/úpravou",
        category=ErrorCategory.NOT_FOUND
    ),

    # INTERNAL category - NEW
    "INT_UNEXPECTED_ERROR": ErrorCodeInfo(
        uuid=ERROR_CODES["INT_UNEXPECTED_ERROR"],
        code="INT-001",
        name="INT_UNEXPECTED_ERROR",
        message="Unexpected internal error occurred",
        description="Došlo k neočekávané chybě nebo neznámému stavu systému.",
        resolution="Kontaktovat administrátora s detaily chyby a časem výskytu",
        category=ErrorCategory.INTERNAL
    ),

    "INT_LOADER_FAILED": ErrorCodeInfo(
        uuid=ERROR_CODES["INT_LOADER_FAILED"],
        code="INT-002",
        name="INT_LOADER_FAILED",
        message="DataLoader failed to load entity",
        description="GraphQL DataLoader selhal při načítání entity. Může jít o chybu v batch loadingu.",
        resolution="Zkusit operaci znovu nebo kontaktovat administrátora",
        category=ErrorCategory.INTERNAL
    ),

    "INT_EXTENSION_FAILED": ErrorCodeInfo(
        uuid=ERROR_CODES["INT_EXTENSION_FAILED"],
        code="INT-003",
        name="INT_EXTENSION_FAILED",
        message="GraphQL extension failed",
        description="Chyba v extension pipeline (RBAC, profiling, atd.).",
        resolution="Zkontrolovat konfiguraci extensions nebo kontaktovat administrátora",
        category=ErrorCategory.INTERNAL
    ),
}


# ===========================================================================================
# HELPER FUNCTIONS
# ===========================================================================================

def get_error_code(code_name: str) -> Optional[str]:
    """Získat UUID kód podle jména.

    Args:
        code_name: Jméno error kódu (např. "AUTH_NO_REQUIRED_ROLE")

    Returns:
        UUID string nebo None pokud kód neexistuje

    Example:
        >>> get_error_code("AUTH_NO_REQUIRED_ROLE")
        "f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e"
    """
    return ERROR_CODES.get(code_name)


def get_error_info(code_name: str) -> Optional[ErrorCodeInfo]:
    """Získat detailní informace o error kódu.

    Args:
        code_name: Jméno error kódu

    Returns:
        ErrorCodeInfo objekt s detaily nebo None

    Example:
        >>> info = get_error_info("AUTH_NO_REQUIRED_ROLE")
        >>> print(info.description)
        "Uživatel nemá požadovanou roli..."
    """
    return ERROR_CODE_DETAILS.get(code_name)


def get_error_by_uuid(uuid: str) -> Optional[ErrorCodeInfo]:
    """Najít error info podle UUID.

    Args:
        uuid: UUID kód chyby

    Returns:
        ErrorCodeInfo objekt nebo None

    Example:
        >>> info = get_error_by_uuid("f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e")
        >>> print(info.code)
        "AUTH-002"
    """
    for details in ERROR_CODE_DETAILS.values():
        if details.uuid == uuid:
            return details
    return None


def format_error_response(
    error_name: str,
    details: Optional[Dict] = None,
    custom_message: Optional[str] = None
) -> Dict:
    """Format standardized error response with full metadata.

    This function creates a consistent error response structure that includes
    both the UUID (for machine processing) and human-readable code, along with
    all metadata from the error code definition.

    Args:
        error_name: Name of error code (e.g., "AUTH_NO_REQUIRED_ROLE")
        details: Additional context/details dictionary (e.g., user_id, required_roles)
        custom_message: Optional custom message to override default

    Returns:
        Formatted error response dictionary with keys:
        - uuid: UUID string for machine processing
        - code: Human-readable code (e.g., "AUTH-002")
        - name: Error code name
        - category: Error category
        - message: User-friendly error message
        - details: Additional context
        - resolution: Suggested fix

    Example:
        >>> error_response = format_error_response(
        ...     "AUTH_NO_REQUIRED_ROLE",
        ...     details={
        ...         "user_id": "123e4567-e89b-12d3-a456-426614174000",
        ...         "user_fullname": "John Doe",
        ...         "required_roles": ["editor", "garant"],
        ...         "current_roles": ["viewer"]
        ...     }
        ... )
        >>> print(f"[{error_response['code']}] {error_response['message']}")
        [AUTH-002] Permission denied - no required role for creation
    """
    error = ERROR_CODE_DETAILS.get(error_name)
    if not error:
        # Fallback to unexpected error if code not found
        error = ERROR_CODE_DETAILS["INT_UNEXPECTED_ERROR"]
        details = {**(details or {}), "original_error_name": error_name}

    return {
        "uuid": error.uuid,
        "code": error.code,
        "name": error.name,
        "category": error.category.value,
        "message": custom_message or error.message,
        "details": details or {},
        "resolution": error.resolution,
        "description": error.description
    }


def list_error_codes(category: Optional[ErrorCategory] = None) -> Dict[str, ErrorCodeInfo]:
    """Vypsat všechny error kódy, volitelně filtrované podle kategorie.

    Args:
        category: Filtrovat podle kategorie (ErrorCategory enum)

    Returns:
        Dictionary mapující code_name -> ErrorCodeInfo

    Example:
        auth_errors = list_error_codes(category=ErrorCategory.AUTHORIZATION)
        for name, error_info in auth_errors.items():
            print(f"{error_info.code}: {error_info.message}")
    """
    if category is None:
        return ERROR_CODE_DETAILS

    return {
        name: info
        for name, info in ERROR_CODE_DETAILS.items()
        if info.category == category
    }


# ===========================================================================================
# CUSTOM EXCEPTIONS
# ===========================================================================================

class AuthorizationException(Exception):
    """Custom exception pro authorization errors s UUID kódem.

    Používat místo standardního PermissionError pro specifické UUID kódy.

    Example:
        raise AuthorizationException(
            msg="Permission denied. User 'John' has no required role.",
            code=ERROR_CODES["AUTH_NO_REQUIRED_ROLE"]
        )
    """
    def __init__(self, msg: str, code: str):
        self.msg = msg
        self.code = code
        super().__init__(msg)


class ValidationException(Exception):
    """Custom exception pro validation errors s UUID kódem."""
    def __init__(self, msg: str, code: str):
        self.msg = msg
        self.code = code
        super().__init__(msg)


class BusinessLogicException(Exception):
    """Custom exception pro business logic errors s UUID kódem."""
    def __init__(self, msg: str, code: str):
        self.msg = msg
        self.code = code
        super().__init__(msg)


# ===========================================================================================
# ROLE REQUIREMENTS MAPPING
# ===========================================================================================

ROLE_REQUIREMENTS_FOR_OPERATIONS = {
    "CREATE": {
        "required_roles": ["editor", "garant", "děkan", "vedoucí katedry", "prorektor", "rektor"],
        "error_code": "AUTH_NO_REQUIRED_ROLE",
        "description": "Pro vytvoření entity je vyžadována editační role"
    },
    "UPDATE": {
        "required_roles": ["editor", "garant", "děkan", "vedoucí katedry"],
        "error_code": "AUTH_NOT_CREATOR_OR_EDITOR",
        "description": "Pro úpravu entity musíte být tvůrce nebo mít editační roli"
    },
    "DELETE": {
        "required_roles": ["administrátor", "admin", "děkan", "rektor", "proděkan"],
        "error_code": "AUTH_NOT_CREATOR_OR_EDITOR",
        "description": "Pro smazání entity musíte být tvůrce nebo mít admin roli"
    }
}


if __name__ == "__main__":
    # Příklad použití
    print("=== Error Codes Registry ===\n")

    # Získat UUID
    code = get_error_code("AUTH_NO_REQUIRED_ROLE")
    print(f"AUTH_NO_REQUIRED_ROLE UUID: {code}\n")

    # Získat detaily
    info = get_error_info("AUTH_NO_REQUIRED_ROLE")
    if info:
        print(f"Code: {info.code}")
        print(f"Name: {info.name}")
        print(f"Message: {info.message}")
        print(f"Description: {info.description}")
        print(f"Resolution: {info.resolution}")
        print(f"Category: {info.category.value}\n")

    # Vypsat všechny Authorization errors
    print("=== Authorization Errors ===")
    auth_errors = list_error_codes(category=ErrorCategory.AUTHORIZATION)
    for name, details in auth_errors.items():
        print(f"{details.code}: {details.message}")

    # Použití format_error_response
    print("\n=== Formatted Error Response ===")
    error_response = format_error_response(
        "AUTH_NO_REQUIRED_ROLE",
        details={
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_fullname": "John Doe",
            "required_roles": ["editor", "garant"],
            "current_roles": ["viewer"]
        }
    )
    print(f"[{error_response['code']}] {error_response['message']}")
    print(f"UUID: {error_response['uuid']}")
    print(f"Details: {error_response['details']}")
    print(f"Resolution: {error_response['resolution']}")

