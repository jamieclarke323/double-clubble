from datetime import datetime, timedelta

from app.data_loader import QUIZ_TIMEZONE, Player, Quiz


def test_home_page_lists_fixtures(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"West Ham" in resp.data
    assert b"Fixtures" in resp.data or b"fixtures" in resp.data
    assert b"West Ham United vs Charlton Athletic" in resp.data


def test_future_quiz_shows_unlock_message(client, app):
    app.config["BYPASS_UNLOCK"] = False
    quiz = app.config["QUIZZES"][0]
    resp = client.get(f"/quiz/{quiz.quiz_id}")
    assert resp.status_code == 200
    assert b"Unlocks" in resp.data
    assert b"7:00" in resp.data or b"7:0" in resp.data


def test_unknown_quiz_returns_404(client):
    resp = client.get("/quiz/not-a-real-quiz")
    assert resp.status_code == 404


def test_guess_endpoint_locked_before_unlock(client, app):
    app.config["BYPASS_UNLOCK"] = False
    quiz = app.config["QUIZZES"][0]
    resp = client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Anything"})
    assert resp.status_code == 403
    assert resp.get_json()["status"] == "locked"


def _tiny_quiz_app(app):
    """Swap in a tiny 2-player quiz so full-completion tests are fast."""
    players = [
        Player(
            name="Darren Bent",
            position="ST",
            years_charlton="2005-2006",
            apps_charlton=68,
            goals_charlton=31,
            years_opponent="2014-2017",
            apps_opponent=84,
            goals_opponent=28,
        ),
        Player(
            name="Chris Powell",
            position="LB",
            years_charlton="1998-2007",
            apps_charlton=244,
            goals_charlton=2,
            years_opponent="2006",
            apps_opponent=15,
            goals_opponent=0,
        ),
    ]
    quiz = Quiz(
        quiz_id="tiny-quiz",
        opponent="Tiny FC",
        fixture_date=(datetime.now(QUIZ_TIMEZONE) - timedelta(days=1)).date(),
        players=players,
    )
    quiz.unlock_at = datetime.now(QUIZ_TIMEZONE) - timedelta(days=1)
    app.config["QUIZZES"] = [quiz]
    app.config["QUIZZES_BY_ID"] = {"tiny-quiz": quiz}
    return quiz


def test_correct_guess_marks_player_found(client, app):
    quiz = _tiny_quiz_app(app)
    resp = client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Bent"})
    data = resp.get_json()
    assert data["status"] == "correct"
    assert data["solved_count"] == 1
    assert data["completed"] is False


def test_close_misspelling_gives_close_feedback(client, app):
    quiz = _tiny_quiz_app(app)
    resp = client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Powal"})
    data = resp.get_json()
    assert data["status"] == "close"
    assert data["player"]["name"] == "Chris Powell"
    assert data["solved_count"] == 1


def test_completing_all_players_sets_completed_true(client, app):
    quiz = _tiny_quiz_app(app)
    client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Bent"})
    resp = client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Powell"})
    data = resp.get_json()
    assert data["status"] == "correct"
    assert data["completed"] is True


def test_clue_endpoint_only_returns_unsolved_players(client, app):
    quiz = _tiny_quiz_app(app)
    client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Bent"})
    resp = client.post(f"/quiz/{quiz.quiz_id}/clue", json={"types": ["apps", "position"]})
    data = resp.get_json()
    assert data["status"] == "ok"
    assert len(data["clues"]) == 1
    assert "apps" in data["clues"][0]
    assert "position" in data["clues"][0]
    assert "years" not in data["clues"][0]


def test_clue_endpoint_supports_initials(client, app):
    quiz = _tiny_quiz_app(app)
    resp = client.post(f"/quiz/{quiz.quiz_id}/clue", json={"types": ["initials"]})
    data = resp.get_json()
    assert data["status"] == "ok"
    initials = {entry["initials"] for entry in data["clues"]}
    assert initials == {"D.B.", "C.P."}


def test_giveup_requires_confirmation(client, app):
    quiz = _tiny_quiz_app(app)
    resp = client.post(f"/quiz/{quiz.quiz_id}/giveup", json={"confirm": False})
    assert resp.status_code == 400


def test_giveup_reveals_all_answers(client, app):
    quiz = _tiny_quiz_app(app)
    resp = client.post(f"/quiz/{quiz.quiz_id}/giveup", json={"confirm": True})
    data = resp.get_json()
    assert data["status"] == "given_up"
    assert len(data["players"]) == 2
    names = {p["name"] for p in data["players"]}
    assert names == {"Darren Bent", "Chris Powell"}


def test_reset_requires_confirmation(client, app):
    quiz = _tiny_quiz_app(app)
    resp = client.post(f"/quiz/{quiz.quiz_id}/reset", json={"confirm": False})
    assert resp.status_code == 400


def test_reset_clears_solved_progress(client, app):
    quiz = _tiny_quiz_app(app)
    client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Bent"})

    resp = client.post(f"/quiz/{quiz.quiz_id}/reset", json={"confirm": True})
    assert resp.get_json()["status"] == "reset"

    page = client.get(f"/quiz/{quiz.quiz_id}")
    assert b"Darren Bent" not in page.data
    assert b"0</span> / <span" in page.data


def test_progress_persists_across_requests_via_session_cookie(client, app):
    quiz = _tiny_quiz_app(app)
    client.post(f"/quiz/{quiz.quiz_id}/guess", json={"guess": "Bent"})

    page = client.get(f"/quiz/{quiz.quiz_id}")
    assert b"Darren Bent" in page.data


def test_session_lifetime_is_48_hours(app):
    assert app.config["PERMANENT_SESSION_LIFETIME"].total_seconds() == 48 * 3600
