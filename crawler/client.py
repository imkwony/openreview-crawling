"""OpenReview login and polite, throttled pagination."""
import os
import random
import time

BASEURL = "https://api2.openreview.net"
PAGE_SIZE = 1000
MIN_DELAY, MAX_DELAY = 2.0, 3.0  # seconds between API calls


def random_pause(sleep=time.sleep):
    sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def paginate(fetch, page_size=PAGE_SIZE, sleep=random_pause):
    """Yield every item from fetch(limit=, offset=), pausing before each request."""
    offset = 0
    while True:
        sleep()
        batch = fetch(limit=page_size, offset=offset)
        yield from batch
        if len(batch) < page_size:
            return
        offset += page_size


def login():
    """Log in with OPENREVIEW_USERNAME / OPENREVIEW_PASSWORD from the environment or .env."""
    import openreview
    from dotenv import load_dotenv

    load_dotenv()
    username = os.getenv("OPENREVIEW_USERNAME")
    password = os.getenv("OPENREVIEW_PASSWORD")
    if not username or not password:
        raise SystemExit("Set OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD in .env (see .env.example).")
    random_pause()
    return openreview.api.OpenReviewClient(baseurl=BASEURL, username=username, password=password)
