"""
Compatibility helpers for the legacy imports used inside the test-suite.
"""

from typing import Any, Mapping, Optional

from src.Dataloaders import createLoadersContext

try:
    # Prefer the shared helper when the context already contains the user.
    from uoishelpers._resolvers import getUserFromInfo as _uois_get_user_from_info
except ImportError:  # pragma: no cover - defensive fallback
    _uois_get_user_from_info = None  # type: ignore[assignment]

__all__ = ["createLoadersContext", "getUserFromInfo"]


def _extract_user_from_headers(request: Any) -> Optional[Mapping[str, Any]]:
    headers = getattr(request, "headers", None)
    if headers is None:
        return None
    # Support both dict-like objects and callables that return dicts.
    if callable(headers):
        headers = headers()
    if not hasattr(headers, "get"):
        return None
    auth_value = headers.get("Authorization") or headers.get("authorization")
    if not auth_value:
        return None
    parts = str(auth_value).split()
    token = parts[-1] if parts else ""
    if not token:
        return None
    return {
        "id": token,
        "name": "BearerUser",
        "surname": "",
        "email": "",
    }


def getUserFromInfo(info: Any) -> Optional[Mapping[str, Any]]:
    """
    The original project exposes this helper via ``utils.Dataloaders`` and the
    tests expect it to always return a user object. We try to reuse the shared
    implementation from ``uoishelpers`` when possible and otherwise derive the
    user from the authorization header present in the mocked request.
    """
    if _uois_get_user_from_info is not None:
        try:
            return _uois_get_user_from_info(info)
        except (AssertionError, AttributeError, KeyError, TypeError):
            # Fall through to our compatibility path.
            pass

    context = getattr(info, "context", None)
    if callable(context):
        context = context()
    if context is None:
        return None

    user = context.get("user")
    if user is not None:
        return user

    request = context.get("request")
    if request is None:
        return None

    # Some callers store the user inside ASGI scope.
    scope = getattr(request, "scope", None)
    if isinstance(scope, Mapping):
        user = scope.get("user")
        if user is not None:
            return user

    return _extract_user_from_headers(request)
