"""Mechanics of the intensive-margin hours response, on a stub simulation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from free_childcare_reform import sources
from free_childcare_reform.hours_response import hours_response, out_of_pocket_childcare


class _Stub:
    """Two households: a couple with a child who pay for childcare, and a single worker.

    Person 0 works 30 hours a week for £35,000 and is the adult the response
    can move; person 1 is their non-working partner; person 2 is the child;
    person 3 is a childless worker in the second household. Only person 0 has
    a positive out-of-pocket childcare cost, so only person 0 responds.
    """

    def __init__(self, support, uc_element=0.0, net_income=(40_000.0, 20_000.0)):
        p = lambda values: pd.Series(values)  # noqa: E731
        self._values = {
            ("employment_income", None): p([35_000.0, 0.0, 0.0, 25_000.0]),
            ("hours_worked", None): p([30.0 * 52, 0.0, 0.0, 40.0 * 52]),
            ("household_weight", "person"): p([10.0, 10.0, 10.0, 5.0]),
            ("household_weight", None): p([10.0, 5.0]),
            ("country", "person"): p(["ENGLAND", "ENGLAND", "ENGLAND", "WALES"]),
            ("employment_status", None): p(["FT_EMPLOYED", "UNEMPLOYED", "CHILD", "FT_EMPLOYED"]),
            ("age", None): p([35.0, 34.0, 2.0, 40.0]),
            ("adult_index", None): p([1.0, 2.0, 0.0, 1.0]),
            ("youngest_child_age", "person"): p([2.0, 2.0, 2.0, np.nan]),
            ("tax_free_childcare", "benunit"): p([support, 0.0]),
            ("uc_childcare_element", "benunit"): p([uc_element, 0.0]),
            ("benunit_id", None): p([1, 2]),
            ("benunit_id", "person"): p([1, 1, 1, 2]),
            ("household_id", None): p([100, 200]),
            ("household_id", "person"): p([100, 100, 100, 200]),
            ("household_net_income", None): p(list(net_income)),
        }

    def calculate(self, variable, year, map_to=None):
        return self._values[(variable, map_to)]


CHILDCARE = np.array([8_000.0, 8_000.0, 8_000.0, 0.0])


def test_out_of_pocket_nets_off_both_cost_contingent_supports():
    sim = _Stub(support=1_600.0, uc_element=400.0)
    assert out_of_pocket_childcare(sim, 2027, CHILDCARE).tolist() == [
        6_000.0,
        6_000.0,
        6_000.0,
        0.0,
    ]


def test_the_response_follows_the_price_change_and_the_rerun_sets_the_revenue():
    baseline = _Stub(support=1_600.0)  # pays 6,400 out of pocket
    reform = _Stub(support=6_000.0)  # pays 2,000: a 68.75% price fall
    price_change = (2_000.0 - 6_400.0) / 6_400.0
    hours_change = sources.HOURS_PRICE_ELASTICITY * price_change
    extra_earnings = 35_000.0 * hours_change
    reruns = []

    def rerun(employment_income):
        reruns.append(np.asarray(employment_income))
        # The household keeps 60% of the extra earnings.
        gain = (employment_income[0] - 35_000.0) * 0.6
        return _Stub(support=6_000.0, net_income=(40_000.0 + gain, 20_000.0))

    result = hours_response(baseline, reform, 2027, CHILDCARE, CHILDCARE, rerun)

    assert reruns[0].tolist() == pytest.approx([35_000.0 + extra_earnings, 0.0, 0.0, 25_000.0])
    assert result["workers_in_scope"] == 10
    assert result["workers_with_price_change"] == 10
    assert result["mean_price_change_pct"] == pytest.approx(price_change * 100, abs=0.01)
    assert result["extra_weekly_hours"] == pytest.approx(30.0 * hours_change * 10, abs=0.1)
    assert result["ftes"] == pytest.approx(30.0 * hours_change * 10 / 37.5, abs=0.1)
    assert result["earnings_gbp"] == pytest.approx(extra_earnings * 10, abs=0.01)
    assert result["net_revenue_gbp"] == pytest.approx(extra_earnings * 10 * 0.4, abs=0.01)
    # The household's gain lands on the adult whose hours produced it.
    allocated = result["expected_net_income_change_per_person"]
    assert allocated.tolist() == pytest.approx([extra_earnings * 0.6, 0.0, 0.0, 0.0])
    # The country split reconciles to the total.
    assert result["by_country"]["england"]["net_revenue_gbp"] == pytest.approx(
        result["net_revenue_gbp"], abs=0.01
    )
    assert result["by_country"]["wales"]["earnings_gbp"] == 0.0


def test_the_elasticity_scale_moves_hours_proportionally():
    baseline = _Stub(support=1_600.0)
    reform = _Stub(support=6_000.0)
    rerun = lambda e: _Stub(support=6_000.0)  # noqa: E731
    central = hours_response(baseline, reform, 2027, CHILDCARE, CHILDCARE, rerun)
    doubled = hours_response(
        baseline, reform, 2027, CHILDCARE, CHILDCARE, rerun, elasticity_scale=2.0
    )
    assert doubled["earnings_gbp"] == pytest.approx(2 * central["earnings_gbp"], abs=0.01)
    assert doubled["elasticity"] == pytest.approx(2 * sources.HOURS_PRICE_ELASTICITY)


def test_no_price_change_means_no_response():
    sim = _Stub(support=1_600.0)
    result = hours_response(sim, sim, 2027, CHILDCARE, CHILDCARE, lambda e: sim)
    assert result["workers_in_scope"] == 10
    assert result["workers_with_price_change"] == 0
    assert result["earnings_gbp"] == 0.0
    assert result["net_revenue_gbp"] == 0.0


def test_the_price_fall_is_bounded_at_the_whole_cost():
    """A subsidy larger than the cost cannot make the price more than 100% cheaper."""
    baseline = _Stub(support=1_600.0)
    reform = _Stub(support=20_000.0)
    result = hours_response(baseline, reform, 2027, CHILDCARE, CHILDCARE, lambda e: reform)
    assert result["mean_price_change_pct"] == -100.0
