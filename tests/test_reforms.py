"""Unit tests for the reform arithmetic that does not need a simulation."""

import numpy as np
import pytest

from free_childcare_reform import sources
from free_childcare_reform.reforms import displaced_childcare_expenses


def test_displacement_never_pushes_expenses_negative():
    expenses = np.array([0.0, 100.0, 1_000.0])
    new_free_hours = np.array([500.0, 5_000.0, 100.0])
    result = displaced_childcare_expenses(expenses, new_free_hours, 1.0)
    assert (result >= 0).all()
    assert result[0] == 0
    assert result[1] == 0


def test_displacement_of_zero_leaves_expenses_untouched():
    expenses = np.array([250.0, 1_000.0])
    result = displaced_childcare_expenses(expenses, np.array([500.0, 500.0]), 0.0)
    assert (result == expenses).all()


def test_displacement_applies_only_the_displaced_share():
    # £1,000 of new free hours at 71.4% displacement removes £714 of paid care.
    result = displaced_childcare_expenses(
        np.array([2_000.0]), np.array([1_000.0]), sources.FREE_HOURS_DISPLACEMENT
    )
    assert result[0] == 2_000 - 1_000 * sources.FREE_HOURS_DISPLACEMENT


def test_hours_worked_is_annual_in_policyengine_uk():
    """Guards the units bug this analysis works around.

    policyengine-uk's impute_wages_for_nonworkers computes
    employment_income / (hours_worked * 52), but hours_worked is annual, so it
    divides by 52 twice and imputes about £194 of annual earnings for entering
    part-time work instead of roughly £21,600 (policyengine-uk#1839).

    An earlier version of this test did arithmetic on two local constants and
    so could not detect anything about policyengine-uk at all. This one reads
    the variable's own metadata, so a release that redefines the units fails
    here rather than silently re-breaking the extensive margin.
    """
    from policyengine_uk.system import system

    variable = system.variables["hours_worked"]
    assert variable.definition_period == "year", (
        "hours_worked is annual; the imputation in labour_supply.py divides by "
        "WEEKS_PER_YEAR exactly once on that basis"
    )
    assert "annual" in variable.label.lower(), (
        f"hours_worked may have been redefined: {variable.label!r}"
    )


def test_the_widened_universal_entitlement_does_not_stack_on_the_targeted_offer():
    """A 2-year-old must not draw both free entitlements.

    policyengine-uk's exclusions were written for a system where the universal
    entitlement started at age 3, so `targeted_childcare_entitlement_eligible`
    excludes extended-eligible families and nothing else. Widening the age
    floor to 0.75 breaks that assumption: without the reform's added exclusion
    a non-working family on qualifying benefits draws 570 hours from the
    targeted offer and 570 from the universal one — 30 free hours a week where
    the reform gives 15.
    """
    import inspect

    from free_childcare_reform.reforms import _universal_excludes_targeted

    source = inspect.getsource(_universal_excludes_targeted)
    assert "targeted_childcare_entitlement_eligible" in source
    assert "~(targeted & in_targeted_age)" in source, (
        "the universal entitlement must step aside where the targeted offer applies"
    )


# Behavioural tests of the reform variables. These build a household and read
# what the model pays, rather than inspecting source text — the age-floor
# limitation below was found by writing them.

YEAR = 2027


def _situation(child_age: float, employment_income: float = 0):
    """One parent, one child, in England."""
    return {
        "people": {
            "child": {"age": {YEAR: child_age}},
            "parent": {"age": {YEAR: 32}, "employment_income": {YEAR: employment_income}},
        },
        "benunits": {"bu": {"members": ["child", "parent"]}},
        "households": {"hh": {"members": ["child", "parent"], "country": {YEAR: "ENGLAND"}}},
    }


def _free_entitlement(child_age: float, employment_income: float = 0, reform: bool = False):
    from policyengine_uk import Simulation

    from free_childcare_reform.pipeline import PARAMETER_YEARS
    from free_childcare_reform.reforms import free_hours_scenario

    situation = _situation(child_age, employment_income)
    sim = (
        Simulation(situation=situation, scenario=free_hours_scenario(PARAMETER_YEARS))
        if reform
        else Simulation(situation=situation)
    )
    return {
        variable: float(sim.calculate(variable, YEAR).sum())
        for variable in (
            "universal_childcare_entitlement",
            "targeted_childcare_entitlement",
        )
    }


def test_the_reform_pays_a_one_year_old_of_a_non_working_family():
    """The core of leg 1: 15 free hours with no work test, from age 1."""
    baseline = _free_entitlement(1)
    reform = _free_entitlement(1, reform=True)
    assert baseline["universal_childcare_entitlement"] == 0
    assert reform["universal_childcare_entitlement"] > 6_000


def test_the_reform_pays_nothing_to_a_child_recorded_as_age_zero():
    """A known limitation, pinned so it cannot change unnoticed.

    The reform covers children from 9 months, but FRS ages are whole years, so
    the 0.75 age floor evaluates as `age >= 1` and the 9-to-12-month cohort
    gets nothing — roughly £0.28bn missing from the free-hours leg. If a future
    dataset carries sub-year ages this test fails, which is the signal to
    re-cost the leg rather than a regression.
    """
    assert _free_entitlement(0, reform=True)["universal_childcare_entitlement"] == 0


def test_a_two_year_old_on_qualifying_benefits_gets_fifteen_hours_not_thirty():
    """The non-stacking fix, tested by what is paid rather than by source text.

    Without it the widened universal entitlement stacks on the disadvantaged
    two-year-old offer and the child draws 570 hours from each.
    """
    baseline = _free_entitlement(2)
    reform = _free_entitlement(2, reform=True)
    # A family with no earnings receives Universal Credit, so it qualifies for
    # the disadvantaged offer.
    assert baseline["targeted_childcare_entitlement"] > 0
    assert reform["universal_childcare_entitlement"] == 0, (
        "the universal entitlement must step aside where the targeted offer applies"
    )
    assert reform["targeted_childcare_entitlement"] == pytest.approx(
        baseline["targeted_childcare_entitlement"]
    )


def test_three_and_four_year_olds_are_unchanged_by_the_reform():
    """They already hold the universal entitlement, so the age floor is moot."""
    for age in (3, 4):
        baseline = _free_entitlement(age)
        reform = _free_entitlement(age, reform=True)
        assert baseline["universal_childcare_entitlement"] > 0
        assert reform["universal_childcare_entitlement"] == pytest.approx(
            baseline["universal_childcare_entitlement"]
        ), age


def test_cost_contingent_support_reaches_the_adult_whose_work_decision_it_bears_on():
    """`tax_free_childcare` is paid on the child's row, not the parent's.

    So `map_to="person"` is a no-op that leaves every adult reading zero, and
    the out-of-work subtraction silently does nothing — which is what happened
    (PolicyEngine/free-childcare-reform#3 review). The award has to be
    aggregated to the benefit unit and projected back onto its adults, which
    is also how `household_net_income` carries it.
    """
    import numpy as np
    from policyengine_uk import Simulation

    from free_childcare_reform.labour_supply import _support_per_adult

    YEAR = 2027
    situation = {
        "people": {
            "child": {"age": {YEAR: 3}},
            "parent": {
                "age": {YEAR: 32},
                "employment_income": {YEAR: 35_000},
                "childcare_expenses": {YEAR: 6_000},
            },
        },
        "benunits": {"bu": {"members": ["child", "parent"]}},
        "households": {"hh": {"members": ["child", "parent"], "country": {YEAR: "ENGLAND"}}},
    }
    sim = Simulation(situation=situation)
    per_person = np.asarray(sim.calculate("tax_free_childcare", YEAR, map_to="person"), float)
    projected = _support_per_adult(sim, YEAR)
    adult = np.asarray(sim.calculate("adult_index", YEAR), float) > 0

    benunit_total = float(
        np.asarray(sim.calculate("tax_free_childcare", YEAR, map_to="benunit"), float).sum()
    )
    if benunit_total == 0:
        pytest.skip("no support in this situation to project")
    assert per_person[adult].sum() == 0, "support sits on the child's row, as expected"
    assert projected[adult].sum() == pytest.approx(benunit_total * adult.sum()), (
        "every adult must see the benefit unit's award"
    )


def test_the_out_of_work_support_adjustment_applies_only_to_existing_workers():
    """Three deterministic cases, from the #3 review's C10.

    The adjustment removes support attached to childcare a leaver would stop
    buying. For someone already out of work it is a double credit: their
    recorded `childcare_expenses` is a fixed input, so the support sits in
    `household_net_income` in both employment states and cancels, while the
    care they would newly buy is already counted net of the subsidy.
    """
    import inspect

    from free_childcare_reform import labour_supply

    source = inspect.getsource(labour_supply._net_gain_to_work)
    assert "already_working" in source, (
        "the out-of-work support adjustment must be restricted to people who are already in work"
    )


@pytest.mark.parametrize(
    "recorded_expenses,employment_income,label",
    [
        (6_000, 35_000, "worker with recorded childcare"),
        (0, 0, "non-worker with no recorded childcare"),
        (6_000, 0, "non-worker with recorded childcare"),
    ],
)
def test_the_gain_to_work_identity_holds_for_each_case(recorded_expenses, employment_income, label):
    """The gain to work is in-work income less childcare, minus out-of-work.

    Only an existing worker's out-of-work side has support removed. The third
    case is the one that was wrong: a non-worker with recorded spend was
    credited that support a second time.
    """
    import numpy as np
    from policyengine_uk import Simulation

    from free_childcare_reform.labour_supply import _net_gain_to_work

    YEAR = 2027
    situation = {
        "people": {
            "child": {"age": {YEAR: 3}},
            "parent": {
                "age": {YEAR: 32},
                "employment_income": {YEAR: employment_income},
                "childcare_expenses": {YEAR: recorded_expenses},
            },
        },
        "benunits": {"bu": {"members": ["child", "parent"]}},
        "households": {"hh": {"members": ["child", "parent"], "country": {YEAR: "ENGLAND"}}},
    }
    sim = Simulation(situation=situation)
    people = len(np.asarray(sim.calculate("age", YEAR)))
    frame = _net_gain_to_work(
        sim, YEAR, np.zeros(people), np.full(people, 20_000.0), count_adults=1
    )
    working = np.asarray(sim.calculate("employment_income", YEAR), float) > 0
    expected_out_of_work = frame["out_of_work_income"].to_numpy() - np.where(
        working, frame["out_of_work_support"].to_numpy(), 0.0
    )
    assert np.allclose(
        frame["gain_to_work"].to_numpy(),
        frame["in_work_income_net_of_childcare"].to_numpy() - expected_out_of_work,
    ), label
    if not working.any():
        assert np.allclose(
            frame["out_of_work_income_net_of_childcare"].to_numpy(),
            frame["out_of_work_income"].to_numpy(),
        ), f"{label}: a non-worker's out-of-work income must not lose support"
