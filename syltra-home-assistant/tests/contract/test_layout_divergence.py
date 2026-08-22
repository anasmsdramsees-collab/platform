"""The placeholder directories must keep telling the truth (spec §8).

Several directories the specification's layout defines hold no content, because
a Python workspace wanted the packages elsewhere. Each carries a README saying
where the content actually is.

A pointer nobody checks is a pointer that rots, and a README that confidently
names a file which was renamed two months ago is worse than the empty directory
it replaced. These tests fail the build when that happens.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.contract

ROOT = Path(__file__).resolve().parents[2]

# Directories §8 defines that hold no content. `services/cloud-connector/` is
# deliberately absent: whether it should exist at all is an open decision
# (docs/GAPS.md §2.3), not a settled divergence.
PLACEHOLDERS = (
    "models/definitions",
    "models/training",
    "models/evaluation",
    "models/exported",
    "simulator/devices",
    "simulator/scenarios",
    "simulator/fixtures",
    "infrastructure/docker",
)

# A backtick-quoted repository path: `a/b/c.py` or `a/b/`.
REFERENCE = re.compile(r"`([a-z][\w./-]*\.(?:py|json|md)|[a-z][\w./-]*/)`")


@pytest.mark.parametrize("directory", PLACEHOLDERS)
def test_each_empty_directory_explains_itself(directory: str) -> None:
    readme = ROOT / directory / "README.md"
    assert readme.exists(), f"{directory} is empty and says nothing about why"


@pytest.mark.parametrize("directory", PLACEHOLDERS)
def test_every_path_a_readme_points_at_exists(directory: str) -> None:
    readme = ROOT / directory / "README.md"
    for reference in REFERENCE.findall(readme.read_text(encoding="utf-8")):
        assert (ROOT / reference.rstrip("/")).exists(), (
            f"{directory}/README.md points at {reference}, which does not exist"
        )


@pytest.mark.parametrize("directory", PLACEHOLDERS)
def test_a_directory_that_gained_content_no_longer_needs_the_note(directory: str) -> None:
    """The note claims the directory is empty. It has to still be true."""
    contents = [
        path
        for path in (ROOT / directory).rglob("*")
        if path.is_file() and path.name not in {".gitkeep", "README.md"}
    ]
    assert not contents, (
        f"{directory} now holds {[p.name for p in contents]}; "
        "its README says the content lives elsewhere"
    )


def test_the_list_matches_what_is_actually_empty() -> None:
    """Catches a new empty directory nobody added to the list above."""
    skip = {".git", ".venv", "node_modules", "__pycache__", ".claude", ".next"}
    unexplained = []
    for path in ROOT.rglob("*"):
        if not path.is_dir() or any(part in skip or part.startswith(".") for part in path.parts):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in PLACEHOLDERS or relative.startswith("services/cloud-connector"):
            continue
        files = [p for p in path.rglob("*") if p.is_file() and p.name != ".gitkeep"]
        if not files and (path / ".gitkeep").exists():
            unexplained.append(relative)
    assert not unexplained, f"empty placeholder directories with no explanation: {unexplained}"
