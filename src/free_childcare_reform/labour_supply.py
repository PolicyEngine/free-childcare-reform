"""Extensive-margin labour supply response to the childcare reform.

Why this module exists rather than calling policyengine-uk's dynamics directly
==============================================================================

policyengine-uk ships an OBR-methodology labour supply framework in
``policyengine_uk.dynamics``. Two things about it matter here.

First, ``apply_labour_supply_responses`` runs only the *intensive* margin;
``apply_participation_responses`` is present but commented out of the
coordinator as a placeholder. Childcare is the canonical *extensive*-margin
question, so the margin that matters is the one that is not wired up.

Second, and more important, the participation model measures work incentives
as the gain to work in ``household_net_income``. That variable does not net off
childcare costs. Childcare is a cost of working, so the main channel by which a
childcare subsidy raises maternal employment — it cuts the price of the care
that working requires — is invisible to it. Run unmodified against this reform
it reports employment *falling*, because the reform removes work conditions
from childcare support and so lowers the gain to work as that variable measures
it. That effect is real and is kept, but on its own it is only half the story.

This module therefore reuses the parts of policyengine-uk that are right —
``calculate_participation_elasticities`` (the OBR Table A1 elasticities, which
vary by gender, partner employment status, age of youngest child and earnings
quintile, exactly the dimensions childcare reform operates on) and
``calculate_gain_to_work`` (which recomputes the whole tax-benefit system with
each adult's employment switched off) — and adds the childcare terms the
framework is missing:

    gain to work = in-work net income
                 - childcare paid out of pocket while working
                 - (out-of-work net income - cost-contingent childcare support)

Out-of-work childcare spend is taken as zero for the marginal worker, which is
the standard assumption. That is also why cost-contingent support has to come
back out of out-of-work income: ``childcare_expenses`` is a fixed input, so
without it a non-worker is credited with a subsidy on care they are not buying.
See :func:`_net_gain_to_work`.

Responses are applied deterministically as expected values (each person's
weight is scaled by their participation probability change) rather than by the
Bernoulli draw in the upstream module, so that the result does not depend on a
random seed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from policyengine_uk.dynamics.participation import (
    calculate_earnings_quintile,
    calculate_gain_to_work,
    calculate_participation_elasticities,
    impute_wages_for_nonworkers,
)

from . import sources

# Weekly hours assumed for someone entering work, matching the upstream OBR
# implementation's default and its FTE conversion.
HOURS_FOR_NEW_ENTRANTS = 18.8
FULL_TIME_HOURS = 37.5


def _excluded(sim, year: int, count_adults: int = 2) -> np.ndarray:
    """Adults the OBR framework holds outside the participation margin.

    The upstream helper reads employment status and age for the simulation's
    default period; this restates it for an explicit year.
    """
    employment_status = np.asarray(sim.calculate("employment_status", year))
    self_employed = np.isin(employment_status, ["FT_SELF_EMPLOYED", "PT_SELF_EMPLOYED"])
    student = employment_status == "STUDENT"
    age = np.asarray(sim.calculate("age", year), float)
    adult_index = np.asarray(sim.calculate("adult_index", year), float)
    return (
        self_employed
        | student
        | (age >= 60)
        | (adult_index == 0)
        | (adult_index >= count_adults + 1)
    )


def _responds_to_childcare(sim, year: int) -> np.ndarray:
    """Adults whose labour supply the childcare reform can plausibly move.

    Brewer et al. find the participation effect of the English entitlements is
    confined to parents whose *youngest* child is in the eligible age band, and
    absent for those who also have a younger, non-eligible child — they still
    need care for the younger one, so the entitlement does not free them to
    work. That is the single most important structural restriction on the
    response, and it replicates internationally.

    The reform's band runs from 9 months to school age. ``youngest_child_age``
    is whole years, so a benefit unit whose youngest child is under 1 is
    treated as having a child below the band and is excluded.
    """
    if not sources.RESTRICT_TO_YOUNGEST_CHILD_ELIGIBLE:
        return np.ones(len(np.asarray(sim.calculate("age", year))), bool)
    youngest = np.asarray(
        sim.calculate("youngest_child_age", year, map_to="person").values, float
    )
    return (youngest >= 1) & (youngest <= 4)


def _net_gain_to_work(
    sim,
    year: int,
    childcare_cost_when_working: np.ndarray,
    cost_contingent_support: np.ndarray,
    count_adults: int = 2,
) -> pd.DataFrame:
    """Gain to work, with childcare treated as a cost of working.

    Two corrections to the upstream gain-to-work measure, both in the same
    direction — they restore childcare's role as a price of working:

    * **In-work income** has out-of-pocket childcare spend subtracted. Working
      requires buying care; ``household_net_income`` does not net it off.

    * **Out-of-work income** has cost-contingent childcare support subtracted.
      ``calculate_gain_to_work`` recomputes the whole tax-benefit system with
      employment switched off, but ``childcare_expenses`` is a fixed input, so a
      non-worker is still credited with a subsidy on childcare they would not be
      buying. That is harmless in the baseline, where Tax-Free Childcare carries
      a work condition and drops out anyway, but the reform's subsidy has no
      work condition, so without this it would appear to be worth just as much
      out of work as in it — and the reform would look like it weakened work
      incentives when it strengthens them.

    Free-hours entitlements are deliberately *not* subtracted here: they are
    in-kind and, under this reform's first tier, genuinely available whether or
    not the parent works. Their availability out of work is a real reduction in
    the gain to work and the model should show it.
    """
    frame = calculate_gain_to_work(
        sim,
        year,
        hours_for_new_entrants=HOURS_FOR_NEW_ENTRANTS,
        count_adults=count_adults,
        impute_nonworker_wages=True,
    )
    frame["childcare_cost_when_working"] = childcare_cost_when_working
    frame["in_work_income_net_of_childcare"] = (
        frame["in_work_income"] - childcare_cost_when_working
    )
    frame["out_of_work_income_net_of_childcare"] = (
        frame["out_of_work_income"] - cost_contingent_support
    )
    frame["gain_to_work"] = (
        frame["in_work_income_net_of_childcare"]
        - frame["out_of_work_income_net_of_childcare"]
    )
    return frame


def prepare(
    baseline_sim,
    reform_sim,
    year: int,
    baseline_childcare_cost: np.ndarray,
    reform_childcare_cost: np.ndarray,
    baseline_cost_contingent_support: np.ndarray,
    reform_cost_contingent_support: np.ndarray,
    count_adults: int = 2,
) -> dict:
    """Everything the response needs that does not depend on the elasticity.

    Computing the gain to work means recomputing the whole tax-benefit system
    with each adult's employment switched off, twice per simulation. None of it
    varies with the elasticity scale, so it is done once here and reused across
    the low, central and high bounds.

    ``baseline_childcare_cost`` and ``reform_childcare_cost`` are person-level
    annual out-of-pocket childcare spend while working, mapped to the adults who
    would bear it (the childcare-paying benefit unit's members).
    """
    baseline = _net_gain_to_work(
        baseline_sim,
        year,
        baseline_childcare_cost,
        baseline_cost_contingent_support,
        count_adults,
    )
    reform = _net_gain_to_work(
        reform_sim,
        year,
        reform_childcare_cost,
        reform_cost_contingent_support,
        count_adults,
    )

    gtw_baseline = baseline["gain_to_work"].to_numpy()
    gtw_reform = reform["gain_to_work"].to_numpy()

    # Percentage change in the gain to work, the OBR framework's driver. Only
    # defined where the baseline gain to work is positive; where working does
    # not pay in the baseline there is no proportional change to scale.
    gtw_pct_change = np.zeros_like(gtw_baseline)
    positive = gtw_baseline > 0
    gtw_pct_change[positive] = (
        gtw_reform[positive] - gtw_baseline[positive]
    ) / gtw_baseline[positive]

    earnings_quintile = calculate_earnings_quintile(
        baseline_sim, year, HOURS_FOR_NEW_ENTRANTS, random_seed=42
    )
    elasticity_wrt_income = calculate_participation_elasticities(
        baseline_sim, earnings_quintile
    )

    # OBR Appendix E: an elasticity with respect to in-work income becomes an
    # elasticity with respect to the gain to work by scaling by
    # (1 - replacement rate).
    in_work = baseline["in_work_income"].to_numpy()
    out_of_work = baseline["out_of_work_income"].to_numpy()
    replacement_rate = np.zeros_like(in_work)
    working_positive = in_work > 0
    replacement_rate[working_positive] = (
        out_of_work[working_positive] / in_work[working_positive]
    )
    replacement_rate = np.clip(replacement_rate, 0, 1)
    elasticity_wrt_gain_to_work = elasticity_wrt_income * (1 - replacement_rate)

    employment_income = np.asarray(baseline_sim.calculate("employment_income", year), float)
    excluded = _excluded(baseline_sim, year, count_adults)
    eligible = ~excluded & _responds_to_childcare(baseline_sim, year)
    currently_working = eligible & (employment_income > 0)
    currently_not_working = eligible & (employment_income == 0)

    weights = np.asarray(
        baseline_sim.calculate("household_weight", year, map_to="person").values, float
    )
    imputed_wages = impute_wages_for_nonworkers(baseline_sim, year, HOURS_FOR_NEW_ENTRANTS)
    # For someone moving into work the exchequer gains their gross earnings less
    # the rise in their household's net income — income tax and National
    # Insurance paid, plus benefits withdrawn. Measured on the reform's
    # tax-benefit system, so a mover's newly-won childcare entitlements are
    # netted off the gain rather than double-counted.
    reform_gain = (
        reform["in_work_income"].to_numpy() - reform["out_of_work_income"].to_numpy()
    )

    return {
        "gtw_pct_change": gtw_pct_change,
        "elasticity_wrt_gain_to_work": elasticity_wrt_gain_to_work,
        "eligible": eligible,
        "currently_working": currently_working,
        "currently_not_working": currently_not_working,
        "employment_income": employment_income,
        "imputed_wages": imputed_wages,
        "reform_gain": reform_gain,
        "weights": weights,
    }


def participation_response(prepared: dict, elasticity_scale: float = 1.0) -> dict:
    """Expected-value extensive-margin response at one elasticity scale.

    ``prepared`` comes from :func:`prepare`, which holds everything that does
    not vary with the elasticity. ``elasticity_scale`` scales the OBR
    participation elasticities uniformly and is the handle for the low, central
    and high bounds; see ``sources``.
    """
    gtw_pct_change = prepared["gtw_pct_change"]
    eligible = prepared["eligible"]
    currently_working = prepared["currently_working"]
    currently_not_working = prepared["currently_not_working"]
    employment_income = prepared["employment_income"]
    imputed_wages = prepared["imputed_wages"]
    reform_gain = prepared["reform_gain"]
    weights = prepared["weights"]
    elasticity = prepared["elasticity_wrt_gain_to_work"] * elasticity_scale

    # Proportional change in each person's probability of working.
    participation_change = np.where(eligible, elasticity * gtw_pct_change, 0.0)
    # Bound the proportional change: an elasticity applied to a large
    # proportional change in a small baseline gain to work can otherwise imply
    # a probability change above one.
    participation_change = np.clip(
        participation_change,
        -sources.PARTICIPATION_CHANGE_BOUND,
        sources.PARTICIPATION_CHANGE_BOUND,
    )

    # Expected entries and exits, rather than a stochastic draw. A non-worker
    # with a positive change enters with that probability; a worker with a
    # negative change leaves with its magnitude.
    entry_probability = np.where(currently_not_working, np.maximum(participation_change, 0), 0)
    exit_probability = np.where(currently_working, np.maximum(-participation_change, 0), 0)
    entrants = float((entry_probability * weights).sum())
    leavers = float((exit_probability * weights).sum())
    net_entrants = entrants - leavers

    earnings_gained = float((entry_probability * imputed_wages * weights).sum())
    earnings_lost = float((exit_probability * employment_income * weights).sum())
    net_earnings = earnings_gained - earnings_lost

    ftes = net_entrants * (HOURS_FOR_NEW_ENTRANTS / FULL_TIME_HOURS)

    revenue_from_entrants = float(
        (entry_probability * (imputed_wages - reform_gain) * weights).sum()
    )
    revenue_lost_to_leavers = float(
        (exit_probability * (employment_income - reform_gain) * weights).sum()
    )
    net_revenue = revenue_from_entrants - revenue_lost_to_leavers

    return {
        "entrants": entrants,
        "leavers": leavers,
        "net_entrants": net_entrants,
        "net_ftes": ftes,
        "earnings_gained_gbp": earnings_gained,
        "earnings_lost_gbp": earnings_lost,
        "net_earnings_gbp": net_earnings,
        "revenue_from_entrants_gbp": revenue_from_entrants,
        "revenue_lost_to_leavers_gbp": revenue_lost_to_leavers,
        "net_revenue_gbp": net_revenue,
        "elasticity_scale": elasticity_scale,
        "responding_adults_m": float(weights[eligible].sum()) / 1e6,
        "mean_gain_to_work_change_pct": float(
            np.average(gtw_pct_change[eligible], weights=weights[eligible])
        )
        if weights[eligible].sum()
        else 0.0,
    }


def price_elasticity_response(
    baseline_sim,
    reform_sim,
    year: int,
    price_elasticity: float,
    count_adults: int = 2,
) -> dict:
    """Independent cross-check using the childcare price elasticity directly.

    The gain-to-work model above works through the whole tax-benefit system.
    This is the literature's own arithmetic instead: apply a childcare price
    elasticity of maternal employment to the proportional fall in the price of
    the childcare that working requires, scaled by additionality.

    The two are not independent evidence — the elasticity bounds on the
    gain-to-work model are set from the same literature — but they are
    independent *arithmetic*, and they answer different questions. The
    gain-to-work model captures that the reform removes work conditions from
    childcare support, which cuts work incentives. This one sees only the price
    of care and so can only be positive. Reporting both bounds the answer.

    The price change is scaled by additionality because a free hour that
    displaces an hour the family was already buying changes what they pay, not
    whether they can work. Brewer et al. put additionality at about 29%.
    """
    responding = _responds_to_childcare(baseline_sim, year) & ~_excluded(
        baseline_sim, year, count_adults
    )
    employment_income = np.asarray(baseline_sim.calculate("employment_income", year), float)
    gender = np.asarray(baseline_sim.calculate("gender", year)).astype(str)
    weights = np.asarray(
        baseline_sim.calculate("household_weight", year, map_to="person").values, float
    )
    # The literature's estimates are for maternal employment specifically.
    mothers = responding & (gender == "FEMALE")
    not_working_mothers = mothers & (employment_income == 0)

    def net_price(sim) -> float:
        """Aggregate childcare cost to families, net of cost-contingent support."""
        expenses = float(sim.calculate("childcare_expenses", year).sum())
        support = float(sim.calculate("tax_free_childcare", year).sum())
        return expenses - support

    baseline_price = net_price(baseline_sim)
    reform_price = net_price(reform_sim)
    price_change = (reform_price - baseline_price) / baseline_price if baseline_price else 0.0
    effective_price_change = price_change * sources.FREE_HOURS_ADDITIONALITY

    # Elasticity is negative and the price change is negative, so employment rises.
    employment_change_pct = price_elasticity * effective_price_change
    affected = float((not_working_mothers * weights).sum())

    # The elasticity is defined on the employment *rate* of the affected group,
    # so it applies to mothers in the band who are currently employed.
    employed_in_band = float(((mothers & (employment_income > 0)) * weights).sum())
    entrants = employed_in_band * employment_change_pct

    return {
        "price_elasticity": price_elasticity,
        "net_childcare_price_change": round(price_change, 4),
        "additionality": round(sources.FREE_HOURS_ADDITIONALITY, 4),
        "effective_price_change": round(effective_price_change, 4),
        "employment_change_pct": round(employment_change_pct, 4),
        "mothers_in_band_employed_m": round(employed_in_band / 1e6, 3),
        "mothers_in_band_not_working_m": round(affected / 1e6, 3),
        "entrants": round(entrants),
        "net_ftes": round(entrants * (HOURS_FOR_NEW_ENTRANTS / FULL_TIME_HOURS)),
    }
