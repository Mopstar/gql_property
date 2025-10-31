"""
Proxy module that re-exports database feeder helpers from `src.DBFeeder`
while keeping the legacy import paths used in the provided tests.
"""

from typing import Any, Dict

from src.DBFeeder import backupDB, initDB, get_demodata as _raw_get_demodata

__all__ = ["initDB", "backupDB", "get_demodata"]

_EVOLUTION_SUFFIX = "_evolution"


def _normalize_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    The historical fixtures reference tables without the `_evolution` suffix,
    while the new dataset includes that suffix. We keep both variants so the
    rest of the codebase can use either form.
    """
    result = dict(data)
    for key, value in data.items():
        if key.endswith(_EVOLUTION_SUFFIX):
            base_key = key[: -len(_EVOLUTION_SUFFIX)]
            result.setdefault(base_key, value)
    return result


def get_demodata() -> Dict[str, Any]:
    """
    Return the demo dataset with backwards-compatible keys.
    """
    raw = _raw_get_demodata()
    if isinstance(raw, dict):
        return _normalize_keys(raw)
    return raw
