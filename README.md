# OpenReview Crawling

Ranked submission lists for ML conferences, served as a static site on GitHub Pages.
Each conference page is a searchable, sortable table of papers with their rank (from
reviewer ratings) and whether they were accepted.

Currently available: **ICLR 2027**, **ICLR 2026**, **NeurIPS 2025**.

NeurIPS keeps submissions private, so its page lists only accepted papers and rejected
papers whose authors opted in to public release (the page says so). NeurIPS 2026 has no
public data on OpenReview yet.

## Credits

- Data is collected with the [OpenReview Python API (`openreview-py`)](https://github.com/openreview/openreview-py).
- The idea comes from <https://hrrs.ai/iclr-2027/>. This project is an independent
  implementation; no code was copied from that site.

## How it works

```
python -m crawler iclr 2027   ->   iclr-2027/papers.enc.json   ->   iclr-2027/index.html (static)
```

The data is a list of rows: `[paperId, title, rank, rankByAI, aiWritten, accept, keywords]`. It is
published only in encrypted form (`papers.enc.json`); a plaintext copy stays in `.cache/`.

| Column | Meaning |
|---|---|
| Keywords | The keywords authors gave their submission. Search matches title, keywords and paper ID. Hidden on narrow screens (still searchable). |
| Rank | Papers ordered by the average of reviewer ratings (highest first). Equal averages share a rank (1, 1, 3). Unreviewed papers are blank. |
| Rank-by-AI, AI-Written?-by-AI | Reserved for model outputs. Empty until a model is chosen. |
| Accept | Status per paper: ✅ accepted, ❌ rejected, 🏳️ withdrawn, 🙅‍♂️🙅‍♀️ desk-rejected, ⏳ under review. Stored as codes `A`/`R`/`W`/`D`/`U`. Click the header to show only the statuses you pick (it combines with search). |

## Data encryption

The data file is gzip + AES-256-GCM encrypted (key derived with PBKDF2-SHA256) and the
browser decrypts it. `crawler/crypto.py` and `assets/table.js` must stay in sync.

## Layout

```
index.html            landing page with links to each conference
assets/table.{css,js} shared table UI used by every conference page
iclr-2027/            one folder per conference-year: index.html + papers.enc.json
crawler/              OpenReview crawler (client, ranking, encryption, per-venue settings, CLI)
tests/                pytest tests
```

## Run the crawler

Requires Python 3.12 (`openreview-py` has no wheel for 3.14 yet).

```bash
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env     # then fill in your OpenReview username and password
.venv/Scripts/python -m crawler iclr 2027
```

- Credentials live only in `.env`, which is git-ignored.
- The crawler waits a random 2-3 seconds before every API call.
- Raw responses are cached in `.cache/` (git-ignored) so an interrupted run resumes;
  use `--refresh` to fetch everything again. With a complete cache the command makes no
  API calls and just rebuilds the encrypted file.

Run the tests with `.venv/Scripts/python -m pytest`.

## Add another conference

1. New year of a supported conference: no code change. A new conference: add a venue in
   `crawler/venues.py` and register it in `VENUES`.
2. Add `SITE_PASSWORD_<NAME>_<YEAR>` to `.env` (see `.env.example`).
3. Run `python -m crawler <conference> <year>`. It writes `<conference>-<year>/papers.enc.json`
   and `<conference>-<year>/index.html` (rendered from `crawler/templates/conference.html`).
4. Turn its greyed-out entry in the root `index.html` into a link.

## Deploy

Push to GitHub and enable Pages (Settings, Pages, branch `main`, folder `/`).
`.nojekyll` is included so files are served as-is.
