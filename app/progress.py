"""Per-browser quiz progress, stored in the signed Flask session cookie.

No accounts/login were requested, so progress is scoped to the visitor's
browser session cookie. This is enough to satisfy "the user should be able
to keep playing the same quiz without losing already found answers" for a
single browser, while keeping the app stateless on the server.
"""

from __future__ import annotations

from flask import session

SESSION_KEY = "quiz_progress"


def _all_progress() -> dict:
    # Mark the session permanent so Flask enforces PERMANENT_SESSION_LIFETIME
    # (48 hours) server-side, forgetting progress after that long without a
    # visit rather than relying only on the cookie's client-side expiry.
    session.permanent = True
    return session.setdefault(SESSION_KEY, {})


def get_quiz_progress(quiz_id: str) -> dict:
    progress = _all_progress()
    quiz_state = progress.setdefault(
        quiz_id, {"solved": [], "given_up": False}
    )
    return quiz_state


def _save_quiz_progress(quiz_id: str, quiz_state: dict) -> None:
    progress = _all_progress()
    progress[quiz_id] = quiz_state
    session[SESSION_KEY] = progress
    session.modified = True


def mark_solved(quiz_id: str, player_index: int) -> dict:
    state = get_quiz_progress(quiz_id)
    if player_index not in state["solved"]:
        state["solved"].append(player_index)
    _save_quiz_progress(quiz_id, state)
    return state


def mark_given_up(quiz_id: str) -> dict:
    state = get_quiz_progress(quiz_id)
    state["given_up"] = True
    _save_quiz_progress(quiz_id, state)
    return state


def reset_quiz_progress(quiz_id: str) -> dict:
    state = {"solved": [], "given_up": False}
    _save_quiz_progress(quiz_id, state)
    return state


def solved_indices(quiz_id: str) -> set[int]:
    return set(get_quiz_progress(quiz_id)["solved"])
