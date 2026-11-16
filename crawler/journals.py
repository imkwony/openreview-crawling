"""Journals that are not on OpenReview: paper lists come from Crossref's public API (no key)."""
import html
import json
import re
from dataclasses import dataclass, field

from .client import random_pause

CROSSREF = "https://api.crossref.org/journals/{issn}/works"
PAGE_SIZE = 1000


@dataclass(frozen=True)
class Journal:
    name: str
    slug: str
    issn: str
    note: str = ""
    page: dict = field(default_factory=dict)

    @property
    def label(self):
        return self.name


JCI = Journal(
    name="Journal of Causal Inference",
    slug="jci",
    issn="2193-3685",
    note=" Paper list from Crossref; the journal has no public reviews, so Rank is empty and every paper is published.",
    page={
        "heading": "Papers",
        "description": "Journal of Causal Inference papers, listed from Crossref.",
        "intro": "Titles and authors come from Crossref; each link opens the paper by DOI.",
        "kw_label": "Authors",
        "script_attrs": ' data-link="https://doi.org/"',
    },
)

JOURNALS = {"jci": JCI}


def clean_title(text):
    """Crossref titles may contain markup such as <i>...</i> or MathML; keep plain text."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", text)).split())


def build_rows(items):
    """Rows in the shared table format: [doi, title, None, None, None, "A", authors]."""
    rows = []
    for work in items:
        if work.get("type") != "journal-article" or not work.get("title"):
            continue
        authors = [" ".join(filter(None, [a.get("given"), a.get("family")])) or a.get("name", "")
                   for a in work.get("author", [])]
        rows.append([work["DOI"], clean_title(work["title"][0]), None, None, None, "A",
                     [a for a in authors if a]])
    rows.sort(key=lambda r: (r[1].lower(), r[0]))
    return rows


def crawl(journal, cache_dir, refresh=False, get=None, sleep=random_pause):
    """All works of the journal (cached in .cache/ so a rerun makes no requests)."""
    cache = cache_dir / journal.slug / "works.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    if get is None:
        import requests
        get = lambda url, params: requests.get(url, params=params, timeout=60)
    items, cursor = [], "*"
    while True:
        sleep()
        resp = get(CROSSREF.format(issn=journal.issn),
                   {"rows": PAGE_SIZE, "cursor": cursor,
                    "select": "DOI,title,author,issued,type"})
        resp.raise_for_status()
        message = resp.json()["message"]
        if not message["items"]:
            break
        items.extend(message["items"])
        cursor = message["next-cursor"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return items
