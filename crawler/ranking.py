"""Rank papers by the average of their reviewers' ratings."""
import re
from fractions import Fraction

_LEADING_INT = re.compile(r"^\s*(-?\d+)")


def parse_rating(value):
    """Return an int rating from OpenReview content ('6: marginally above...' or 6)."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    match = _LEADING_INT.match(str(value))
    return int(match.group(1)) if match else None


def assign_ranks(ratings_by_paper):
    """Map paper id -> rank (1 = highest average), or None when unreviewed.

    Competition ranking: papers with the same average share a rank and the
    next rank skips ahead (1, 1, 3). Averages use exact fractions so ties are
    never broken by floating-point error.
    """
    averages = {
        pid: Fraction(sum(r), len(r)) for pid, r in ratings_by_paper.items() if r
    }
    ordered = sorted(averages.values(), reverse=True)
    first_position = {}
    for position, avg in enumerate(ordered, start=1):
        first_position.setdefault(avg, position)
    return {pid: first_position[averages[pid]] if pid in averages else None
            for pid in ratings_by_paper}
