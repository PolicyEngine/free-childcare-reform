"""Checks on the result artifacts themselves.

The audit (issue #2, finding 8) showed the workflow stayed green through
missing, empty and divergent result files: the analysis tests skip when the
root JSON is absent, and the dashboard loads a different copy under
`public/`. These fail instead.
"""

import hashlib
import json
import math
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_RESULTS = REPO_ROOT / "data" / "free_childcare_reform_results.json"
PUBLIC_RESULTS = REPO_ROOT / "dashboard" / "public" / "data" / "free_childcare_reform_results.json"


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
        "data/ and dashboard/public/data/ differ — rerun the pipeline, which writes both"
    )


@pytest.fixture(scope="module")
def results():
    return json.loads(ROOT_RESULTS.read_text())


def _walk_numbers(node, path=""):
    """Every scalar in the payload, with the path that reaches it."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk_numbers(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_numbers(value, f"{path}[{index}]")
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        yield path, node


def test_every_number_is_finite(results):
    """NaN and Infinity are valid Python and invalid JSON.

    `json.dumps` emits them bare and `json.load` reads them back, so a
    Python-only check passes a file every browser's JSON.parse rejects. The
    pipeline now serialises with allow_nan=False; this is the second lock.
    """
    for path, value in _walk_numbers(results):
        assert math.isfinite(value), f"{path} is {value}"


def test_the_raw_bytes_contain_no_javascript_invalid_tokens():
    """What a browser sees, not what Python can be talked into reading."""
    text = ROOT_RESULTS.read_text()
    for token in ("NaN", "Infinity", "-Infinity"):
        assert f": {token}" not in text, f"{token} would break JSON.parse"


def test_the_results_carry_the_shape_the_dashboard_expects(results):
    """A typed schema, not a key-presence check.

    Replacing a nested object with a string previously passed every artifact
    test while crashing the dashboard on its first property access, so the
    types are asserted as well as the keys.
    """
    assert isinstance(results["years"], list) and results["years"]
    for key in ("assumptions", "sources", "comparable_costings", "by_year"):
        assert key in results, key
    assert isinstance(results["comparable_costings"], list)

    for year in results["years"]:
        block = results["by_year"][str(year)]
        assert isinstance(block, dict), year
        for key, kind in (
            ("legs", dict),
            ("labour_supply", dict),
            ("dynamic_cost", dict),
            ("baseline_programmes", list),
            ("benchmarks", list),
            ("fee_base_sensitivity", dict),
            ("subsidy_take_up", dict),
        ):
            assert isinstance(block.get(key), kind), (year, key)

        for bound in ("low", "central", "high"):
            dynamic = block["dynamic_cost"][bound]
            assert isinstance(dynamic, dict), (year, bound)
            for field in (
                "static_cost_bn",
                "labour_supply_offset_bn",
                "dynamic_cost_bn",
                "net_entrants",
                "net_ftes",
            ):
                assert isinstance(dynamic[field], (int, float)), (year, bound, field)

        for leg in ("free_hours", "subsidy", "combined"):
            leg_block = block["legs"][leg]
            assert isinstance(leg_block, dict), (year, leg)
            assert isinstance(leg_block["static_cost_bn"], (int, float)), (year, leg)
            for key in ("household_effects", "household_effects_by_bound", "labour_supply"):
                assert isinstance(leg_block[key], dict), (year, leg, key)
            for bound in ("low", "central", "high"):
                effects = leg_block["household_effects_by_bound"][bound]
                assert isinstance(effects, dict), (leg, bound)
                for breakdown in (
                    "by_income_quintile",
                    "by_income_quintile_families_with_under_5s",
                    "by_family_type",
                    "by_family_type_families_with_under_5s",
                ):
                    rows = effects[breakdown]
                    assert isinstance(rows, list) and rows, (leg, bound, breakdown)
                    for row in rows:
                        assert isinstance(row["group"], str)
                        assert isinstance(row["average_gain_gbp"], (int, float))


def test_the_results_record_what_produced_them(results):
    """So a figure traces to a source state, not just to a package version."""
    provenance = results["provenance"]
    assert provenance["analysis_commit"], "no analysis commit recorded"
    assert provenance["source_digest"], "no source digest recorded"
    assert provenance["python_version"]
    assert provenance["generated_at"]
    assert results["dataset_revision"]
    assert results["policyengine_version"]


def test_the_committed_results_were_generated_from_the_committed_source():
    """A dirty run identifies nothing on its own.

    `analysis_commit` plus `working_tree_dirty: true` says "this commit plus
    unknown uncommitted bytes". The digest pins what actually ran, so it must
    match the source in the tree now.
    """
    from free_childcare_reform.pipeline import _source_digest

    recorded = json.loads(ROOT_RESULTS.read_text())["provenance"]["source_digest"]
    assert recorded == _source_digest(), (
        "the committed results were generated from different source than is "
        "checked in — rerun the pipeline"
    )
