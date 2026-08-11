from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request

from .data_loader import Quiz, QUIZ_TIMEZONE
from .matching import MatchResult, match_guess
from . import progress as progress_store

bp = Blueprint("quiz", __name__)


@bp.app_context_processor
def inject_site_info():
    return {
        "site_name": current_app.config["SITE_NAME"],
        "site_url": current_app.config["SITE_URL"],
    }


def _quizzes() -> list[Quiz]:
    return current_app.config["QUIZZES"]


def _quiz_or_404(quiz_id: str):
    quiz = current_app.config["QUIZZES_BY_ID"].get(quiz_id)
    return quiz


def _is_quiz_unlocked(quiz: Quiz, now: datetime | None = None) -> bool:
    if current_app.config.get("BYPASS_UNLOCK", False):
        return True
    return quiz.is_unlocked(now)


def _player_public_dict(player, index: int) -> dict:
    return {
        "index": index,
        "name": player.name,
        "position": player.position,
        "years_charlton": player.years_charlton,
        "apps_charlton": player.apps_charlton,
        "goals_charlton": player.goals_charlton,
        "years_opponent": player.years_opponent,
        "apps_opponent": player.apps_opponent,
        "goals_opponent": player.goals_opponent,
    }


@bp.route("/")
def index():
    now = datetime.now(QUIZ_TIMEZONE)
    fixtures = []
    for quiz in _quizzes():
        fixtures.append(
            {
                "quiz": quiz,
                "unlocked": _is_quiz_unlocked(quiz, now),
            }
        )
    return render_template("index.html", fixtures=fixtures, now=now)


@bp.route("/quiz/<quiz_id>")
def quiz_page(quiz_id: str):
    quiz = _quiz_or_404(quiz_id)
    if quiz is None:
        return render_template("not_found.html", quiz_id=quiz_id), 404

    now = datetime.now(QUIZ_TIMEZONE)
    if not _is_quiz_unlocked(quiz, now):
        return render_template("locked.html", quiz=quiz, now=now)

    state = progress_store.get_quiz_progress(quiz_id)
    solved = set(state["solved"])
    given_up = state["given_up"]

    players_view = []
    for index, player in enumerate(quiz.players):
        if index in solved or given_up:
            players_view.append({"found": True, **_player_public_dict(player, index)})
        else:
            players_view.append({"found": False, "index": index})

    completed = len(solved) >= quiz.total_players

    return render_template(
        "quiz.html",
        quiz=quiz,
        players_view=players_view,
        solved_count=len(solved),
        total=quiz.total_players,
        completed=completed,
        given_up=given_up,
    )


@bp.route("/quiz/<quiz_id>/guess", methods=["POST"])
def submit_guess(quiz_id: str):
    quiz = _quiz_or_404(quiz_id)
    if quiz is None:
        return jsonify({"status": "error", "message": "Unknown quiz."}), 404
    if not _is_quiz_unlocked(quiz):
        return jsonify({"status": "locked", "message": "This quiz is not unlocked yet."}), 403

    data = request.get_json(silent=True) or {}
    guess = str(data.get("guess", "")).strip()
    if not guess:
        return jsonify({"status": "wrong", "message": "Type a surname to guess."})

    state = progress_store.get_quiz_progress(quiz_id)
    solved = set(state["solved"])

    if state["given_up"] or len(solved) >= quiz.total_players:
        return jsonify({"status": "already_complete", "message": "This quiz is already finished."})

    outcome = match_guess(guess, quiz.players, solved)

    if outcome.result == MatchResult.CORRECT:
        progress_store.mark_solved(quiz_id, outcome.player_index)
        player = quiz.players[outcome.player_index]
        new_solved_count = len(solved) + 1
        completed = new_solved_count >= quiz.total_players
        return jsonify(
            {
                "status": "correct",
                "message": f"Correct! {player.name} played for both clubs.",
                "player": _player_public_dict(player, outcome.player_index),
                "solved_count": new_solved_count,
                "total": quiz.total_players,
                "completed": completed,
            }
        )

    if outcome.result == MatchResult.CLOSE:
        progress_store.mark_solved(quiz_id, outcome.player_index)
        player = quiz.players[outcome.player_index]
        new_solved_count = len(solved) + 1
        completed = new_solved_count >= quiz.total_players
        return jsonify(
            {
                "status": "close",
                "message": f"So close! We'll count that - the answer was {player.name}.",
                "player": _player_public_dict(player, outcome.player_index),
                "solved_count": new_solved_count,
                "total": quiz.total_players,
                "completed": completed,
            }
        )

    return jsonify(
        {
            "status": "wrong",
            "message": "Not a match - keep trying!",
            "solved_count": len(solved),
            "total": quiz.total_players,
            "completed": False,
        }
    )


@bp.route("/quiz/<quiz_id>/clue", methods=["POST"])
def request_clue(quiz_id: str):
    quiz = _quiz_or_404(quiz_id)
    if quiz is None:
        return jsonify({"status": "error", "message": "Unknown quiz."}), 404
    if not _is_quiz_unlocked(quiz):
        return jsonify({"status": "locked", "message": "This quiz is not unlocked yet."}), 403

    data = request.get_json(silent=True) or {}
    requested_types = [
        t for t in data.get("types", []) if t in ("apps", "years", "goals", "position", "initials")
    ]
    if not requested_types:
        return jsonify({"status": "error", "message": "Choose at least one clue type."}), 400

    state = progress_store.get_quiz_progress(quiz_id)
    solved = set(state["solved"])

    clues = []
    for index, player in enumerate(quiz.players):
        if index in solved or state["given_up"]:
            continue
        entry = {"index": index}
        for clue_type in requested_types:
            entry[clue_type] = player.clue_value(clue_type)
        clues.append(entry)

    return jsonify({"status": "ok", "clue_types": requested_types, "clues": clues})


@bp.route("/quiz/<quiz_id>/giveup", methods=["POST"])
def give_up(quiz_id: str):
    quiz = _quiz_or_404(quiz_id)
    if quiz is None:
        return jsonify({"status": "error", "message": "Unknown quiz."}), 404
    if not _is_quiz_unlocked(quiz):
        return jsonify({"status": "locked", "message": "This quiz is not unlocked yet."}), 403

    data = request.get_json(silent=True) or {}
    if not data.get("confirm"):
        return jsonify({"status": "error", "message": "Confirmation required."}), 400

    progress_store.mark_given_up(quiz_id)
    players = [_player_public_dict(player, index) for index, player in enumerate(quiz.players)]

    return jsonify(
        {
            "status": "given_up",
            "message": "Here are all the answers.",
            "players": players,
            "total": quiz.total_players,
        }
    )


@bp.route("/quiz/<quiz_id>/reset", methods=["POST"])
def reset_quiz(quiz_id: str):
    quiz = _quiz_or_404(quiz_id)
    if quiz is None:
        return jsonify({"status": "error", "message": "Unknown quiz."}), 404

    data = request.get_json(silent=True) or {}
    if not data.get("confirm"):
        return jsonify({"status": "error", "message": "Confirmation required."}), 400

    progress_store.reset_quiz_progress(quiz_id)
    return jsonify({"status": "reset", "message": "Progress reset."})
