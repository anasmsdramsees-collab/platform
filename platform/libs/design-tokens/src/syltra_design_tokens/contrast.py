"""WCAG 2.2 contrast computation (guidelines §22, §6.5).

Implements the WCAG relative-luminance and contrast-ratio formulas so token
pairs can be verified automatically rather than by eye. The guidelines set two
bars:

- **4.5:1** for normal text (§6.5, §22);
- **3:1** for essential icons, boundaries and controls (§6.5, §22).

Large text (18pt / 24px, or 14pt / 18.66px bold) may use 3:1 under WCAG, and
`required_ratio` encodes that so a heading is not held to a stricter bar than
the standard sets.
"""

from dataclasses import dataclass
from typing import Final

NORMAL_TEXT_RATIO: Final = 4.5
LARGE_TEXT_RATIO: Final = 3.0
NON_TEXT_RATIO: Final = 3.0

LARGE_TEXT_PX: Final = 24.0
LARGE_BOLD_PX: Final = 18.66


class ContrastError(ValueError):
    """A colour could not be parsed."""


def parse_hex(colour: str) -> tuple[int, int, int]:
    """Parse `#RGB` or `#RRGGBB` into 8-bit channels."""
    value = colour.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(channel * 2 for channel in value)
    if len(value) != 6:
        msg = f"{colour!r} is not a hex colour"
        raise ContrastError(msg)
    try:
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
    except ValueError as exc:
        msg = f"{colour!r} is not a hex colour"
        raise ContrastError(msg) from exc


def _channel_luminance(channel: int) -> float:
    scaled = channel / 255.0
    if scaled <= 0.04045:
        return scaled / 12.92
    return float(((scaled + 0.055) / 1.055) ** 2.4)


def relative_luminance(colour: str) -> float:
    """WCAG relative luminance, 0 (black) to 1 (white)."""
    red, green, blue = parse_hex(colour)
    return (
        0.2126 * _channel_luminance(red)
        + 0.7152 * _channel_luminance(green)
        + 0.0722 * _channel_luminance(blue)
    )


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG contrast ratio, 1.0 to 21.0."""
    lighter = relative_luminance(foreground)
    darker = relative_luminance(background)
    if lighter < darker:
        lighter, darker = darker, lighter
    return (lighter + 0.05) / (darker + 0.05)


def required_ratio(font_size_px: float | None = None, bold: bool = False) -> float:
    """The ratio WCAG requires for text of this size.

    Large text is 18pt (24px), or 14pt (18.66px) when bold.
    """
    if font_size_px is None:
        return NORMAL_TEXT_RATIO
    if font_size_px >= LARGE_TEXT_PX or (bold and font_size_px >= LARGE_BOLD_PX):
        return LARGE_TEXT_RATIO
    return NORMAL_TEXT_RATIO


@dataclass(frozen=True)
class ContrastCheck:
    """One foreground/background pair and whether it meets its bar."""

    name: str
    foreground: str
    background: str
    ratio: float
    required: float
    kind: str = "text"

    @property
    def passes(self) -> bool:
        return self.ratio >= self.required

    def describe(self) -> str:
        verdict = "pass" if self.passes else "FAIL"
        return (
            f"{verdict}  {self.name}: {self.foreground} on {self.background} "
            f"= {self.ratio:.2f}:1 (needs {self.required}:1)"
        )


def check(
    name: str,
    foreground: str,
    background: str,
    required: float = NORMAL_TEXT_RATIO,
    kind: str = "text",
) -> ContrastCheck:
    return ContrastCheck(
        name=name,
        foreground=foreground,
        background=background,
        ratio=contrast_ratio(foreground, background),
        required=required,
        kind=kind,
    )
