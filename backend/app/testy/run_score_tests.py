"""Backward-compatible entry point for the score-test runner."""

import sys
from pathlib import Path


BACKEND_FOLDER = Path(__file__).resolve().parents[2]
if str(BACKEND_FOLDER) not in sys.path:
    sys.path.insert(0, str(BACKEND_FOLDER))

from app.testy.score_tests.run_score.run_score_tests import main


if __name__ == "__main__":
    main()
