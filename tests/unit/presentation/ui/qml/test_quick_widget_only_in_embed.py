"""`BUG-115` guard — a `QQuickWidget` is constructed, inherited, or given a
clear colour in exactly one place: `src/presentation/ui/qml/embed/`.

Why a grep guard and not a review rule: the defect this closes spread by
copy-paste — ten hosts, each carrying the same twelve lines and the same
wrong comment ("transparent so the parent shows through"), each written
by someone who read the previous host as the pattern to follow. A rule in
`qml-rule.md` did not stop the tenth copy; this test stops the eleventh.
Same shape as `test_qml_style_discipline.py` (colour literals in `.qml`).
"""

from __future__ import annotations

import re
from pathlib import Path

_UI_ROOT = Path(__file__).resolve().parents[5] / "src" / "presentation" / "ui"
_EMBED_DIR = _UI_ROOT / "qml" / "embed"

#: Constructing one, or naming it as a base class.
_CONSTRUCT_OR_SUBCLASS = re.compile(r"\bQQuickWidget\(\)|\(QQuickWidget\)")
#: The clear colour is the engine factory's decision (`TASK-042`); no host
#: sets it, opaque or otherwise, because the only value a host ever
#: reached for was the one that renders black on a real screen.
_CLEAR_COLOUR = re.compile(r"\.setClearColor\(")


def _ui_python_files() -> list[Path]:
    return sorted(
        path
        for path in _UI_ROOT.rglob("*.py")
        if _EMBED_DIR not in path.parents and "tests" not in path.parts
    )


def _offenders(pattern: re.Pattern[str]) -> list[str]:
    return [
        f"{path.relative_to(_UI_ROOT)}:{number}: {line.strip()}"
        for path in _ui_python_files()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if pattern.search(line)
    ]


def test_there_are_ui_files_to_check():
    """A guard that passes because it found nothing is how this rots."""
    assert _ui_python_files(), f"no .py under {_UI_ROOT}"
    assert (_EMBED_DIR / "quick_surface.py").is_file()


def test_no_qquickwidget_is_built_or_subclassed_outside_embed():
    offenders = _offenders(_CONSTRUCT_OR_SUBCLASS)
    assert not offenders, (
        "QQuickWidget constructed or subclassed outside qml/embed/ — embed the "
        "scene through QuickSurface (BUG-115 §4.3):\n" + "\n".join(offenders)
    )


def test_no_host_sets_a_clear_colour():
    offenders = _offenders(_CLEAR_COLOUR)
    assert not offenders, (
        "setClearColor() outside qml/embed/ — the clear colour is the surface "
        "token QuickSurface resolves, never a per-host choice (BUG-115):\n"
        + "\n".join(offenders)
    )
