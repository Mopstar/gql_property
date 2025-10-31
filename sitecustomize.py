import os
import sys


def _ensure_src_on_path() -> None:
    """
    Ensure that the repository's `src` directory is importable without
    requiring callers to mutate `PYTHONPATH`. Tests import packages such
    as `DBDefinitions` directly, so we prepend the physical path here.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(root_dir, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


_ensure_src_on_path()
