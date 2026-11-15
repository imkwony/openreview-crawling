from crawler.ranking import parse_rating, assign_ranks


def test_parse_rating_variants():
    assert parse_rating(6) == 6
    assert parse_rating("6: marginally above the acceptance threshold") == 6
    assert parse_rating(" 10") == 10
    assert parse_rating("n/a") is None
    assert parse_rating(None) is None


def test_average_ranking_higher_is_better():
    ratings = {"a": [6, 6], "b": [8, 4, 6], "c": [2]}
    rows = assign_ranks(ratings)
    assert rows["a"] == rows["b"] == 1  # 6.0 == 6.0, shared rank
    assert rows["c"] == 3  # competition ranking: 1, 1, 3


def test_exact_ties_not_broken_by_float_error():
    # 1/3 + 1/3 + 1/3 style averages must tie exactly
    ratings = {"x": [5, 5, 6], "y": [6, 5, 5], "z": [6, 6, 6]}
    ranks = assign_ranks(ratings)
    assert ranks["z"] == 1
    assert ranks["x"] == ranks["y"] == 2


def test_unreviewed_papers_have_no_rank():
    ratings = {"a": [4], "b": []}
    ranks = assign_ranks(ratings)
    assert ranks["a"] == 1
    assert ranks["b"] is None
