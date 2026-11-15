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


VENUES = {"iclr": ICLR}


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
