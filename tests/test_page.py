from pathlib import Path

from crawler.page import render_page
from crawler.venues import ICLR

ROOT = Path(__file__).resolve().parent.parent


def test_label():
    assert ICLR(2026).label == "ICLR 2026"


def test_template_reproduces_the_committed_iclr_2027_page():
    assert render_page(ICLR(2027)) == (ROOT / "iclr-2027" / "index.html").read_text(encoding="utf-8")


def test_other_year_page_uses_its_own_label_only():
    html = render_page(ICLR(2026))
    assert "ICLR 2026 Submissions Ranked" in html
    assert "2027" not in html
    assert "{{" not in html


def test_neurips_page_shows_label_and_partial_data_note():
    from crawler.venues import NeurIPS

    html = render_page(NeurIPS(2025))
    assert "NeurIPS 2025 Submissions Ranked" in html
    assert "opted in" in html
    assert "ICLR" not in html
    assert "{{" not in html
