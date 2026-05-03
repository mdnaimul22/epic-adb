import sys
from pathlib import Path

_MARKER_FILES = (".env", "main.py", "pyproject.toml", ".git", "cli.py", "app.py")

def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current] + list(current.parents):
        if any((candidate / m).exists() for m in _MARKER_FILES):
            return candidate
    return current.parent

PROJECT_ROOT = find_project_root()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
