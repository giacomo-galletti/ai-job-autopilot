"""Theme for the designed CV and cover letter: colours and font, kept out of the stylesheets.

The defaults live in theme.json next to this file. To restyle your own documents, create
`profile/theme.json` (the gitignored private folder at the repo root) with only the keys you
want to change:

    {"accent": "#0f766e", "accent_bar": "#0f766e", "font_family": "Inter"}

Keys (all optional):

    ink, body, muted, accent, accent_bar, rule, paper   CSS colours (#rgb, #rrggbb or rgb()/hsl())
    font_family   Name of the font used first, e.g. "Inter" (bundled, SIL OFL). Any font installed
                  on the machine also works; the stack falls back to Inter, then the system font.

The CV and the cover letter both read this, so the pair always matches.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
DEFAULTS_FILE = HERE / "theme.json"
PROFILE_FILE = REPO_ROOT / "profile" / "theme.json"

_COLOR_KEYS = {
    "ink": "--ink",
    "body": "--body",
    "muted": "--muted",
    "accent": "--accent",
    "accent_bar": "--accent-bar",
    "rule": "--rule",
    "paper": "--paper",
}
_COLOR = re.compile(r"^(#[0-9a-fA-F]{3,8}|(rgb|hsl)a?\([0-9 ,.%/]+\))$")
_FONT = re.compile(r"^[A-Za-z0-9 _-]{1,60}$")


class ThemeError(ValueError):
    """The theme file has a value that is not safe to put in the stylesheet."""


def load_theme(profile_file: Path | None = None) -> dict:
    """theme.json defaults, overridden by profile/theme.json when it exists."""
    theme = json.loads(DEFAULTS_FILE.read_text(encoding="utf-8"))
    override = PROFILE_FILE if profile_file is None else profile_file
    if override.is_file():
        theme.update(json.loads(override.read_text(encoding="utf-8")))
    return theme


def css_overrides(theme: dict | None = None) -> str:
    """A <style> block redefining the stylesheet's :root variables from the theme."""
    theme = theme or load_theme()
    lines = []
    for key, var in _COLOR_KEYS.items():
        value = str(theme[key]).strip()
        if not _COLOR.match(value):
            raise ThemeError(f"theme {key!r} is not a CSS colour: {value!r}")
        lines.append(f"  {var}: {value};")
    font = str(theme["font_family"]).strip()
    if not _FONT.match(font):
        raise ThemeError(f"theme 'font_family' must be a plain font name: {font!r}")
    stack = f'"{font}", "Inter", -apple-system, system-ui, sans-serif' if font != "Inter" else '"Inter", -apple-system, system-ui, sans-serif'
    lines.append(f"  --font-stack: {stack};")
    return "<style>\n:root {\n" + "\n".join(lines) + "\n}\n</style>"
