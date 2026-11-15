from crawler.build import build_rows
from crawler.venues import ICLR

V = ICLR(2027)
SUB = "ICLR.cc/2027/Conference/Submission"


def test_build_rows_shape_and_values():
    submissions = [
        {"id": "p1", "title": "Beta", "venueid": V.venue_id},
        {"id": "p2", "title": "Alpha", "venueid": SUB},
        {"id": "p3", "title": "Gamma", "venueid": f"{V.venue_id}/Rejected_Submission"},
    ]
    reviews = [
        {"forum": "p1", "rating": "8: accept"},
        {"forum": "p1", "rating": 6},
        {"forum": "p2", "rating": 6},
        {"forum": "ghost", "rating": 10},  # review for unknown paper is ignored
    ]
    decisions = []
    rows = build_rows(V, submissions, reviews, decisions)
    # [id, title, rank, rank_by_ai, ai_written, accept]
    assert rows == [
        ["p1", "Beta", 1, None, None, 1],
        ["p2", "Alpha", 2, None, None, None],
        ["p3", "Gamma", None, None, None, 0],
    ]


def test_ties_listed_alphabetically_and_decision_text_used():
    submissions = [
        {"id": "b", "title": "banana", "venueid": SUB},
        {"id": "a", "title": "Apple", "venueid": SUB},
    ]
    reviews = [{"forum": "a", "rating": 5}, {"forum": "b", "rating": 5}]
    decisions = [{"forum": "a", "decision": "Accept (Poster)"}]
    rows = build_rows(V, submissions, reviews, decisions)
    assert [r[0] for r in rows] == ["a", "b"]  # same rank 1, alphabetical
    assert rows[0][2] == rows[1][2] == 1
    assert rows[0][5] == 1 and rows[1][5] is None
