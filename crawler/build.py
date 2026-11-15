"""Crawl one venue from OpenReview and write the site's papers.json."""
import json
from pathlib import Path

from .client import login, paginate
from .ranking import assign_ranks, parse_rating
from .venues import accept_flag

ROOT = Path(__file__).resolve().parent.parent


def build_rows(venue, submissions, reviews, decisions):
    """Rows: [id, title, rank, rank_by_ai, ai_written, accept]; the AI columns stay null."""
    known = {s["id"] for s in submissions}
    ratings = {s["id"]: [] for s in submissions}
    for review in reviews:
        value = parse_rating(review.get("rating"))
        if review["forum"] in known and value is not None:
            ratings[review["forum"]].append(value)
    ranks = assign_ranks(ratings)
    decision_text = {d["forum"]: d.get("decision") for d in decisions}

    rows = [
        [
            s["id"],
            s["title"],
            ranks[s["id"]],
            None,
            None,
            accept_flag(venue, s.get("venueid"), decision_text.get(s["id"])),
        ]
        for s in submissions
    ]
    rows.sort(key=lambda r: (r[2] is None, r[2] or 0, r[1].lower(), r[0]))
    return rows


def _value(content, key):
    field = content.get(key)
    return field.get("value") if isinstance(field, dict) else field


def _cached(path, refresh, produce):
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    data = produce()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def crawl(venue, refresh=False):
    """Fetch submissions, reviews and decisions (cached in .cache/ so a rerun resumes)."""
    cache = ROOT / ".cache" / venue.slug
    client = login()

    def notes(invitation, parent=False, **extra):
        # Reviews and decisions live under per-paper invitations (Submission<N>/-/Official_Review),
        # so they are found through their shared parent invitation, not by exact match.
        key = "parent_invitations" if parent else "invitation"
        return paginate(lambda limit, offset: client.get_notes(
            **{key: invitation}, limit=limit, offset=offset, **extra))

    def fetch_submissions():
        out = []
        for n in notes(venue.submission_invitation, sort="number:asc"):
            out.append({"id": n.id, "title": _value(n.content, "title") or "",
                        "venueid": _value(n.content, "venueid")})
            if len(out) % 5000 == 0:
                print(f"  submissions: {len(out)}", flush=True)
        return out

    def fetch_reviews():
        return [{"forum": n.forum, "rating": _value(n.content, "rating")}
                for n in notes(venue.review_invitation, parent=True)]

    def fetch_decisions():
        return [{"forum": n.forum, "decision": _value(n.content, "decision")}
                for n in notes(venue.decision_invitation, parent=True)]

    print("Fetching submissions...", flush=True)
    submissions = _cached(cache / "submissions.json", refresh, fetch_submissions)
    print("Fetching reviews...", flush=True)
    reviews = _cached(cache / "reviews.json", refresh, fetch_reviews)
    print("Fetching decisions...", flush=True)
    decisions = _cached(cache / "decisions.json", refresh, fetch_decisions)
    return submissions, reviews, decisions


def write_papers(venue, rows):
    out = ROOT / venue.slug / "papers.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out
