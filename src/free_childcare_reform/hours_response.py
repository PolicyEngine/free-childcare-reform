"""Intensive-margin hours response to the childcare reform, for parents in work.

The extensive-margin model in :mod:`labour_supply` moves people into and out
of work. This module moves the hours of people who stay in work, driven by the
change in the price of the childcare they buy. It exists because
policyengine-uk's own intensive-margin machinery
(``apply_labour_supply_responses``) is driven by income and substitution
elasticities on *earnings*; a childcare subsidy changes the price of an input
to working, which that framework does not see.

The response is

    hours change (%) = HOURS_PRICE_ELASTICITY * out-of-pocket price change (%)

for each adult in the responsive population (see
:func:`labour_supply.responds_to_childcare`) who is in work and pays for
childcare in the baseline. Hours and earnings move together at a constant
hourly wage. The exchequer effect is not an assumed rate: the reform
simulation is rerun with the changed earnings, and the revenue is the extra
earnings less the rise in household net income — tax and National Insurance
paid plus benefits withdrawn, on the reform's tax-benefit system.

The elasticity is a total-hours effect from Brewer et al. that already
contains the participation channel the extensive model reports separately, so
adding the two overstates the whole; see ``sources.HOURS_PRICE_ELASTICITY``.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from microdf import MicroSeries

from . import sources
from .labour_supply import (
    FULL_TIME_HOURS,
    WEEKS_PER_YEAR,
    _excluded,
    _support_per_adult,
    _values,
    responds_to_childcare,
)


def out_of_pocket_childcare(sim, year: int, childcare_cost: np.ndarray) -> np.ndarray:
    """What an adult's benefit unit pays for childcare after cost-contingent support.

    ``childcare_cost`` is the benefit unit's ``childcare_expenses`` projected
    onto its adults. Tax-Free Childcare (or the subsidy that replaces it) and
    the Universal Credit childcare element are both paid against that spend,
    so both come off it: the price a parent responds to is what they are left
    paying. The UC element does not change under the reform, but it belongs in
    the base the change is measured against.
    """
    uc_element = _values(sim, "uc_childcare_element", year, map_to="benunit").astype(float)
    benunit_ids = _values(sim, "benunit_id", year)
    person_benunit_ids = _values(sim, "benunit_id", year, map_to="person")
    uc_per_adult = pd.Series(uc_element, index=benunit_ids).reindex(person_benunit_ids).to_numpy()
    return np.maximum(childcare_cost - _support_per_adult(sim, year) - uc_per_adult, 0.0)


def hours_response(
    baseline_sim,
    reform_sim,
    year: int,
    baseline_childcare_cost: np.ndarray,
    reform_childcare_cost: np.ndarray,
    rerun_with_earnings: Callable[[np.ndarray], object],
    elasticity_scale: float = 1.0,
    count_adults: int = 2,
) -> dict:
    """Hours, earnings and revenue from parents in work changing their hours.

    ``rerun_with_earnings`` builds the reform simulation again with the given
    ``employment_income`` array, so the revenue on the extra hours is computed
    by the model rather than at an assumed marginal rate.
    ``elasticity_scale`` is the same low/central/high multiplier as the
    extensive margin, so one control moves both.
    """
    employment_income = np.asarray(baseline_sim.calculate("employment_income", year), float)
    hours = np.asarray(baseline_sim.calculate("hours_worked", year).values, float)
    weights = np.asarray(
        baseline_sim.calculate("household_weight", year, map_to="person").values, float
    )
    country = np.asarray(baseline_sim.calculate("country", year, map_to="person").values).astype(
        str
    )

    eligible = ~_excluded(baseline_sim, year, count_adults) & responds_to_childcare(
        baseline_sim, year
    )
    baseline_price = out_of_pocket_childcare(baseline_sim, year, baseline_childcare_cost)
    reform_price = out_of_pocket_childcare(reform_sim, year, reform_childcare_cost)
    responding = eligible & (employment_income > 0) & (hours > 0) & (baseline_price > 0)

    # Proportional change in the price of childcare, bounded at a 100% fall:
    # the subsidy and displaced free hours can only take out-of-pocket cost to
    # zero, and the bound guards the division where it is nearly there.
    price_change = np.zeros_like(baseline_price)
    price_change[responding] = (
        reform_price[responding] - baseline_price[responding]
    ) / baseline_price[responding]
    price_change = np.clip(price_change, -1.0, 1.0)

    elasticity = sources.HOURS_PRICE_ELASTICITY * elasticity_scale
    hours_change_share = np.where(responding, elasticity * price_change, 0.0)
    # Constant hourly wage: earnings scale with hours.
    extra_earnings = employment_income * hours_change_share
    extra_weekly_hours = hours * hours_change_share / WEEKS_PER_YEAR

    rerun = rerun_with_earnings(employment_income + extra_earnings)
    reform_income = np.asarray(reform_sim.calculate("household_net_income", year).values, float)
    rerun_income = np.asarray(rerun.calculate("household_net_income", year).values, float)
    household_gain = rerun_income - reform_income

    # The household's net gain, allocated back to the adults whose extra
    # earnings produced it in proportion to those earnings, so it can be laid
    # over the static distribution the same way as the participation response.
    household_ids = np.asarray(baseline_sim.calculate("household_id", year).values)
    person_household_ids = np.asarray(
        baseline_sim.calculate("household_id", year, map_to="person").values
    )
    gain_lookup = pd.Series(household_gain, index=household_ids)
    earnings_by_household = (
        pd.Series(extra_earnings, index=person_household_ids).groupby(level=0).sum()
    )
    person_household_gain = gain_lookup.reindex(person_household_ids).to_numpy()
    person_household_earnings = earnings_by_household.reindex(person_household_ids).to_numpy()
    share = np.divide(
        extra_earnings,
        person_household_earnings,
        out=np.zeros_like(extra_earnings),
        where=person_household_earnings != 0,
    )
    expected_net_income_change = person_household_gain * share

    household_weights = np.asarray(baseline_sim.calculate("household_weight", year).values, float)
    earnings_total = float(MicroSeries(extra_earnings, weights=weights).sum())
    net_income_total = float(MicroSeries(household_gain, weights=household_weights).sum())

    def _aggregate(mask: np.ndarray) -> dict:
        earnings = float(MicroSeries(extra_earnings[mask], weights=weights[mask]).sum())
        net_income = float(
            MicroSeries(expected_net_income_change[mask], weights=weights[mask]).sum()
        )
        return {
            "workers_in_scope": round(
                float(MicroSeries(responding[mask], weights=weights[mask]).sum())
            ),
            "workers_with_price_change": round(
                float(
                    MicroSeries(
                        (responding & (price_change != 0))[mask], weights=weights[mask]
                    ).sum()
                )
            ),
            "extra_weekly_hours": round(
                float(MicroSeries(extra_weekly_hours[mask], weights=weights[mask]).sum()), 1
            ),
            "ftes": round(
                float(MicroSeries(extra_weekly_hours[mask], weights=weights[mask]).sum())
                / FULL_TIME_HOURS,
                1,
            ),
            "earnings_gbp": round(earnings, 2),
            "net_revenue_gbp": round(earnings - net_income, 2),
        }

    by_country = {name.lower(): _aggregate(country == name) for name in sorted(set(country))}
    result = _aggregate(np.ones_like(responding, bool))
    # The UK revenue from the household-level rerun directly, so the country
    # allocation above can be checked against it rather than defining it.
    result["net_revenue_gbp"] = round(earnings_total - net_income_total, 2)
    result.update(
        {
            "mean_price_change_pct": round(
                float(MicroSeries(price_change[responding], weights=weights[responding]).mean())
                * 100,
                2,
            )
            if responding.any()
            else 0.0,
            "mean_hours_change_pct": round(
                float(
                    MicroSeries(hours_change_share[responding], weights=weights[responding]).mean()
                )
                * 100,
                3,
            )
            if responding.any()
            else 0.0,
            "elasticity": round(elasticity, 4),
            "by_country": by_country,
            "expected_net_income_change_per_person": expected_net_income_change,
        }
    )
    return result
