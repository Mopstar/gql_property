"""
Compatibility shim for tests that import `GraphTypeDefinitions` directly.
The real implementation lives in `src.GraphTypeDefinitions`, so we simply
re-export everything from there.
"""

from src.GraphTypeDefinitions import *  # noqa: F401,F403
