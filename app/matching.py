"""Fuzzy surname matching for free-typed quiz guesses.

Rules of thumb (documented here since they are a design assumption, not a
spec handed down by the user):

* Guesses are normalised (case-folded, accents stripped, punctuation and
  whitespace collapsed) before comparison so "guomundsson", "Gudmundsson"
  and "Guðmundsson" are all treated the same.
* A guess is CORRECT if, once normalised, it exactly matches one of a
  player's accepted answers (their surname, their full name, or - for the
  handful of multi-word surnames - the final word alone).
* A guess is CLOSE if it doesn't exactly match but scores >= CLOSE_THRESHOLD
  on a fuzzy ratio against the best-matching accepted answer. This is what
  catches minor typos/misspellings ("Guddmunson").
* Anything else is treated as WRONG (no useful match found).
* Guesses shorter than MIN_GUESS_LENGTH characters are never matched, to
  avoid short strings fuzzy-matching against many different surnames.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum

from rapidfuzz import fuzz

CLOSE_THRESHOLD = 70
MIN_GUESS_LENGTH = 3

# Characters that unicodedata's NFKD decomposition does not reduce to a
# plain ASCII letter (they are distinct letters, not accented variants),
# so they need an explicit transliteration.
_EXTRA_TRANSLITERATIONS = {
    "\u00f0": "d",  # ð -> d
    "\u00d0": "d",  # Ð -> d
    "\u00fe": "th",  # þ -> th
    "\u00de": "th",  # Þ -> th
    "\u00e6": "ae",  # æ -> ae
    "\u00c6": "ae",  # Æ -> ae
    "\u00f8": "o",  # ø -> o
    "\u00d8": "o",  # Ø -> o
    "\u0142": "l",  # ł -> l
    "\u0141": "l",  # Ł -> l
}


class MatchResult(Enum):
    CORRECT = "correct"
    CLOSE = "close"
    WRONG = "wrong"


@dataclass
class GuessOutcome:
    result: MatchResult
    player_index: int | None = None
    score: int = 0


def normalise(text: str) -> str:
    for original, replacement in _EXTRA_TRANSLITERATIONS.items():
        text = text.replace(original, replacement)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"['`’]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _best_score_against_player(guess_norm: str, answers: list[str]) -> int:
    best = 0
    for answer in answers:
        answer_norm = normalise(answer)
        if not answer_norm:
            continue
        score = fuzz.ratio(guess_norm, answer_norm)
        best = max(best, score)
    return best


def match_guess(guess: str, players, solved_indices: set[int]) -> GuessOutcome:
    """Match a free-typed guess against the unsolved players in a quiz.

    ``players`` is the full ordered list of Player objects for the quiz;
    ``solved_indices`` are indices already found so they're skipped.
    """
    guess_norm = normalise(guess)
    if len(guess_norm.replace(" ", "")) < MIN_GUESS_LENGTH:
        return GuessOutcome(MatchResult.WRONG)

    # First pass: look for an exact match (covers full names/surnames).
    for index, player in enumerate(players):
        if index in solved_indices:
            continue
        for answer in player.acceptable_answers:
            if normalise(answer) == guess_norm:
                return GuessOutcome(MatchResult.CORRECT, index, 100)

    # Second pass: fuzzy match to find a "close" candidate.
    best_index, best_score = None, 0
    for index, player in enumerate(players):
        if index in solved_indices:
            continue
        score = _best_score_against_player(guess_norm, player.acceptable_answers)
        if score > best_score:
            best_index, best_score = index, score

    if best_index is not None and best_score >= CLOSE_THRESHOLD:
        return GuessOutcome(MatchResult.CLOSE, best_index, best_score)

    return GuessOutcome(MatchResult.WRONG, None, best_score)
