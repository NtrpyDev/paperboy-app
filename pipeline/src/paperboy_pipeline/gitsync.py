"""Committing and pushing the content repo checkout, safely when runs overlap.

Runs overlap, and two runs that both append to the open chunk or the seen file cannot be merged
by git. So a command that pushes never merges: it builds its change from the work folder and the
checkout, commits it, and pushes. When the push is rejected because the remote moved, it resets
the checkout to the new origin/main and builds the same change again on top of it. Every command
that pushes therefore derives its whole change from its arguments, the work folder, and what is
already on main; nothing it needs lives only in the checkout.

Commits are one per changed top-level folder, each holding only that folder, with a fixed
subject, so each folder's last commit subject describes it on GitHub.
"""
import subprocess
import sys
from pathlib import Path
from typing import Callable

SUBJECTS = {
    "papers": "Published papers: explainer page, card image, and record for each",
    "feed": "Feed head and chunks the app reads",
    "state": "Pipeline bookkeeping: papers in the feed, source cursors, the backlog, and claims",
}
ATTEMPTS = 5
REJECTED = ("[rejected]", "non-fast-forward", "fetch first", "failed to update ref", "cannot lock ref")


class GitError(Exception):
    """A git command failed, or the push kept being rejected."""


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def commit(root: Path) -> list[str]:
    """Commit each changed folder of SUBJECTS on its own. Other changes are left alone. Returns the
    folders committed."""
    done = []
    for folder, subject in SUBJECTS.items():
        if not git(root, "status", "--porcelain", "--", folder).strip():
            continue
        git(root, "add", "-A", "--", folder)
        git(root, "commit", "-q", "-m", subject, "--", folder)
        done.append(folder)
    return done


def _push(root: Path) -> bool:
    """True when pushed, False when the remote moved and rejected it."""
    result = subprocess.run(["git", "-C", str(root), "push", "-q", "origin", "HEAD:main"], capture_output=True, text=True)
    if result.returncode == 0:
        return True
    message = (result.stderr or result.stdout).strip()
    if any(sign in message for sign in REJECTED):
        return False
    raise GitError(f"git push origin HEAD:main failed: {message}")


def _reset_to_origin(root: Path) -> None:
    git(root, "fetch", "-q", "origin", "main")
    git(root, "reset", "-q", "--hard", "origin/main")
    git(root, "clean", "-q", "-fd", "--", *SUBJECTS)


def sync(root: Path, apply: Callable[[], None], *, start_from_origin: bool, attempts: int = ATTEMPTS, label: str = "push") -> int:
    """apply() changes the checkout; commit and push it. On a rejected push, reset to the new
    origin/main and apply again, up to `attempts` times. Returns the attempt that pushed.

    start_from_origin: reset to origin/main before the first attempt too. The checkout must then
    hold nothing unpushed: a command that starts from origin refuses a dirty or ahead checkout
    rather than throw work away. Without it the first attempt builds on the checkout as it is
    (publish, whose run left queue changes in the checkout that it rebuilds from the work folder)."""
    if start_from_origin:
        git(root, "fetch", "-q", "origin", "main")
        dirty = git(root, "status", "--porcelain", "--", *SUBJECTS).strip()
        ahead = git(root, "rev-list", "origin/main..HEAD").strip()
        if dirty or ahead:
            raise GitError("the checkout holds changes that are not on origin/main; push or discard them first:\n"
                           + (dirty or f"{len(ahead.splitlines())} local commits"))
    for attempt in range(1, attempts + 1):
        if start_from_origin or attempt > 1:
            _reset_to_origin(root)
        apply()
        commit(root)
        if _push(root):
            return attempt
        print(f"{label}: origin/main moved, building the change again on top of it (attempt {attempt + 1} of {attempts})", file=sys.stderr)
    raise GitError(f"the push was rejected {attempts} times; origin/main keeps moving")
