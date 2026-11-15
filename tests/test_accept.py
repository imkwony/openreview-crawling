from crawler.venues import ICLR, accept_flag

V = ICLR(2027)
SUB = "ICLR.cc/2027/Conference/Submission"


def test_venue_ids():
    assert V.venue_id == "ICLR.cc/2027/Conference"
    assert V.submission_invitation == "ICLR.cc/2027/Conference/-/Submission"
    assert V.review_invitation == "ICLR.cc/2027/Conference/-/Official_Review"
    assert V.decision_invitation == "ICLR.cc/2027/Conference/-/Decision"


def test_status_from_venueid():
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference", decision=None) == "A"
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference/Rejected_Submission", decision=None) == "R"
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference/Withdrawn_Submission", decision=None) == "W"
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference/Desk_Rejected_Submission", decision=None) == "D"


def test_undecided_is_under_review():
    assert accept_flag(V, venueid=SUB, decision=None) == "U"
    assert accept_flag(V, venueid=None, decision=None) == "U"


def test_decision_text_fallback():
    assert accept_flag(V, venueid=SUB, decision="Accept (Oral)") == "A"
    assert accept_flag(V, venueid=SUB, decision="Accept (Poster)") == "A"
    assert accept_flag(V, venueid=SUB, decision="Reject") == "R"
    assert accept_flag(V, venueid=SUB, decision="something odd") == "U"
