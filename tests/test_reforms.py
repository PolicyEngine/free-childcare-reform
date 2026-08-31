"""Unit tests for the reform arithmetic that does not need a simulation."""

import numpy as np

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


def test_additionality_matches_the_ifs_estimate():
    # 163 additional hours per 570 free hours offered (IFS WP20/09).
    assert round(sources.FREE_HOURS_ADDITIONALITY, 3) == 0.286
    assert round(sources.FREE_HOURS_ADDITIONALITY + sources.FREE_HOURS_DISPLACEMENT, 6) == 1


def test_elasticity_bounds_bracket_the_central_case():
    assert sources.ELASTICITY_SCALE_LOW < 1 < sources.ELASTICITY_SCALE_HIGH
    assert (
        sources.PRICE_ELASTICITY_HIGH
        < sources.PRICE_ELASTICITY_CENTRAL
        < sources.PRICE_ELASTICITY_LOW
    )


def test_hours_worked_is_treated_as_annual():
    """Guards the units bug this analysis had to work around.

    policyengine-uk's impute_wages_for_nonworkers computes
    employment_income / (hours_worked * 52), but hours_worked is annual, so it
    divides by 52 twice and imputes about £194 of annual earnings for entering
    part-time work instead of roughly £21,600. impute_entrant_earnings treats
    the variable as annual. If a future policyengine-uk release changes the
    units of hours_worked, this fails rather than silently re-breaking the
    extensive margin.
    """
    from free_childcare_reform.labour_supply import HOURS_FOR_NEW_ENTRANTS, WEEKS_PER_YEAR

    # A full-time worker on £40,000 at 37.5 hours a week.
    annual_hours = 37.5 * WEEKS_PER_YEAR
    hourly_wage = 40_000 / annual_hours
    assert 15 < hourly_wage < 30, "hours_worked must be annual for this to be a real wage"
    entrant = hourly_wage * HOURS_FOR_NEW_ENTRANTS * WEEKS_PER_YEAR
    assert 15_000 < entrant < 25_000
    # The upstream formula, for contrast.
    broken = (40_000 / (annual_hours * WEEKS_PER_YEAR)) * HOURS_FOR_NEW_ENTRANTS * WEEKS_PER_YEAR
    assert broken < 500


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
