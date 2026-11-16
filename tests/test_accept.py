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


def test_neurips_venue_ids_and_label():
    from crawler.venues import NeurIPS

    n = NeurIPS(2025)
    assert n.venue_id == "NeurIPS.cc/2025/Conference"
    assert n.slug == "neurips-2025"
    assert n.label == "NeurIPS 2025"
    assert n.review_invitation == "NeurIPS.cc/2025/Conference/-/Official_Review"
    assert n.decision_invitation == "NeurIPS.cc/2025/Conference/-/Decision"


def test_neurips_status_and_decision_text():
    from crawler.venues import NeurIPS

    n = NeurIPS(2025)
    assert accept_flag(n, venueid="NeurIPS.cc/2025/Conference", decision=None) == "A"
    assert accept_flag(n, venueid="NeurIPS.cc/2025/Conference/Rejected_Submission", decision=None) == "R"
    assert accept_flag(n, venueid=None, decision="Accept (poster)") == "A"
    assert accept_flag(n, venueid=None, decision="Reject") == "R"


def test_registry_and_partial_data_note():
    from crawler.venues import NeurIPS, VENUES

    assert set(VENUES) == {"iclr", "neurips", "icml", "uai", "clear"}
    assert "opted in" in NeurIPS(2025).note  # NeurIPS only publishes some papers
    assert V.note == ""  # ICLR publishes everything: no note


def test_icml_venue_uses_its_own_rating_field_and_partial_note():
    from crawler.venues import ICML

    m = ICML(2026)
    assert m.venue_id == "ICML.cc/2026/Conference"
    assert m.slug == "icml-2026"
    assert m.label == "ICML 2026"
    assert m.rating_field == "overall_recommendation"
    assert "opted in" in m.note
    assert accept_flag(m, venueid="ICML.cc/2026/Conference", decision=None) == "A"
    assert accept_flag(m, venueid="ICML.cc/2026/Conference/Rejected_Submission", decision=None) == "R"


def test_default_rating_field_is_rating():
    assert V.rating_field == "rating"


def test_uai_and_clear_venue_ids_and_accepted_only_note():
    from crawler.venues import CLeaR, UAI

    assert UAI(2026).venue_id == "auai.org/UAI/2026/Conference"
    assert CLeaR(2025).venue_id == "cclear.cc/CLeaR/2025/Conference"
    assert CLeaR(2025).slug == "clear-2025"
    assert "only accepted papers" in UAI(2026).note
