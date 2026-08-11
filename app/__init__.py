from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from flask import Flask

from .data_loader import load_quizzes

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_XLSX_PATH = BASE_DIR / "data_source.xlsx"


def create_app(xlsx_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    # Per-device progress (no login) is kept in the signed session cookie for
    # 48 hours since the visitor's last request, then forgotten.
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=48)
    # Enable once served over HTTPS (e.g. PythonAnywhere) so the cookie is never sent in the clear.
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    # Temporary QA switch: when true, all quizzes behave as unlocked.
    app.config["BYPASS_UNLOCK"] = os.environ.get("BYPASS_UNLOCK", "0") == "1"
    # Shown on shareable result images - update once the site has a real URL.
    app.config["SITE_NAME"] = "Double Clubble"
    app.config["SITE_URL"] = os.environ.get("SITE_URL", "double-clubble.example.com")

    xlsx_path = Path(xlsx_path or os.environ.get("QUIZ_XLSX_PATH", DEFAULT_XLSX_PATH))
    quizzes = load_quizzes(xlsx_path)
    app.config["QUIZZES"] = quizzes
    app.config["QUIZZES_BY_ID"] = {quiz.quiz_id: quiz for quiz in quizzes}

    from . import routes

    app.register_blueprint(routes.bp)

    return app
