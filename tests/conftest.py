import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.data_loader import QUIZ_TIMEZONE, load_quizzes

DATA_PATH = Path(__file__).resolve().parent.parent / "data_source.xlsx"


@pytest.fixture(scope="session")
def quizzes():
    return load_quizzes(DATA_PATH)


@pytest.fixture()
def app():
    flask_app = create_app(DATA_PATH)
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def unlocked_quiz(app):
    """Force the first quiz to already be unlocked, for gameplay tests."""
    quiz = app.config["QUIZZES"][0]
    quiz.unlock_at = datetime.now(QUIZ_TIMEZONE) - timedelta(days=1)
    return quiz
