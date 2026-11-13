"""Finding a Chromium-family browser to drive. Nothing is ever downloaded."""
import os
import shutil

NAMES = ("google-chrome", "chromium", "chromium-browser", "brave")
ENV = "PAPERBOY_CHROME"


def find_browser() -> str | None:
    """The browser executable: $PAPERBOY_CHROME (a path or a name on PATH), else the
    first of NAMES on PATH, else None."""
    chosen = os.environ.get(ENV)
    if chosen:
        if os.path.isfile(chosen) and os.access(chosen, os.X_OK):
            return chosen
        return shutil.which(chosen)
    for name in NAMES:
        path = shutil.which(name)
        if path:
            return path
    return None
