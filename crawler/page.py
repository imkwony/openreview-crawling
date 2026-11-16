"""Render a conference's index.html from the shared template."""
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "templates" / "conference.html"

# Wording for OpenReview conferences; a venue can override any of these with its own `page` dict.
DEFAULT_PAGE = {
    "heading": "Submissions Ranked",
    "description": "{label} submissions ranked by the average of reviewer ratings collected from OpenReview.",
    "intro": "Ratings are collected from public OpenReview reviews. Rank is not an official result.",
    "kw_label": "Keywords",
    "script_attrs": "",
    "date_th": "",  # journals add a sortable "Published" column
}


def render_page(venue):
    text = {**DEFAULT_PAGE, **getattr(venue, "page", {})}
    text["description"] = text["description"].format(label=venue.label)
    text["label"], text["note"] = venue.label, venue.note
    html = TEMPLATE.read_text(encoding="utf-8")
    for key, value in text.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def write_page(venue, root=None):
    root = root or Path(__file__).resolve().parent.parent
    out = root / venue.slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_page(venue), encoding="utf-8", newline="")
    return out
