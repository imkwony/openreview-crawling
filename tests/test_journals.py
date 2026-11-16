from pathlib import Path

from crawler.journals import JCI, build_rows, clean_title, crawl, published_month


def work(doi, title, authors=(), type_="journal-article", online=None):
    return {"DOI": doi, "title": [title], "type": type_,
            "published-online": {"date-parts": [online]} if online else None,
            "author": [{"given": g, "family": f} for g, f in authors]}


def test_clean_title_strips_markup_and_entities():
    assert clean_title("Do <i>causal</i>  effects &amp; bias\n matter?") == "Do causal effects & bias matter?"


def test_build_rows_uses_shared_row_format_and_skips_non_articles():
    rows = build_rows([
        work("10.1/b", "Beta", [("Ada", "Lovelace")], online=[2026, 4, 27]),
        work("10.1/a", "alpha", online=[2025, 11, 2]),
        work("10.1/c", "A review", type_="other"),
        {"DOI": "10.1/d", "type": "journal-article"},  # no title
    ])
    assert rows == [
        ["10.1/b", "Beta", None, None, None, "A", ["Ada Lovelace"], 202604],  # newest first
        ["10.1/a", "alpha", None, None, None, "A", [], 202511],
    ]


def test_published_month_prefers_online_then_print_then_issued():
    base = {"issued": {"date-parts": [[2026, 1, 1]]}}
    assert published_month({**base, "published-online": {"date-parts": [[2026, 4, 27]]}}) == 202604
    assert published_month({**base, "published-print": {"date-parts": [[2025, 12]]}}) == 202512
    assert published_month(base) == 202601
    assert published_month({"issued": {"date-parts": [[2019]]}}) == 201901
    assert published_month({}) is None


def test_crawl_follows_cursor_until_empty_and_caches(tmp_path: Path):
    pages = [
        {"message": {"items": [work("10.1/a", "A")], "next-cursor": "c1"}},
        {"message": {"items": [work("10.1/b", "B")], "next-cursor": "c2"}},
        {"message": {"items": [], "next-cursor": "c3"}},
    ]
    calls = []

    class Resp:
        def __init__(self, body): self.body = body
        def raise_for_status(self): pass
        def json(self): return self.body

    def get(url, params):
        calls.append(params["cursor"])
        return Resp(pages[len(calls) - 1])

    items = crawl(JCI, tmp_path, get=get, sleep=lambda: None)
    assert [i["DOI"] for i in items] == ["10.1/a", "10.1/b"]
    assert calls == ["*", "c1", "c2"]
    assert crawl(JCI, tmp_path, get=None, sleep=lambda: None) == items  # served from cache
