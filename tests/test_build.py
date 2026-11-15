from crawler.build import build_rows, normalize_keywords, review_rating
from crawler.venues import ICLR

V = ICLR(2027)
SUB = "ICLR.cc/2027/Conference/Submission"


def test_build_rows_shape_and_values():
    submissions = [
        {"id": "p1", "title": "Beta", "venueid": V.venue_id, "keywords": ["rl", "robotics"]},
        {"id": "p2", "title": "Alpha", "venueid": SUB},  # no keywords field at all
        {"id": "p3", "title": "Gamma", "venueid": f"{V.venue_id}/Rejected_Submission", "keywords": "nlp, agents"},
    ]
    reviews = [
        {"forum": "p1", "rating": "8: accept"},
        {"forum": "p1", "rating": 6},
        {"forum": "p2", "rating": 6},
        {"forum": "ghost", "rating": 10},  # review for unknown paper is ignored
    ]
    decisions = []
    rows = build_rows(V, submissions, reviews, decisions)
    # [id, title, rank, rank_by_ai, ai_written, accept, keywords]
    assert rows == [
        ["p1", "Beta", 1, None, None, "A", ["rl", "robotics"]],
        ["p2", "Alpha", 2, None, None, "U", []],
        ["p3", "Gamma", None, None, None, "R", ["nlp", "agents"]],
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
    assert rows[0][5] == "A" and rows[1][5] == "U"


def test_write_papers_outputs_only_encrypted_file_in_site_folder(tmp_path):
    import json

    from crawler.build import write_papers
    from crawler.crypto import decrypt_payload

    rows = [["p1", "Secret Title", 1, None, None, None]]
    out = write_papers(V, rows, "Test Secret", root=tmp_path)
    assert out == tmp_path / "iclr-2027" / "papers.enc.json"
    assert not (tmp_path / "iclr-2027" / "papers.json").exists()
    assert "Secret Title" not in out.read_text(encoding="utf-8")
    assert json.loads(decrypt_payload(json.loads(out.read_text(encoding="utf-8")), "Test Secret")) == rows
    # plaintext copy stays in the git-ignored cache
    assert (tmp_path / ".cache" / "iclr-2027" / "papers.json").exists()


def test_site_password_comes_from_env(monkeypatch):
    import pytest

    from crawler import build

    monkeypatch.setattr(build, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("SITE_PASSWORD_ICLR_2027", "from env")
    assert build.site_password(V) == "from env"
    monkeypatch.delenv("SITE_PASSWORD_ICLR_2027")
    with pytest.raises(SystemExit):
        build.site_password(V)


def test_normalize_keywords():
    assert normalize_keywords(["a", " b ", "", None]) == ["a", "b"]
    assert normalize_keywords("x, y ,, z") == ["x", "y", "z"]
    assert normalize_keywords(None) == []
    assert normalize_keywords(42) == []


def test_review_rating_reads_the_venue_specific_field():
    from crawler.venues import ICML

    content = {"rating": {"value": 3}, "overall_recommendation": {"value": 5}}
    assert review_rating(V, content) == 3
    assert review_rating(ICML(2026), content) == 5
    assert review_rating(ICML(2026), {}) is None
