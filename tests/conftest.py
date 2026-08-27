import json
from pathlib import Path

import pytest

RESULTS = Path(__file__).resolve().parents[1] / "data" / "free_childcare_reform_results.json"


@pytest.fixture(scope="session")
def results():
    if not RESULTS.exists():
        pytest.skip("run `python -m free_childcare_reform` first")
    return json.loads(RESULTS.read_text())
