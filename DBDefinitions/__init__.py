"""
Compatibility wrapper that exposes the project database models as a
top-level package. The tests expect to be able to `import DBDefinitions`
directly, so we simply re-export the actual implementation living under
`src.DBDefinitions`.
"""

from src.DBDefinitions import *  # noqa: F401,F403
