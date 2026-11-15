"""Render a conference's index.html from the shared template."""
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "templates" / "conference.html"


def render_page(venue):
    return TEMPLATE.read_text(encoding="utf-8").replace("{{label}}", venue.label)


def write_page(venue, root=None):
    root = root or Path(__file__).resolve().parent.parent
    out = root / venue.slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_page(venue), encoding="utf-8", newline="")
    return out
