"""
Error Codes Registry - Centrální slovník UUID chybových kódů

Tento modul obsahuje všechny UUID error kódy používané v GraphQL API.
Pro použití importujte konstanty ERROR_CODES nebo funkce get_error_code().

Příklad použití:
    from src.error_codes import ERROR_CODES, get_error_code, ErrorCodeInfo

    # V resolver
    raise AuthorizationException(
        msg="Permission denied",
        code=ERROR_CODES["AUTH_NO_REQUIRED_ROLE"]
    )

    # Pro dokumentaci
    error_info = get_error_code("AUTH_NO_REQUIRED_ROLE")
    print(error_info.description)
"""

from typing import Dict, NamedTuple, Optional
from uuid import UUID


class ErrorCodeInfo(NamedTuple):
    """Informace o chybovém kódu.

    Attributes:
        uuid: UUID kód pro strojové zpracování
        code: Lidsky čitelný kód (např. "AUTH-002")
        message: Krátká chybová zpráva
        description: Detailní popis chyby
        resolution: Jak uživatel může problém vyřešit
        category: Kategorie chyby (Authentication, Database, Validation, ...)
    """
    uuid: str
    code: str
    message: str
    description: str
    resolution: str
    category: str


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
}


# ===========================================================================================
# ERROR CODE DETAILS - Detailní informace o každém kódu
# ===========================================================================================

ERROR_CODE_DETAILS: Dict[str, ErrorCodeInfo] = {
    "AUTH_NOT_AUTHENTICATED": ErrorCodeInfo(
        uuid=ERROR_CODES["AUTH_NOT_AUTHENTICATED"],
        code="AUTH-001",
        message="User not authenticated",
        description="Uživatel není přihlášen, ale pokouší se o operaci vyžadující autentizaci",
        resolution="Přihlásit se pomocí /gql/login nebo zajistit platný JWT token",
        category="Authentication"
    ),

    "AUTH_NO_REQUIRED_ROLE": ErrorCodeInfo(
        uuid=ERROR_CODES["AUTH_NO_REQUIRED_ROLE"],
        code="AUTH-002",
        message="Permission denied - no required role for creation",
        description="Uživatel nemá požadovanou roli v žádné skupině pro vytvoření entity. "
                   "Vyžaduje se alespoň jedna z editačních rolí (editor, garant, vedoucí, děkan, atd.)",
        resolution="Kontaktovat správce pro přidělení editační role ve skupině",
        category="Authorization"
    ),

    "AUTH_NOT_CREATOR_OR_EDITOR": ErrorCodeInfo(
        uuid=ERROR_CODES["AUTH_NOT_CREATOR_OR_EDITOR"],
        code="AUTH-003",
        message="Permission denied - not creator or group editor",
        description="Uživatel není tvůrcem entity a nemá požadovanou roli ve skupině entity. "
                   "Pro úpravu/mazání je potřeba být buď tvůrcem, nebo mít editační/admin roli ve skupině.",
        resolution="Upravovat pouze vlastní vytvořený obsah nebo získat editační roli ve skupině entity",
        category="Authorization"
    ),

    "INSERT_FAILED_DB": ErrorCodeInfo(
        uuid=ERROR_CODES["INSERT_FAILED_DB"],
        code="INSERT-001",
        message="Insert operation failed",
        description="Databázová operace insert selhala. Loader vrátil None, což indikuje constraint violation "
                   "nebo jiné databázové omezení (foreign key, unique, not null).",
        resolution="Zkontrolovat vstupní data, databázové logy a constraint definice",
        category="Database"
    ),

    "INSERT_EXCEPTION": ErrorCodeInfo(
        uuid=ERROR_CODES["INSERT_EXCEPTION"],
        code="INSERT-002",
        message="Insert operation raised exception",
        description="Neočekávaná výjimka během insert operace. Může jít o Python exception "
                   "(TypeError, ValueError), síťovou chybu databáze, nebo validační chybu SQLAlchemy.",
        resolution="Analyzovat pole 'msg' pro konkrétní exception details",
        category="Exception"
    ),

    "UPDATE_FAILED_DB": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_FAILED_DB"],
        code="UPDATE-001",
        message="Update operation failed",
        description="Databázová operace update selhala. Entity s daným ID neexistuje, "
                   "nebo došlo k optimistic locking failure (lastchange timestamp se změnil).",
        resolution="Ověřit existenci entity a aktuálnost lastchange timestamp",
        category="Database"
    ),

    "UPDATE_EXCEPTION": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_EXCEPTION"],
        code="UPDATE-002",
        message="Update operation raised exception",
        description="Neočekávaná výjimka během update operace.",
        resolution="Analyzovat pole 'msg' pro konkrétní exception details",
        category="Exception"
    ),

    "UPDATE_NOT_AUTHORIZED": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_NOT_AUTHORIZED"],
        code="UPDATE-003",
        message="You are not authorized to accept/decline this invitation",
        description="Uživatel není účastníkem události a nemůže přijmout/odmítnout pozvánku. "
                   "User ID se neshoduje s invitation.user_id.",
        resolution="Můžete měnit pouze své vlastní pozvánky",
        category="Authorization"
    ),

    "UPDATE_NOT_ORGANIZER": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_NOT_ORGANIZER"],
        code="UPDATE-004",
        message="You are not organizer of this event",
        description="Uživatel není organizátorem události a nemůže upravovat pozvánky ostatních účastníků.",
        resolution="Pouze organizátoři mohou měnit pozvánky",
        category="Authorization"
    ),

    "UPDATE_STALE_DATA": ErrorCodeInfo(
        uuid=ERROR_CODES["UPDATE_STALE_DATA"],
        code="UPDATE-005",
        message="Stale data - entity was modified by another user",
        description="Optimistic locking failure. Entity byla změněna jiným uživatelem mezi načtením a ukládáním.",
        resolution="Znovu načíst aktuální data a provést změny znovu",
        category="Concurrency"
    ),

    "DELETE_FAILED_DB": ErrorCodeInfo(
        uuid=ERROR_CODES["DELETE_FAILED_DB"],
        code="DELETE-001",
        message="Delete operation failed",
        description="Databázová operace delete selhala. Entity neexistuje nebo má závislosti.",
        resolution="Ověřit existenci entity a případné závislosti",
        category="Database"
    ),

    "DELETE_EXCEPTION": ErrorCodeInfo(
        uuid=ERROR_CODES["DELETE_EXCEPTION"],
        code="DELETE-002",
        message="Delete operation raised exception",
        description="Neočekávaná výjimka během delete operace.",
        resolution="Analyzovat pole 'msg' pro konkrétní exception details",
        category="Exception"
    ),

    "DELETE_HAS_DEPENDENCIES": ErrorCodeInfo(
        uuid=ERROR_CODES["DELETE_HAS_DEPENDENCIES"],
        code="DELETE-003",
        message="Cannot delete - entity has dependencies",
        description="Entity nemůže být smazána, protože na ni odkazují jiné entity. "
                   "Foreign key constraint zabraňuje odstranění.",
        resolution="Nejprve odstranit závislé entity nebo nastavit valid=False místo delete",
        category="Business"
    ),

    "VALIDATION_INVALID_INPUT": ErrorCodeInfo(
        uuid=ERROR_CODES["VALIDATION_INVALID_INPUT"],
        code="VALIDATION-001",
        message="Invalid input format",
        description="Vstupní data mají neplatný formát nebo hodnotu.",
        resolution="Zkontrolovat formát vstupních dat podle schema",
        category="Validation"
    ),

    "VALIDATION_MISSING_REQUIRED": ErrorCodeInfo(
        uuid=ERROR_CODES["VALIDATION_MISSING_REQUIRED"],
        code="VALIDATION-002",
        message="Required field is missing",
        description="Povinné pole chybí ve vstupních datech.",
        resolution="Doplnit všechny povinná pole",
        category="Validation"
    ),

    "VALIDATION_FOREIGN_KEY": ErrorCodeInfo(
        uuid=ERROR_CODES["VALIDATION_FOREIGN_KEY"],
        code="VALIDATION-003",
        message="Foreign key constraint violation",
        description="Odkazovaná entita neexistuje. Foreign key reference je neplatná.",
        resolution="Zkontrolovat existenci odkazované entity",
        category="Validation"
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


def list_error_codes(category: Optional[str] = None) -> Dict[str, ErrorCodeInfo]:
    """Vypsat všechny error kódy, volitelně filtrované podle kategorie.

    Args:
        category: Filtrovat podle kategorie (Authentication, Authorization, Database, ...)

    Returns:
        Dictionary mapující code_name -> ErrorCodeInfo

    Example:
        >>> auth_errors = list_error_codes(category="Authorization")
        >>> for name, info in auth_errors.items():
        >>>     print(f"{info.code}: {info.message}")
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
        print(f"Message: {info.message}")
        print(f"Description: {info.description}")
        print(f"Resolution: {info.resolution}")
        print(f"Category: {info.category}\n")

    # Vypsat všechny Authorization errors
    print("=== Authorization Errors ===")
    auth_errors = list_error_codes(category="Authorization")
    for name, details in auth_errors.items():
        print(f"{details.code}: {details.message}")

