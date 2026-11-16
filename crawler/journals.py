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
        "date_th": (
            '<th class="num" aria-sort="descending">'
            '<button type="button" class="sort" data-key="date">Published'
            '<span class="arrow" aria-hidden="true"></span></button></th>'
        ),
    },
)

JOURNALS = {"jci": JCI}


def clean_title(text):
    """Crossref titles may contain markup such as <i>...</i> or MathML; keep plain text."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", text)).split())


def published_month(work):
    """Publication month as the number YYYYMM (None if unknown).

    Crossref's `issued` is the issue date (an annual issue is dated January), so the
    online date is preferred, then the print date, then `issued`.
    """
    for key in ("published-online", "published-print", "issued"):
        parts = (work.get(key) or {}).get("date-parts", [[]])[0]
        if parts and parts[0]:
            return parts[0] * 100 + (parts[1] if len(parts) > 1 else 1)
    return None


def build_rows(items):
    """Rows in the shared table format plus a month: [doi, title, None, None, None, "A", authors, YYYYMM]."""
    rows = []
    for work in items:
        if work.get("type") != "journal-article" or not work.get("title"):
            continue
        authors = [" ".join(filter(None, [a.get("given"), a.get("family")])) or a.get("name", "")
                   for a in work.get("author", [])]
        rows.append([work["DOI"], clean_title(work["title"][0]), None, None, None, "A",
                     [a for a in authors if a], published_month(work)])
    rows.sort(key=lambda r: (-(r[7] or 0), r[1].lower(), r[0]))  # newest first
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
                    "select": "DOI,title,author,issued,published-online,published-print,type"})
        resp.raise_for_status()
        message = resp.json()["message"]
        if not message["items"]:
            break
        items.extend(message["items"])
        cursor = message["next-cursor"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return items
