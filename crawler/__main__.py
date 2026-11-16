"""Usage: python -m crawler iclr 2027 [--refresh]   |   python -m crawler jci"""
import argparse

from .page import write_page
from .build import ROOT, build_rows, crawl, site_password, write_papers
from .journals import JOURNALS
from .journals import build_rows as journal_rows
from .journals import crawl as crawl_journal
from .venues import VENUES


def main():
    parser = argparse.ArgumentParser(description="Crawl a conference (OpenReview) or journal (Crossref).")
    parser.add_argument("source", choices=sorted(VENUES) + sorted(JOURNALS))
    parser.add_argument("year", type=int, nargs="?", help="conference year (not used for journals)")
    parser.add_argument("--refresh", action="store_true", help="ignore the .cache/ copy and refetch")
    args = parser.parse_args()

    if args.source in JOURNALS:
        venue = JOURNALS[args.source]
        password = site_password(venue)
        rows = journal_rows(crawl_journal(venue, ROOT / ".cache", refresh=args.refresh))
        ranked = 0
    else:
        if args.year is None:
            parser.error("a year is required for conferences")
        venue = VENUES[args.source](args.year)
        password = site_password(venue)  # fail fast, before any crawling
        submissions, reviews, decisions = crawl(venue, refresh=args.refresh)
        rows = build_rows(venue, submissions, reviews, decisions)
        ranked = sum(1 for r in rows if r[2] is not None)
    out = write_papers(venue, rows, password)
    write_page(venue)
    print(f"{len(rows)} papers ({ranked} ranked) -> {out}")


if __name__ == "__main__":
    main()
