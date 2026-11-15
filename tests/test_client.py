from crawler.client import paginate, random_pause


def test_paginate_collects_all_pages_and_sleeps_before_each_call():
    data = list(range(2500))
    calls, sleeps = [], []

    def fetch(limit, offset):
        calls.append((limit, offset))
        return data[offset : offset + limit]

    out = list(paginate(fetch, page_size=1000, sleep=lambda: sleeps.append(1)))
    assert out == data
    assert calls == [(1000, 0), (1000, 1000), (1000, 2000)]
    assert len(sleeps) == len(calls)  # one pause before every request


def test_paginate_exact_multiple_stops_on_empty_page():
    data = list(range(2000))
    calls = []

    def fetch(limit, offset):
        calls.append(offset)
        return data[offset : offset + limit]

    assert list(paginate(fetch, page_size=1000, sleep=lambda: None)) == data
    assert calls == [0, 1000, 2000]


def test_random_pause_is_between_two_and_three_seconds():
    slept = []
    for _ in range(50):
        random_pause(sleep=slept.append)
    assert all(2.0 <= s <= 3.0 for s in slept)
