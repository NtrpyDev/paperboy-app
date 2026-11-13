"""The cursors command at the command line: it records the last day each source is processed through."""
import json

from paperboy_pipeline import schemas
from paperboy_pipeline.cli import main

ALL = ["arxiv", "biorxiv", "medrxiv", "europepmc", "crossref"]


def cursors(content):
    return json.loads((content / "state/cursors.json").read_text())


def test_set_through_writes_every_source_into_an_empty_checkout(tmp_path, capsys):
    content = tmp_path / "content"
    assert main(["cursors", "--content", str(content), "--set-through", "2026-11-12"]) == 0
    assert cursors(content) == {"v": 1, "cursors": {name: "2026-11-12" for name in ALL}}
    assert schemas.errors("cursors", cursors(content)) == []
    assert "arxiv: through 2026-11-12" in capsys.readouterr().out


def test_set_through_moves_only_the_named_sources(tmp_path):
    content = tmp_path / "content"
    main(["cursors", "--content", str(content), "--set-through", "2026-11-10"])
    assert main(["cursors", "--content", str(content), "--set-through", "2026-11-12", "--sources", "arxiv,crossref"]) == 0
    assert cursors(content)["cursors"] == {
        "arxiv": "2026-11-12", "biorxiv": "2026-11-10", "medrxiv": "2026-11-10", "europepmc": "2026-11-10", "crossref": "2026-11-12"}


def test_a_cursor_never_moves_backward(tmp_path, capsys):
    content = tmp_path / "content"
    main(["cursors", "--content", str(content), "--set-through", "2026-11-12", "--sources", "arxiv"])
    before = (content / "state/cursors.json").read_bytes()
    capsys.readouterr()

    assert main(["cursors", "--content", str(content), "--set-through", "2026-11-09", "--sources", "arxiv"]) == 0

    assert (content / "state/cursors.json").read_bytes() == before
    assert "arxiv: already through 2026-11-12" in capsys.readouterr().out


def test_unknown_source_or_bad_date_is_refused(tmp_path):
    content = tmp_path / "content"
    for argv in (["--set-through", "2026-11-12", "--sources", "nature"], ["--set-through", "yesterday"]):
        try:
            code = main(["cursors", "--content", str(content), *argv])
        except SystemExit as exit:
            code = exit.code
        assert code == 2
    assert not (content / "state/cursors.json").exists()


def test_push_commits_and_pushes_the_cursors(tmp_path):
    import subprocess

    def git(root, *a):
        return subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True).stdout

    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    content = tmp_path / "content"
    content.mkdir()
    git(content, "init", "-q", "-b", "main")
    git(content, "config", "user.name", "Test")
    git(content, "config", "user.email", "test@example.invalid")
    (content / "README.md").write_text("x\n")
    git(content, "add", "README.md")
    git(content, "commit", "-q", "-m", "Start")
    git(content, "remote", "add", "origin", str(remote))
    git(content, "push", "-q", "origin", "main")

    assert main(["cursors", "--content", str(content), "--set-through", "2026-11-12", "--sources", "arxiv", "--push"]) == 0

    assert json.loads(git(remote, "show", "main:state/cursors.json")) == {"v": 1, "cursors": {"arxiv": "2026-11-12"}}
