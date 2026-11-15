from crawler.venues import ICLR, accept_flag

V = ICLR(2027)


def test_venue_ids():
    assert V.venue_id == "ICLR.cc/2027/Conference"
    assert V.submission_invitation == "ICLR.cc/2027/Conference/-/Submission"
    assert V.review_invitation == "ICLR.cc/2027/Conference/-/Official_Review"
    assert V.decision_invitation == "ICLR.cc/2027/Conference/-/Decision"


def test_accept_from_venueid():
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference", decision=None) == 1
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference/Rejected_Submission", decision=None) == 0
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference/Desk_Rejected_Submission", decision=None) == 0
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference/Withdrawn_Submission", decision=None) == 0


def test_undecided_is_unknown():
    assert accept_flag(V, venueid="ICLR.cc/2027/Conference/Submission", decision=None) is None


def test_decision_text_fallback():
    sub = "ICLR.cc/2027/Conference/Submission"
    assert accept_flag(V, venueid=sub, decision="Accept (Oral)") == 1
    assert accept_flag(V, venueid=sub, decision="Accept (Poster)") == 1
    assert accept_flag(V, venueid=sub, decision="Reject") == 0
    assert accept_flag(V, venueid=sub, decision="something odd") is None
