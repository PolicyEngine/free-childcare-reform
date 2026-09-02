"""Mechanics of the intensive-margin hours response, on a stub simulation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from free_childcare_reform import sources
from free_childcare_reform.hours_response import (
    hours_response,
    out_of_pocket_childcare,
    realised_uc_childcare_support,
)


class _Stub:
    """Two households: a couple with a child who pay for childcare, and a single worker.

    Person 0 works 30 hours a week for £35,000 and is the adult the response
    can move; person 1 is their non-working partner; person 2 is the child;
    person 3 is a childless worker in the second household. Only person 0 has
    a positive out-of-pocket childcare cost, so only person 0 responds.
    """

    def __init__(self, support, universal_credit=(0.0, 0.0), net_income=(40_000.0, 20_000.0)):
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
            ("universal_credit", None): p(list(universal_credit)),
            ("benunit_id", None): p([1, 2]),
            ("benunit_id", "person"): p([1, 1, 1, 2]),
            ("household_id", None): p([100, 200]),
            ("household_id", "person"): p([100, 100, 100, 200]),
            ("household_net_income", None): p(list(net_income)),
        }

    def calculate(self, variable, year, map_to=None):
        return self._values[(variable, map_to)]


CHILDCARE = np.array([8_000.0, 8_000.0, 8_000.0, 0.0])
NO_UC = np.zeros(2)


def test_out_of_pocket_nets_off_both_cost_contingent_supports():
    sim = _Stub(support=1_600.0)
    assert out_of_pocket_childcare(sim, 2027, CHILDCARE, np.array([400.0, 0.0])).tolist() == [
        6_000.0,
        6_000.0,
        6_000.0,
        0.0,
    ]


def test_realised_uc_support_is_the_award_difference_not_the_element():
    """A tapered working family keeps only part of the element's face value.

    The element is £6,800 (85% of £8,000) in the UC maximum amount, but the
    taper withdraws most of it: the award is £1,200 with the element and £0
    without. The realised support is £1,200, and the family's out-of-pocket
    cost is £8,000 - £1,600 - £1,200 = £5,200, not the £0 that subtracting
    the element would give.
    """
    with_element = _Stub(support=1_600.0, universal_credit=(1_200.0, 0.0))
    without = _Stub(support=1_600.0, universal_credit=(0.0, 0.0))
    realised = realised_uc_childcare_support(with_element, without, 2027)
    assert realised.tolist() == [1_200.0, 0.0]
    price = out_of_pocket_childcare(with_element, 2027, CHILDCARE, realised)
    assert price.tolist() == [5_200.0, 5_200.0, 5_200.0, 0.0]


def test_a_tapered_uc_family_responds_to_its_realised_price():
    """The price change is measured on what the family pays, not on the element."""
    # Baseline: TFC 1,600 and 1,200 of realised UC support on 8,000 of costs.
    baseline = _Stub(support=1_600.0, universal_credit=(1_200.0, 0.0))
    # Reform: the subsidy pays 6,000; the taper now withdraws the element
    # entirely (the family's UC no longer moves with childcare), so realised
    # UC support is zero. Out of pocket falls from 5,200 to 2,000.
    reform = _Stub(support=6_000.0, universal_credit=(0.0, 0.0))
    result = hours_response(
        baseline,
        reform,
        2027,
        CHILDCARE,
        CHILDCARE,
        lambda e: reform,
        baseline_uc_support=np.array([1_200.0, 0.0]),
        reform_uc_support=NO_UC,
    )
    assert result["mean_price_change_pct"] == pytest.approx(
        (2_000.0 - 5_200.0) / 5_200.0 * 100, abs=0.01
    )


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

    result = hours_response(baseline, reform, 2027, CHILDCARE, CHILDCARE, rerun, NO_UC, NO_UC)

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
    central = hours_response(baseline, reform, 2027, CHILDCARE, CHILDCARE, rerun, NO_UC, NO_UC)
    doubled = hours_response(
        baseline, reform, 2027, CHILDCARE, CHILDCARE, rerun, NO_UC, NO_UC, elasticity_scale=2.0
    )
    assert doubled["earnings_gbp"] == pytest.approx(2 * central["earnings_gbp"], abs=0.01)
    assert doubled["elasticity"] == pytest.approx(2 * sources.HOURS_PRICE_ELASTICITY)


def test_no_price_change_means_no_response():
    sim = _Stub(support=1_600.0)
    result = hours_response(sim, sim, 2027, CHILDCARE, CHILDCARE, lambda e: sim, NO_UC, NO_UC)
    assert result["workers_in_scope"] == 10
    assert result["workers_with_price_change"] == 0
    assert result["earnings_gbp"] == 0.0
    assert result["net_revenue_gbp"] == 0.0


def test_the_price_fall_is_bounded_at_the_whole_cost():
    """A subsidy larger than the cost cannot make the price more than 100% cheaper."""
    baseline = _Stub(support=1_600.0)
    reform = _Stub(support=20_000.0)
    result = hours_response(
        baseline, reform, 2027, CHILDCARE, CHILDCARE, lambda e: reform, NO_UC, NO_UC
    )
    assert result["mean_price_change_pct"] == -100.0


def test_a_two_earner_household_splits_the_gain_by_earnings_and_reconciles():
    """Both adults respond; the household gain is allocated in proportion to their extra earnings."""
    baseline = _Stub(support=1_600.0)
    reform = _Stub(support=6_000.0)
    # Person 1 also works: 20 hours a week for £15,000.
    for sim in (baseline, reform):
        sim._values[("employment_income", None)] = pd.Series([35_000.0, 15_000.0, 0.0, 25_000.0])
        sim._values[("hours_worked", None)] = pd.Series([30.0 * 52, 20.0 * 52, 0.0, 40.0 * 52])
        sim._values[("employment_status", None)] = pd.Series(
            ["FT_EMPLOYED", "PT_EMPLOYED", "CHILD", "FT_EMPLOYED"]
        )
    hours_change = sources.HOURS_PRICE_ELASTICITY * (2_000.0 - 6_400.0) / 6_400.0
    extra = np.array([35_000.0, 15_000.0]) * hours_change

    def rerun(employment_income):
        gain = (employment_income[0] + employment_income[1] - 50_000.0) * 0.6
        out = _Stub(support=6_000.0, net_income=(40_000.0 + gain, 20_000.0))
        out._values[("employment_income", None)] = pd.Series(employment_income)
        return out

    result = hours_response(baseline, reform, 2027, CHILDCARE, CHILDCARE, rerun, NO_UC, NO_UC)
    allocated = result["expected_net_income_change_per_person"]
    assert allocated[:2].tolist() == pytest.approx((extra * 0.6).tolist())
    assert allocated[0] / allocated[1] == pytest.approx(35_000.0 / 15_000.0)
    assert result["earnings_gbp"] == pytest.approx(extra.sum() * 10, abs=0.01)
    assert result["net_revenue_gbp"] == pytest.approx(extra.sum() * 10 * 0.4, abs=0.01)
    assert result["by_country"]["england"]["net_revenue_gbp"] == pytest.approx(
        result["net_revenue_gbp"], abs=0.01
    )
