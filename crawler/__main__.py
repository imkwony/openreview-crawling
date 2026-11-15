"""Usage: python -m crawler iclr 2027 [--refresh]"""
import argparse

from .build import build_rows, crawl, write_papers
from .venues import VENUES


def main():
    parser = argparse.ArgumentParser(description="Crawl a conference from OpenReview.")
    parser.add_argument("conference", choices=sorted(VENUES))
    parser.add_argument("year", type=int)
    parser.add_argument("--refresh", action="store_true", help="ignore the .cache/ copy and refetch")
    args = parser.parse_args()

    venue = VENUES[args.conference](args.year)
    submissions, reviews, decisions = crawl(venue, refresh=args.refresh)
    rows = build_rows(venue, submissions, reviews, decisions)
    out = write_papers(venue, rows)
    reviewed = sum(1 for r in rows if r[2] is not None)
    print(f"{len(rows)} papers ({reviewed} ranked) -> {out}")


if __name__ == "__main__":
    main()
