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
    gets nothing. Measured directly, the whole age-zero group is worth £1.76bn
    and a three-month share about £0.44bn — 22% of the free-hours leg. If a future
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


class _StubSimulation:
    """The three variables `_support_per_adult` reads, and nothing else.

    A situation simulation will not produce Tax-Free Childcare without more
    scaffolding than a mechanics test should carry, and the earlier version of
    this test skipped for exactly that reason — it never reached its
    assertions. A stub makes the projection deterministic and lets the awkward
    shapes be covered: several benefit units, several children, duplicate ids.
    """

    def __init__(self, totals, benunit_ids, person_benunit_ids):
        self._values = {
            ("tax_free_childcare", "benunit"): np.asarray(totals, float),
            ("benunit_id", None): np.asarray(benunit_ids),
            ("benunit_id", "person"): np.asarray(person_benunit_ids),
        }

    def calculate(self, variable, year, map_to=None):
        return self._values[(variable, map_to)]


def test_support_projects_from_the_benefit_unit_onto_each_of_its_people():
    """The award is paid on the child's row; every member must see it.

    Two benefit units, the first with two children and two adults, the second
    with one of each. Reading `tax_free_childcare` per person leaves adults at
    zero, which is the bug this projection fixes.
    """
    from free_childcare_reform.labour_supply import _support_per_adult

    sim = _StubSimulation(
        totals=[7_500.0, 2_000.0],
        benunit_ids=[10, 20],
        person_benunit_ids=[10, 10, 10, 10, 20, 20],
    )
    projected = _support_per_adult(sim, 2027)
    assert projected.tolist() == [7_500.0, 7_500.0, 7_500.0, 7_500.0, 2_000.0, 2_000.0]


def test_a_benefit_unit_with_no_award_projects_zero_rather_than_nothing():
    from free_childcare_reform.labour_supply import _support_per_adult

    sim = _StubSimulation([0.0, 3_000.0], [1, 2], [1, 1, 2, 2])
    assert _support_per_adult(sim, 2027).tolist() == [0.0, 0.0, 3_000.0, 3_000.0]


def test_the_projection_refuses_an_ambiguous_or_incomplete_join():
    """Silence here is what made the original bug invisible."""
    from free_childcare_reform.labour_supply import _support_per_adult

    duplicated = _StubSimulation([1.0, 2.0], [5, 5], [5, 5])
    with pytest.raises(ValueError, match="not unique"):
        _support_per_adult(duplicated, 2027)

    incomplete = _StubSimulation([1.0], [5], [5, 6])
    with pytest.raises(ValueError, match="missing"):
        _support_per_adult(incomplete, 2027)


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


# Mutation guards. The review reverted six fixes at once and the suite still
# reported "32 passed", so each of these asserts the mechanism rather than a
# figure a regenerated artifact would carry along with the mutation.


def test_the_effective_subsidy_rate_is_weighted_and_uses_the_benefit_unit_weight():
    """Two distinct mistakes: no weights at all, and the wrong weights."""
    import inspect

    from free_childcare_reform.labour_supply import _effective_subsidy_rate

    source = inspect.getsource(_effective_subsidy_rate)
    assert "MicroSeries" in source, "the rate must be survey-weighted"
    assert 'calculate("benunit_weight"' in source, (
        "a benefit-unit rate takes the benefit-unit weight, not the household "
        "weight mapped onto benefit units"
    )
    assert 'map_to="benunit"' not in source.split("benunit_weight")[1][:200]


def test_leaver_ftes_use_observed_hours_and_entrants_the_assumption():
    import inspect

    from free_childcare_reform import labour_supply

    source = inspect.getsource(labour_supply.participation_response)
    assert "weekly_hours_worked" in source, (
        "leavers give up observed hours; using the entrant assumption for both "
        "overstates the net full-time equivalent"
    )
    # Asserting the names exist is not enough: a mutation that computes them
    # and then ignores them passed an earlier version of this test.
    assert "ftes = entrant_ftes - leaver_ftes" in source, (
        "the net full-time equivalent must be the difference of the two, not "
        "net entrants at the entrant assumption"
    )


def test_quintiles_are_placed_against_thresholds_not_ranked():
    """Ranking split tied imputed earnings by input row order."""
    import inspect

    from free_childcare_reform.labour_supply import potential_earnings_quintile

    source = inspect.getsource(potential_earnings_quintile)
    assert "searchsorted" in source, "quintiles must be threshold placement"
    assert "cumsum" not in source, "weighted-rank assignment was order-dependent"


def test_the_age_floor_is_the_extended_scheme_floor():
    """0.75 evaluates as age 1 on whole-year ages; 1.0 would hide that."""
    from free_childcare_reform.reforms import UNIVERSAL_ENTITLEMENT_AGE_MIN

    assert UNIVERSAL_ENTITLEMENT_AGE_MIN == 0.75, (
        "the floor is the extended scheme's, and the fact that whole-year ages "
        "make it behave as age 1 is a documented limitation, not a reason to "
        "write 1.0"
    )
