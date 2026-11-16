"""Per-conference settings. Add a new class here to support another venue."""
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenReviewVenue:
    """Naming conventions shared by OpenReview conferences (override per venue)."""

    prefix: str  # e.g. "ICLR.cc"
    name: str  # e.g. "ICLR"
    year: int
    review_name: str = "Official_Review"
    decision_name: str = "Decision"
    rating_field: str = "rating"  # name of the score field in this venue's review form
    note: str = ""  # shown on the page when OpenReview only exposes part of the data

    @property
    def label(self):
        """Display name, e.g. "ICLR 2027"."""
        return f"{self.name} {self.year}"

    @property
    def slug(self):
        return f"{self.name.lower()}-{self.year}"

    @property
    def venue_id(self):
        return f"{self.prefix}/{self.year}/Conference"

    @property
    def submission_invitation(self):
        return f"{self.venue_id}/-/Submission"

    @property
    def review_invitation(self):
        return f"{self.venue_id}/-/{self.review_name}"

    @property
    def decision_invitation(self):
        return f"{self.venue_id}/-/{self.decision_name}"

    @property
    def status_by_venueid(self):
        """Where OpenReview files a paper once it is decided -> status code."""
        return {
            self.venue_id: "A",
            f"{self.venue_id}/Rejected_Submission": "R",
            f"{self.venue_id}/Withdrawn_Submission": "W",
            f"{self.venue_id}/Desk_Rejected_Submission": "D",
        }


def ICLR(year):
    return OpenReviewVenue(prefix="ICLR.cc", name="ICLR", year=year)


# Some venues keep submissions private: only accepted papers, and rejected papers
# whose authors opted in, are public. Make the page say so.
_OPT_IN_NOTE = (
    " Only accepted papers and rejected papers whose authors opted in to"
    " public release are listed, so this is not every submission."
)


def NeurIPS(year):
    return OpenReviewVenue(prefix="NeurIPS.cc", name="NeurIPS", year=year, note=_OPT_IN_NOTE)


def ICML(year):
    return OpenReviewVenue(prefix="ICML.cc", name="ICML", year=year,
                           rating_field="overall_recommendation", note=_OPT_IN_NOTE)


# Only accepted papers are public here, and there are no public reviews or decisions.
_ACCEPTED_ONLY_NOTE = (
    " OpenReview lists only accepted papers for this conference and has no public"
    " reviews, so Rank is empty."
)


def UAI(year):
    return OpenReviewVenue(prefix="auai.org/UAI", name="UAI", year=year, note=_ACCEPTED_ONLY_NOTE)


def CLeaR(year):
    return OpenReviewVenue(prefix="cclear.cc/CLeaR", name="CLeaR", year=year, note=_ACCEPTED_ONLY_NOTE)


def COLM(year):
    return OpenReviewVenue(prefix="colmweb.org/COLM", name="COLM", year=year,
                           note=" OpenReview lists only accepted papers for this conference, so this is not every submission.")


VENUES = {"iclr": ICLR, "neurips": NeurIPS, "icml": ICML, "uai": UAI, "clear": CLeaR, "colm": COLM}


def accept_flag(venue, venueid, decision):
    """Status code: A accepted, R rejected, W withdrawn, D desk-rejected, U under review."""
    status = venue.status_by_venueid.get(venueid)
    if status:
        return status
    if decision:
        text = decision.strip().lower()
        if text.startswith("accept"):
            return "A"
        if text.startswith("reject"):
            return "R"
    return "U"
