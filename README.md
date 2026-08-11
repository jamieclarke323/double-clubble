# Double Clubble

A web quiz for Charlton Athletic fans: for each 2026/27 Championship away
fixture, name as many players as you can who have played for **both**
Charlton Athletic and that day's opponent.

Data is parsed directly from `data_source.xlsx` (sheet `DoubleClubble`,
plus the `AwayFixtures` sheet for venues) - there's no separate data entry
step. Add/edit rows in the spreadsheet and restart the app to pick up
changes.

## Features

- Home page listing all 24 Charlton away fixtures for 2026/27, in date order.
- Each fixture links to its quiz. A quiz unlocks at **7:00am UK time** on
  its fixture date and stays unlocked forever after that - clicking a
  future quiz shows the exact unlock date/time instead.
- Free-typed guesses, matched against player **surnames** with fuzzy
  matching so small typos still count, and near-misses are told they're
  "close".
- A clues modal - tick any of Apps / Years / Goals to reveal that data
  (from the spreadsheet) for every player you haven't found yet.
- A "give up" option with a confirmation step that reveals every answer.
- A congratulations message when every player in a quiz has been found.
- Progress (which players you've found) is remembered per-browser via a
  session cookie, so refreshing or coming back later doesn't lose it.
- Red / white / black theme, Futura Bold typography throughout.

## Project layout

```
double-clubble/
  app/
    __init__.py      # Flask app factory
    data_loader.py    # Parses the spreadsheet into Quiz/Player objects
    matching.py       # Fuzzy surname matching logic
    progress.py        # Session-based per-quiz progress tracking
    routes.py         # All Flask routes/API endpoints
    templates/         # Jinja2 templates
    static/            # CSS + JS
  tests/               # pytest test suite
  data_source.xlsx      # The quiz data spreadsheet
  requirements.txt
  run.py                 # Local dev entrypoint
```

## Setup (local)

```bash
cd double-clubble
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Then open http://127.0.0.1:5000 in a browser.

By default the app reads `data_source.xlsx` in the project root. To point
at a different spreadsheet, set the `QUIZ_XLSX_PATH` environment variable.
Set `SECRET_KEY` to a random value for anything beyond local testing (this
signs the session cookie that stores quiz progress). Set
`SESSION_COOKIE_SECURE=1` once the app is served over HTTPS so the
progress cookie is never sent unencrypted.

## Running the tests

```bash
source .venv/bin/activate
python -m pytest
```

Tests cover: quiz unlock/lock timing (before/at/after 7am, and staying
unlocked afterwards), all 24 fixtures loading correctly, surname
normalisation and fuzzy matching (exact, close-misspelling, unrelated,
multi-word surnames, short-guess guard), and the guess/clue/give-up API
routes end-to-end (including that give-up requires confirmation and
completion triggers `completed: true`).

## Deploying so it's reachable on the web

The app is a standard Flask app (`run.py` exposes `app`), so it will run
on any Python host that supports WSGI apps (Render, PythonAnywhere,
Railway, Fly.io, a VPS with gunicorn, etc.). In production, run it behind
a real WSGI server rather than the Flask dev server, e.g.:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 run:app
```

Make sure `data_source.xlsx` is deployed alongside the code (or set
`QUIZ_XLSX_PATH` to wherever it lives), and set a real `SECRET_KEY`
environment variable. Happy to walk through click-by-click deployment
steps for a specific host (e.g. Render or PythonAnywhere) once you've
picked one.

On PythonAnywhere specifically, no separate WSGI server is needed - the
platform imports `app` from `run.py` directly, so it's enough to:

1. Clone/upload the project into your PythonAnywhere home directory.
2. Create a virtualenv (Python 3.10+) and `pip install -r requirements.txt`.
3. Set the `SECRET_KEY`, `SESSION_COOKIE_SECURE=1` and `SITE_URL`
   environment variables (via the Web tab's "Environment variables"
   section, or at the top of the WSGI config file).
4. Point the web app's WSGI config file at `run:app` and reload.

## Design assumptions (documented, since the source data left some things open to interpretation)

- **Unlock timezone**: "7am" is treated as UK local time (`Europe/London`,
  so it correctly follows BST/GMT), since Charlton Athletic are a UK club.
- **Surname extraction**: the answer is normally the last word of a
  player's name (e.g. "Guðmundsson" for "Jóhann Berg Guðmundsson"). A
  small number of players have genuinely multi-word surnames where the
  final word alone would be a different/obscure name; these are called
  out explicitly in `MULTI_WORD_SURNAMES` in `app/data_loader.py` (e.g.
  "Tal Ben Haim" -> "Ben Haim", "Paolo Di Canio" -> "Di Canio"). Both the
  full multi-word surname and the final word alone are accepted as correct
  answers for these players, and the full name is always accepted too.
- **Fuzzy matching thresholds** (`app/matching.py`): an exact match (after
  lower-casing, accent-stripping and punctuation removal) is "correct". A
  fuzzy ratio of 70+ against the closest unsolved player is treated as
  "close" (typo/misspelling territory). Below that, or for guesses under 3
  characters, the guess is just "not a match". These thresholds were
  tuned by testing against the actual player list to avoid false "close"
  matches on unrelated words.
- **Progress storage**: there's no login/account system in the brief, so
  "the user should be able to keep playing without losing found answers"
  is implemented as per-browser progress via a signed session cookie,
  rather than a database-backed account system.
- **Futura Bold licensing**: Futura is a commercial font and isn't bundled
  with the app. The stylesheet declares `Futura Bold` first (so it's used
  automatically if a visitor already has it installed) and falls back to
  Century Gothic / Trebuchet MS / sans-serif, which are visually close
  free/system alternatives.
- **Clue display**: clues are shown as "Charlton: X / Opponent: Y" so you
  can compare both spells at a glance, rather than only the requested
  club's figures - this seemed more useful without changing what data is
  revealed.
