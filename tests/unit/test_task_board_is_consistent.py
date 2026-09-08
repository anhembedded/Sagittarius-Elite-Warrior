"""No two task files may claim the same ID, and no board link may dangle.

The `Tasks/` boards are maintained by hand, and hand-numbering has now failed
four separate times in this repository:

- `BUG-051`/`BUG-052`, two sessions taking "the next number" from the same
  board (recorded at the top of `Tasks/bug_report/README.md`);
- `BUG-058`, which then collided again with the very bug that renumbering
  produced;
- `BOT-120`, two finished tasks sharing a number with only one of them linked
  from `ROADMAP.md`;
- `BOT-126`, a parallel session numbering against a board this session had not
  yet written to.

`Tasks/bug_report/README.md` already says the Engine repo guards exactly this
and that this repo does not. It does now. The check is mechanical because the
failure is mechanical: nobody reads a whole board before picking a number, and
a collision is invisible until two branches meet.

Ignoring `reports/` and `plans/` is deliberate, not an oversight: a report is
*named after* the task it analyses (`BOT-098A_marker_density_performance.md`),
so sharing that ID is the convention rather than a clash. Sub-task IDs are
whole IDs of their own — `BOT-042A` does not collide with `BOT-042`.
"""

from __future__ import annotations

import collections
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TASKS = _REPO_ROOT / "Tasks"

#: Every directory that holds a real task/bug file. A file's *state* is its
#: directory, so the same ID appearing in two of these is a genuine clash — and
#: so is the same ID twice in one of them.
_FLAT_POOLS = (
    "backlog",
    "completed",
    "in_progress",
    "cancelled",
    "proposal",
    "bug_report/incomplete",
    "bug_report/completed",
)

#: Per-epic sub-task directories, under `Tasks/epics/EPIC-XXX_*/`.
_EPIC_POOLS = ("incomplete", "completed", "cancelled")

#: `BOT-095H`, `EPIC-003F6`, `BUG-058`, `BOLT-001` — the whole stem before the
#: first underscore, so a sub-task letter is part of the identity.
_ID = re.compile(r"^([A-Z]+-\d+[A-Z]?\d*)(?:_|\.md$)")


def _task_files() -> list[Path]:
    found: list[Path] = []
    for pool in _FLAT_POOLS:
        found.extend((_TASKS / pool).glob("*.md"))
    for epic in _TASKS.glob("epics/EPIC-*"):
        for pool in _EPIC_POOLS:
            found.extend((epic / pool).glob("*.md"))
    return found


def _by_id() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = collections.defaultdict(list)
    for path in _task_files():
        match = _ID.match(path.name)
        if match:
            index[match.group(1)].append(path)
    return index


def test_the_scan_actually_finds_the_boards() -> None:
    """Guards the guard. A wrong root or a renamed directory would make every
    assertion below pass over an empty set — green, and proving nothing."""
    assert len(_task_files()) > 100


def test_no_two_task_files_share_an_id() -> None:
    """The collision itself. Two files with one ID means one of them is
    invisible on the board, and a link to that ID reaches whichever the writer
    happened to mean."""
    clashes = {
        task_id: sorted(str(p.relative_to(_REPO_ROOT)) for p in paths)
        for task_id, paths in _by_id().items()
        if len(paths) > 1
    }

    assert clashes == {}, (
        "these IDs are used by more than one task file — renumber the one with "
        f"fewer references and record the change in its own header: {clashes}"
    )


def test_every_board_link_resolves() -> None:
    """A renumber that misses a link leaves the board pointing at a file that
    no longer exists — which reads exactly like a task nobody finished."""
    boards = (_TASKS / "ROADMAP.md", _TASKS / "bug_report" / "README.md")
    dangling: list[str] = []
    for board in boards:
        for target in re.findall(r"\]\(([^)#][^)]*\.md)\)", board.read_text("utf-8")):
            if not (board.parent / target).exists():
                dangling.append(f"{board.name} -> {target}")

    assert dangling == [], f"board links pointing at nothing: {dangling}"
