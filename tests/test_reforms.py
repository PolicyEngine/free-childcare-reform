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
