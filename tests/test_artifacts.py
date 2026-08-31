"""Checks on the result artifacts themselves.

The audit (issue #2, finding 8) showed the workflow stayed green through
missing, empty and divergent result files: the analysis tests skip when the
root JSON is absent, and the dashboard loads a different copy under
`public/`. These fail instead.
"""

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_RESULTS = REPO_ROOT / "data" / "free_childcare_reform_results.json"
PUBLIC_RESULTS = (
    REPO_ROOT / "dashboard" / "public" / "data" / "free_childcare_reform_results.json"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_both_result_files_exist():
    """Never skipped. A missing artifact is a failure, not an absence."""
    for path in (ROOT_RESULTS, PUBLIC_RESULTS):
        assert path.exists(), f"{path.relative_to(REPO_ROOT)} is missing"
        assert path.stat().st_size > 1_000, f"{path.relative_to(REPO_ROOT)} is empty"


def test_the_dashboard_reads_the_same_results_the_analysis_wrote():
    """The dashboard loads its own copy, so the two can silently diverge."""
    assert _digest(ROOT_RESULTS) == _digest(PUBLIC_RESULTS), (
        "data/ and dashboard/public/data/ differ — rerun the pipeline, which "
        "writes both"
    )


@pytest.fixture(scope="module")
def results():
    return json.loads(ROOT_RESULTS.read_text())


def test_the_results_carry_the_shape_the_dashboard_expects(results):
    """A schema check, so a renamed key fails here rather than in a browser."""
    for key in ("years", "by_year", "assumptions", "sources", "comparable_costings"):
        assert key in results, key
    for year in results["years"]:
        block = results["by_year"][str(year)]
        for key in (
            "legs",
            "labour_supply",
            "dynamic_cost",
            "baseline_programmes",
            "benchmarks",
            "fee_base_sensitivity",
            "subsidy_take_up",
        ):
            assert key in block, (year, key)
        for leg in ("free_hours", "subsidy", "combined"):
            leg_block = block["legs"][leg]
            for key in (
                "static_cost_bn",
                "household_effects",
                "household_effects_by_bound",
                "dynamic_cost",
                "labour_supply",
            ):
                assert key in leg_block, (year, leg, key)
            for bound in ("low", "central", "high"):
                assert bound in leg_block["household_effects_by_bound"], (leg, bound)


def test_the_results_record_what_produced_them(results):
    """So a figure can be traced to a commit, not just to a package version."""
    provenance = results["provenance"]
    assert provenance["analysis_commit"], "no analysis commit recorded"
    assert provenance["python_version"]
    assert provenance["generated_at"]
    assert results["dataset_revision"]
    assert results["policyengine_version"]
