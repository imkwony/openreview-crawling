from pathlib import Path

from crawler.journals import JCI, build_rows, clean_title, crawl


def work(doi, title, authors=(), type_="journal-article"):
    return {"DOI": doi, "title": [title], "type": type_,
            "author": [{"given": g, "family": f} for g, f in authors]}


def test_clean_title_strips_markup_and_entities():
    assert clean_title("Do <i>causal</i>  effects &amp; bias\n matter?") == "Do causal effects & bias matter?"


def test_build_rows_uses_shared_row_format_and_skips_non_articles():
    rows = build_rows([
        work("10.1/b", "Beta", [("Ada", "Lovelace")]),
        work("10.1/a", "alpha"),
        work("10.1/c", "A review", type_="other"),
        {"DOI": "10.1/d", "type": "journal-article"},  # no title
    ])
    assert rows == [
        ["10.1/a", "alpha", None, None, None, "A", []],
        ["10.1/b", "Beta", None, None, None, "A", ["Ada Lovelace"]],
    ]


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
