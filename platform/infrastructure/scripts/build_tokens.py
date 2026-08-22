"""Generate the design-system CSS from tokens.json (guidelines §24, ADR-008).

`tokens.json` is the single source of truth. The CSS files are generated and
checked in, so the console needs no build step on the hub — and a test
regenerates them and fails if the checked-in copies have drifted, the same guard
already used for the JSON Schemas in `contracts/`.

Ordering matters in two places and is deliberate:

- **Dark is declared on bare `:root`.** Dark is the primary platform experience
  (§6.3), so it is what a browser gets before any preference is read.
- **Light is applied under `[data-theme="light"]` and under
  `prefers-color-scheme: light` guarded by `:not([data-theme="dark"])`**, so an
  explicit choice always wins over the system preference in both directions.
"""

import json
from pathlib import Path
from typing import Any

BANNER = """/* GENERATED FROM tokens.json — DO NOT EDIT BY HAND.
 * Regenerate with `make tokens`. A test fails if this file drifts from
 * tokens.json (guidelines §24, ADR-008).
 */
"""


def _flat(prefix: str, node: Any, out: dict[str, str]) -> None:
    """Flatten a token group into `--prefix-key: value` pairs, skipping notes."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("_"):
                continue
            _flat(f"{prefix}-{key}" if prefix else key, value, out)
    else:
        out[prefix] = str(node)


def build_tokens_css(tokens: dict[str, Any]) -> str:
    lines = [BANNER, ":root {"]

    lines.append("  /* Brand palette (§6.1) — Graphite, Sand, Electric Cyan. */")
    brand: dict[str, str] = {}
    _flat("syltra", tokens["brand"], brand)
    lines += [f"  --{name}: {value};" for name, value in brand.items()]

    lines.append("")
    lines.append("  /* Semantic status (§6.2). Green lives here and nowhere else. */")
    status: dict[str, str] = {}
    _flat("status", tokens["status"], status)
    lines += [f"  --{name}: {value};" for name, value in status.items()]

    for group, comment in (
        ("space", "Spacing, 4px base (§8.1)"),
        ("radius", "Radius (§8.2)"),
        ("elevation", "Elevation (§8.3) — popovers, dialogs, menus only"),
        ("motion", "Motion (§19)"),
        ("layout", "Desktop shell geometry (§9.2)"),
        ("control", "Control sizing (§12.1, §22)"),
    ):
        lines.append("")
        lines.append(f"  /* {comment}. */")
        flat: dict[str, str] = {}
        _flat(group, tokens[group], flat)
        lines += [f"  --{name}: {value};" for name, value in flat.items()]

    lines.append("}")
    lines.append("")
    lines.append("/* Density (§8.4). Comfortable is the default. */")
    for mode, values in tokens["density"].items():
        selector = ":root, [data-density='comfortable']" if mode == "comfortable" else f"[data-density='{mode}']"
        lines.append(f"{selector} {{")
        lines += [f"  --density-{key}: {value};" for key, value in values.items()]
        lines.append("}")
    return "\n".join(lines) + "\n"


def _theme_block(theme: dict[str, Any]) -> list[str]:
    return [f"  --{name}: {value};" for name, value in theme.items() if not name.startswith("_")]


def build_dark_css(tokens: dict[str, Any]) -> str:
    dark = tokens["theme"]["dark"]
    lines = [
        BANNER,
        "/* Dark theme — the primary platform experience (§6.3).",
        " * Declared on bare :root so it is what a browser gets before any",
        " * preference is read. */",
        ":root,",
        '[data-theme="dark"] {',
        *_theme_block(dark),
        "}",
        "",
        "/* An explicit light choice wins over this, and over the system",
        " * preference, in both directions. */",
    ]
    return "\n".join(lines) + "\n"


def build_light_css(tokens: dict[str, Any]) -> str:
    light = tokens["theme"]["light"]
    block = _theme_block(light)
    lines = [
        BANNER,
        "/* Light theme (§6.4). Applied by explicit choice, or by system",
        " * preference when no explicit choice has been made. */",
        '[data-theme="light"] {',
        *block,
        "}",
        "",
        "@media (prefers-color-scheme: light) {",
        '  :root:not([data-theme="dark"]) {',
        *[f"  {line}" for line in block],
        "  }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def build_typography_css(tokens: dict[str, Any]) -> str:
    typo = tokens["typography"]
    lines = [
        BANNER,
        ":root {",
        "  /* Families (§7.1). Named families first, system fallbacks after. */",
    ]
    lines += [f"  --font-{key}: {value};" for key, value in typo["family"].items() if not key.startswith("_")]
    lines.append("")
    lines.append("  /* Weights — no more than three (§7.3). */")
    lines += [f"  --weight-{key}: {value};" for key, value in typo["weight"].items() if not key.startswith("_")]
    lines.append("")
    lines.append("  /* Type scale (§7.2). */")
    for name, step in typo["scale"].items():
        lines.append(f"  --type-{name}-size: {step['size']};")
        lines.append(f"  --type-{name}-line: {step['line']};")
        lines.append(f"  --type-{name}-weight: {step['weight']};")
    lines.append("}")
    lines.append("")
    lines.append("/* Arabic needs a little more line height than the equivalent")
    lines.append(" * English text (§7.3). */")
    lines.append('[lang="ar"] {')
    lines.append(f"  --line-height-factor: {typo['arabic-line-height-factor']};")
    lines.append("}")
    lines.append("")
    lines.append("/* Utility classes for the scale. */")
    for name, step in typo["scale"].items():
        numeric = step.get("numeric", False)
        lines.append(f".type-{name} {{")
        lines.append(f"  font-size: var(--type-{name}-size);")
        lines.append(
            f"  line-height: calc(var(--type-{name}-line) * var(--line-height-factor, 1));"
        )
        lines.append(f"  font-weight: var(--type-{name}-weight);")
        if numeric:
            # Metrics, energy, temperature, counts and tables (§7.1).
            lines.append("  font-variant-numeric: tabular-nums;")
            lines.append("  font-feature-settings: 'tnum' 1;")
        lines.append("}")
    return "\n".join(lines) + "\n"


def build_motion_css(tokens: dict[str, Any]) -> str:
    motion = {k: v for k, v in tokens["motion"].items() if not k.startswith("_")}
    lines = [
        BANNER,
        ":root {",
        *[f"  --motion-{key}: {value};" for key, value in motion.items()],
        "}",
        "",
        "/* §19 and §22: respect prefers-reduced-motion. Durations collapse to",
        " * a value that is effectively instant but still fires transitionend,",
        " * so state-change handlers that wait on it do not hang. */",
        "@media (prefers-reduced-motion: reduce) {",
        "  :root {",
        "    --motion-fast: 1ms;",
        "    --motion-standard: 1ms;",
        "    --motion-slow: 1ms;",
        "  }",
        "",
        "  *,",
        "  *::before,",
        "  *::after {",
        "    animation-duration: 1ms !important;",
        "    animation-iteration-count: 1 !important;",
        "    transition-duration: 1ms !important;",
        "    scroll-behavior: auto !important;",
        "  }",
        "}",
    ]
    return "\n".join(lines) + "\n"


BUILDERS = {
    "tokens/tokens.css": build_tokens_css,
    "themes/dark-theme.css": build_dark_css,
    "themes/light-theme.css": build_light_css,
    "typography/typography.css": build_typography_css,
    "tokens/motion.css": build_motion_css,
}


def design_system_root(repo_root: Path) -> Path:
    return repo_root / "apps" / "local-console" / "src" / "design-system"


def load_tokens(repo_root: Path) -> dict[str, Any]:
    path = design_system_root(repo_root) / "tokens" / "tokens.json"
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def render_all(repo_root: Path) -> dict[Path, str]:
    tokens = load_tokens(repo_root)
    root = design_system_root(repo_root)
    return {root / name: builder(tokens) for name, builder in BUILDERS.items()}


def write_all(repo_root: Path) -> list[Path]:
    written = []
    for path, content in render_all(repo_root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def main() -> None:  # pragma: no cover - thin CLI wrapper
    repo_root = Path(__file__).resolve().parents[2]
    for path in write_all(repo_root):
        print(f"wrote {path.relative_to(repo_root)}")


if __name__ == "__main__":  # pragma: no cover
    main()
