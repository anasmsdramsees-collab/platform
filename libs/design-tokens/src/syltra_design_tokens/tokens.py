"""Load and audit the SYLTRA design tokens (guidelines §6, §22, §24).

The tokens live in `apps/local-console/src/design-system/tokens/tokens.json`.
This module reads them and builds the contrast audit that Phase UI-0 acceptance
requires ("token contrast checks pass").

Which pairs are audited is a judgement, and the judgement is stated here rather
than buried: every pair a user can actually see. Auditing `text-disabled`
against `background` at 4.5:1 would fail by design — disabled text is
deliberately low-contrast and WCAG exempts it — so it is checked at the
non-text bar and labelled as such.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from syltra_design_tokens.contrast import (
    NON_TEXT_RATIO,
    NORMAL_TEXT_RATIO,
    ContrastCheck,
    check,
)

TOKENS_PATH = Path("apps/local-console/src/design-system/tokens/tokens.json")


def repo_root_from(start: Path) -> Path:
    """Walk up until the tokens file is found."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / TOKENS_PATH).is_file():
            return candidate
    msg = f"could not locate {TOKENS_PATH} above {start}"
    raise FileNotFoundError(msg)


def load_tokens(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or repo_root_from(Path(__file__))
    loaded: dict[str, Any] = json.loads((root / TOKENS_PATH).read_text(encoding="utf-8"))
    return loaded


@dataclass(frozen=True)
class ThemeAudit:
    theme: str
    checks: list[ContrastCheck]

    @property
    def failures(self) -> list[ContrastCheck]:
        return [c for c in self.checks if not c.passes]

    @property
    def passes(self) -> bool:
        return not self.failures

    def report(self) -> str:
        lines = [f"{self.theme} theme — {len(self.checks)} checks"]
        lines += [f"  {c.describe()}" for c in self.checks]
        return "\n".join(lines)


# Text tokens rendered on each surface. The pairing is what a user sees, not
# every mathematically possible combination.
_TEXT_ON_SURFACE = ("text-primary", "text-secondary", "text-tertiary")
_SURFACES = ("background", "surface", "surface-raised", "surface-overlay")


def audit_theme(tokens: dict[str, Any], theme: str) -> ThemeAudit:
    """Every visible foreground/background pair in one theme."""
    palette = tokens["theme"][theme]
    status = tokens["status"]
    checks: list[ContrastCheck] = []

    for surface in _SURFACES:
        background = palette[surface]
        for text in _TEXT_ON_SURFACE:
            checks.append(
                check(f"{text} on {surface}", palette[text], background, NORMAL_TEXT_RATIO)
            )
        # Disabled text is deliberately low-contrast and WCAG exempts inactive
        # controls; it is held to the non-text bar so it stays perceivable
        # without pretending it must read like body copy.
        checks.append(
            check(
                f"text-disabled on {surface}",
                palette["text-disabled"],
                background,
                NON_TEXT_RATIO,
                kind="non-text",
            )
        )

    # Accent is used for primary action text and selected state (§6.5).
    for surface in ("background", "surface", "surface-raised"):
        checks.append(
            check(f"accent on {surface}", palette["accent"], palette[surface], NORMAL_TEXT_RATIO)
        )

    # A primary button places background-coloured text on the accent fill.
    checks.append(
        check(
            "button label on accent",
            palette["background"],
            palette["accent"],
            NORMAL_TEXT_RATIO,
        )
    )

    # Semantic status colours carry text and icons (§6.5: "Every semantic color
    # must include text and icon support"), so they are held to the text bar on
    # every surface they can land on — not only the one they were sampled
    # against. The identity hues in the `status` group are what the brand means
    # by "warning"; each theme restates them at a lightness that passes.
    for name in status:
        if name.startswith("_"):
            continue
        colour = palette[f"status-{name}"]
        for surface in ("background", "surface", "surface-raised"):
            checks.append(
                check(
                    f"status-{name} on {surface}",
                    colour,
                    palette[surface],
                    NORMAL_TEXT_RATIO,
                )
            )

    # Boundaries and the focus ring are essential non-text components (§22).
    for surface in _SURFACES:
        checks.append(
            check(
                f"border-strong on {surface}",
                palette["border-strong"],
                palette[surface],
                NON_TEXT_RATIO,
                kind="non-text",
            )
        )
    checks.append(
        check(
            "focus-ring on background",
            palette["focus-ring"],
            palette["background"],
            NON_TEXT_RATIO,
            kind="non-text",
        )
    )
    checks.append(
        check(
            "focus-ring on surface",
            palette["focus-ring"],
            palette["surface"],
            NON_TEXT_RATIO,
            kind="non-text",
        )
    )
    return ThemeAudit(theme=theme, checks=checks)


def audit_all(repo_root: Path | None = None) -> list[ThemeAudit]:
    tokens = load_tokens(repo_root)
    return [audit_theme(tokens, theme) for theme in ("dark", "light")]


def brand_colours(tokens: dict[str, Any]) -> set[str]:
    """Every brand and status hex value, for the hardcoded-colour check."""
    found: set[str] = set()
    for group in (tokens["brand"], tokens["status"], *tokens["theme"].values()):
        for key, value in group.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict):
                found.update(v.upper() for k, v in value.items() if not k.startswith("_"))
            elif isinstance(value, str) and value.startswith("#"):
                found.add(value.upper())
    return found


def main() -> None:  # pragma: no cover - CLI
    failed = False
    for audit in audit_all():
        print(audit.report())
        print()
        if not audit.passes:
            failed = True
            for failure in audit.failures:
                print(f"  ✘ {failure.describe()}")
    raise SystemExit(1 if failed else 0)

