from datetime import date, datetime, timedelta

from app.data_loader import QUIZ_TIMEZONE, Player, Quiz


def make_player(name="Test Player"):
    return Player(
        name=name,
        position="ST",
        years_charlton="2020",
        apps_charlton=10,
        goals_charlton=2,
        years_opponent="2018",
        apps_opponent=20,
        goals_opponent=5,
    )


def make_quiz(fixture_date):
    return Quiz(
        quiz_id="test-quiz",
        opponent="Test FC",
        fixture_date=fixture_date,
        players=[make_player()],
    )


def test_quiz_unlocks_exactly_at_7am_on_fixture_date():
    quiz = make_quiz(date(2026, 8, 22))
    just_before = datetime(2026, 8, 22, 6, 59, tzinfo=QUIZ_TIMEZONE)
    exactly_7am = datetime(2026, 8, 22, 7, 0, tzinfo=QUIZ_TIMEZONE)
    just_after = datetime(2026, 8, 22, 7, 1, tzinfo=QUIZ_TIMEZONE)

    assert quiz.is_unlocked(just_before) is False
    assert quiz.is_unlocked(exactly_7am) is True
    assert quiz.is_unlocked(just_after) is True


def test_quiz_stays_unlocked_after_match_day():
    quiz = make_quiz(date(2026, 8, 22))
    long_after = datetime(2027, 1, 1, tzinfo=QUIZ_TIMEZONE)
    assert quiz.is_unlocked(long_after) is True


def test_quiz_locked_days_before():
    quiz = make_quiz(date(2026, 8, 22))
    days_before = datetime(2026, 8, 20, tzinfo=QUIZ_TIMEZONE)
    assert quiz.is_unlocked(days_before) is False


def test_all_24_fixtures_loaded_and_sorted(quizzes):
    assert len(quizzes) == 24
    for earlier, later in zip(quizzes, quizzes[1:]):
        assert earlier.fixture_date <= later.fixture_date


def test_first_fixture_is_west_ham_on_22_aug_2026(quizzes):
    west_ham = next(q for q in quizzes if q.opponent == "West Ham United")
    assert west_ham.fixture_date == date(2026, 8, 22)
    assert west_ham.unlock_at.hour == 7


def test_every_quiz_has_players(quizzes):
    for quiz in quizzes:
        assert quiz.total_players > 0
