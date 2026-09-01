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
    import subprocess

    from free_childcare_reform.pipeline import _source_digest

    provenance = json.loads(ROOT_RESULTS.read_text())["provenance"]
    assert provenance["source_digest"] == _source_digest(), (
        "the committed results were generated from different source than is "
        "checked in — rerun the pipeline"
    )

    # The digest alone allows a run whose commit is stale: it pins the source
    # files but not which commit they belonged to. In CI, where the tree is a
    # clean checkout, the recorded commit must be the one being tested.
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    if dirty:
        pytest.skip("working tree is dirty; commit-equality is checked in CI")
    assert provenance["analysis_commit"] == head, (
        f"results were generated at {provenance['analysis_commit'][:8]} but HEAD "
        f"is {head[:8]} — rerun the pipeline and commit the artifacts together"
    )


def test_every_output_can_be_read_for_england_alone(results):
    """The area control governs the whole view, so every block must split.

    Free hours is England-only in law and in the model, so its non-England
    figures must be exactly zero — not missing, which would be
    indistinguishable from a leg that was never split.
    """
    for year in results["years"]:
        block = results["by_year"][str(year)]
        for leg in ("free_hours", "subsidy", "combined"):
            leg_block = block["legs"][leg]
            by_country = leg_block["static_cost_by_country_bn"]
            for area in ("uk", "england", "scotland", "wales", "northern_ireland"):
                assert area in by_country, (year, leg, area)
            assert "household_effects_england" in leg_block, (year, leg)
            assert "household_effects_by_bound_england" in leg_block, (year, leg)

        free_hours = block["legs"]["free_hours"]["static_cost_by_country_bn"]
        for devolved in ("scotland", "wales", "northern_ireland"):
            assert free_hours[devolved] == 0, (
                f"{year}: free hours is England-only, so {devolved} must be zero"
            )
        assert free_hours["england"] == pytest.approx(free_hours["uk"])

        for bound in ("low", "central", "high"):
            by_country = block["labour_supply"][bound]["by_country"]
            assert "england" in by_country, (year, bound)


COUNTRIES = ("england", "scotland", "wales", "northern_ireland")


def _number(value, path):
    """A finite number, and not a bool — `isinstance(True, int)` is True."""
    assert not isinstance(value, bool), f"{path} is a boolean, not a number"
    assert isinstance(value, (int, float)), f"{path} is {type(value).__name__}"
    assert math.isfinite(value), f"{path} is {value}"


def test_country_costs_reconcile_to_the_headline(results):
    """The parts must sum to the whole, on the same quantity.

    An earlier version summed four childcare programme variables while the
    headline used `gov_spending`, differing by £28.7m of Universal Credit
    interaction — two figures for one cost, differing by more than rounding.
    """
    for year in results["years"]:
        for leg in ("free_hours", "subsidy", "combined"):
            block = results["by_year"][str(year)]["legs"][leg]
            by_country = block["static_cost_by_country_bn"]
            for area in COUNTRIES + ("uk",):
                _number(by_country[area], f"{year}/{leg}/{area}")
            parts = sum(by_country[country] for country in COUNTRIES)
            assert by_country["uk"] == pytest.approx(parts, abs=0.001), (year, leg)
            assert by_country["uk"] == pytest.approx(block["static_cost_bn"], abs=0.002), (
                f"{year}/{leg}: country total must reconcile to the headline"
            )


def test_the_free_hours_leg_is_england_only_in_every_country_block(results):
    for year in results["years"]:
        by_country = results["by_year"][str(year)]["legs"]["free_hours"][
            "static_cost_by_country_bn"
        ]
        for devolved in ("scotland", "wales", "northern_ireland"):
            assert by_country[devolved] == 0, (year, devolved)


def test_geography_and_distribution_blocks_are_fully_typed(results):
    """Rejects null, boolean and wrong-shaped objects.

    A mutation setting `subsidy_by_country` to null, an England cost to
    `true` and a country response to null passed every earlier artifact test
    while crashing a client on its first property access.
    """
    for year in results["years"]:
        block = results["by_year"][str(year)]

        by_country = block["subsidy_by_country"]
        assert isinstance(by_country, dict), year
        for area in COUNTRIES + ("uk",):
            _number(by_country[area], f"{year}/subsidy_by_country/{area}")

        for bound in ("low", "central", "high"):
            responses = block["labour_supply"][bound]["by_country"]
            assert isinstance(responses, dict), (year, bound)
            for area in COUNTRIES:
                response = responses[area]
                assert isinstance(response, dict), (year, bound, area)
                for field in ("entrants", "leavers", "net_entrants", "net_revenue_gbp"):
                    _number(response[field], f"{year}/{bound}/{area}/{field}")

        for leg in ("free_hours", "subsidy", "combined"):
            leg_block = block["legs"][leg]
            for key in ("household_effects_england", "household_effects"):
                effects = leg_block[key]
                assert isinstance(effects, dict), (year, leg, key)
                for breakdown in (
                    "by_income_quintile",
                    "by_income_quintile_families_with_under_5s",
                ):
                    rows = effects[breakdown]
                    assert isinstance(rows, list) and rows, (year, leg, key, breakdown)
                    for row in rows:
                        assert isinstance(row["group"], str)
                        _number(row["average_gain_gbp"], f"{year}/{leg}/{key}/{breakdown}")
            for bound in ("low", "central", "high"):
                assert isinstance(leg_block["household_effects_by_bound_england"][bound], dict), (
                    year,
                    leg,
                    bound,
                )


def test_the_scope_scenarios_are_ordered_and_distinct(results):
    """Take-up and Universal Credit inclusion are separate dimensions."""
    for year in results["years"]:
        scenarios = results["by_year"][str(year)]["scope_scenarios"]
        for key in (
            "as_coded_bn",
            "full_take_up_bn",
            "uc_families_included_bn",
            "uc_families_and_full_take_up_bn",
        ):
            _number(scenarios[key], f"{year}/scope_scenarios/{key}")
        assert (
            scenarios["as_coded_bn"]
            < scenarios["full_take_up_bn"]
            < scenarios["uc_families_and_full_take_up_bn"]
        ), year
        assert scenarios["as_coded_bn"] < scenarios["uc_families_included_bn"], year
