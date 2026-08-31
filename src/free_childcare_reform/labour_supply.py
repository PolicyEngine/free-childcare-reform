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
from microdf import MicroSeries
from policyengine_uk.dynamics.participation import calculate_participation_elasticities

from . import sources

# Weekly hours assumed for someone entering work, matching the upstream OBR
# implementation's default and its FTE conversion.
HOURS_FOR_NEW_ENTRANTS = 18.8
FULL_TIME_HOURS = 37.5
WEEKS_PER_YEAR = 52


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


def _hourly_wage(sim, year: int):
    """Implied hourly wage, and who counts as a donor for imputation."""
    employment_income = np.asarray(sim.calculate("employment_income", year), float)
    hours = np.asarray(sim.calculate("hours_worked", year).values, float)
    # hours_worked is ANNUAL in policyengine-uk (mean about 1,887 among
    # workers), so this is already an hourly rate. See impute_entrant_earnings.
    working = (employment_income > 0) & (hours > 0)
    wage = np.where(working, employment_income / np.where(hours > 0, hours, 1), 0.0)
    return employment_income, wage, working


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Median of a weighted sample, via microdf rather than by hand.

    microdf is what policyengine-uk returns from ``calculate``; using it here
    keeps every weighted statistic in this file on the same implementation
    rather than a local reimplementation that could drift from it.
    """
    if not len(values):
        return 0.0
    if float(np.sum(weights)) <= 0:
        return 0.0
    return float(MicroSeries(values, weights=weights).median())


def impute_entrant_earnings(
    sim,
    year: int,
    hours_for_new_entrants: float = HOURS_FOR_NEW_ENTRANTS,
) -> np.ndarray:
    """Annual earnings a non-worker would have on entering work.

    This replaces ``policyengine_uk.dynamics.participation.impute_wages_for_nonworkers``,
    which has a units bug. ``hours_worked`` in policyengine-uk is **annual**
    (mean about 1,887 among workers, implying a sensible £22.12 hourly wage),
    but that function computes ``employment_income / (hours_worked * 52)``,
    dividing by 52 a second time. The resulting hourly wage is about £0.43, and
    a non-worker is imputed roughly £194 of annual earnings for entering
    part-time work rather than about £21,600.

    The consequence is not subtle: entering work appears to pay almost nothing,
    so the extensive-margin response collapses to near-zero entrants and the
    exchequer appears to recover nothing from anyone who does move. Any
    participation estimate built on the upstream helper is wrong in the same
    direction. policyengine-uk is internally inconsistent about this —
    ``dynamics/progression.py`` reads ``hours_worked / 52`` as weekly hours,
    treating the variable as annual, which is the correct reading and the one
    used here.

    The donor pool also differs. Upstream draws donors from the person's
    *elasticity group*, which is keyed off ``calculate_earnings_quintile`` —
    and that function takes quintiles over the whole population including
    children, so its bottom two quintiles are 100% non-earners and contain no
    donors at all. Here a potential entrant is matched to working adults whose
    youngest child is the same age, which is the relevant comparison group for
    a childcare reform, using the weighted **median** wage so the 6% of workers
    with implausibly low implied hourly wages do not drag it down. The result
    is floored at the model's own minimum wage.
    """
    employment_income, wage, working = _hourly_wage(sim, year)
    weights = np.asarray(sim.calculate("household_weight", year, map_to="person").values, float)
    youngest = np.asarray(sim.calculate("youngest_child_age", year, map_to="person").values, float)
    adult = np.asarray(sim.calculate("adult_index", year), float) > 0
    minimum_wage = np.asarray(sim.calculate("minimum_wage", year).values, float)

    donors_overall = working & adult
    fallback = _weighted_median(wage[donors_overall], weights[donors_overall])

    imputed = np.zeros_like(employment_income)
    entrants = adult & ~working
    for age in np.unique(youngest[entrants & np.isfinite(youngest)]):
        band = youngest == age
        donors = band & donors_overall
        median_wage = _weighted_median(wage[donors], weights[donors]) if donors.any() else fallback
        target = band & entrants
        imputed[target] = np.maximum(median_wage, minimum_wage[target])
    remaining = entrants & (imputed == 0)
    imputed[remaining] = np.maximum(fallback, minimum_wage[remaining])
    return imputed * hours_for_new_entrants * WEEKS_PER_YEAR


def potential_earnings_quintile(sim, year: int, entrant_earnings: np.ndarray) -> np.ndarray:
    """Earnings quintile on *potential* earnings, across adults only.

    ``calculate_earnings_quintile`` upstream applies ``pd.qcut`` to raw
    ``employment_income`` over every person in the dataset — children included.
    More than half that population has no earnings, so its bottom two quintiles
    are entirely non-earners and every non-worker lands in Q1 or Q2. Since the
    OBR's Table A1 elasticities rise steeply as the quintile falls, that hands
    every potential entrant close to the top elasticity in the table.

    The OBR's quintiles are of the relevant adult population, on potential
    earnings — actual for workers, imputed for non-workers, which is what the
    upstream docstring describes but not what it does. That is what this
    computes.
    """
    employment_income = np.asarray(sim.calculate("employment_income", year), float)
    adult = np.asarray(sim.calculate("adult_index", year), float) > 0
    weights = np.asarray(sim.calculate("household_weight", year, map_to="person").values, float)
    potential = np.where(employment_income > 0, employment_income, entrant_earnings)

    quintile = np.ones(len(potential), dtype=int)
    index = np.flatnonzero(adult)
    if not len(index):
        return quintile
    values, adult_weights = potential[index], weights[index]
    total = adult_weights.sum()
    if total <= 0:
        return quintile

    # Assign by weighted rank rather than by value cutoffs. Every non-worker in
    # a given band shares one imputed value, so potential earnings carry large
    # point masses; cutting on values would drop a whole mass into a single
    # quintile and leave others empty. Ranking splits ties across the boundary
    # instead. The sort is stable, so the result is deterministic.
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(adult_weights[order])
    # Midpoint of each person's own weight, so a mass straddling a boundary is
    # divided rather than assigned whole to either side.
    position = (cumulative - adult_weights[order] / 2) / total
    ranked = np.clip((position * 5).astype(int) + 1, 1, 5)
    quintile[index[order]] = ranked
    return quintile


def _gain_to_work(
    sim,
    year: int,
    entrant_earnings: np.ndarray,
    count_adults: int = 2,
) -> pd.DataFrame:
    """In-work and out-of-work household net income for each adult.

    A local replacement for ``calculate_gain_to_work``, which is correct in
    structure but calls the broken wage imputation described above. The
    structure is kept: each adult's employment is switched off and on in turn
    and the whole tax-benefit system recomputed, so work-conditional support is
    handled properly. Only the imputed earnings differ.
    """
    original = np.asarray(sim.calculate("employment_income", year), float)
    adult_index = np.asarray(sim.calculate("adult_index", year), float)
    net_income = np.asarray(
        sim.calculate("household_net_income", year, map_to="person").values, float
    )
    out_of_work = net_income.copy()
    in_work = net_income.copy()

    def recompute(employment: np.ndarray) -> np.ndarray:
        sim.reset_calculations()
        sim.set_input("employment_income", year, employment)
        return np.asarray(
            sim.calculate("household_net_income", year, map_to="person").values, float
        )

    for index in range(1, count_adults + 1):
        is_adult = adult_index == index
        if not is_adult.any():
            continue
        without = original.copy()
        without[is_adult] = 0
        out_of_work[is_adult] = recompute(without)[is_adult]

        with_work = original.copy()
        with_work[is_adult] = np.where(
            original[is_adult] > 0, original[is_adult], entrant_earnings[is_adult]
        )
        in_work[is_adult] = recompute(with_work)[is_adult]

    # Restore the simulation to the state it was handed to us in.
    sim.reset_calculations()
    sim.set_input("employment_income", year, original)

    return pd.DataFrame({"in_work_income": in_work, "out_of_work_income": out_of_work})


def responds_to_childcare(sim, year: int) -> np.ndarray:
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

    That matches the cost side, which has the same hole. FRS ages are whole
    years, so the reform's 0.75 age floor evaluates as ``age >= 1`` and no
    child recorded as age 0 receives the entitlement in the reform simulation
    either — see ``reforms.py``. So this restriction is not excluding people
    the model pays; both sides omit the 9-to-12-month cohort together.
    """
    if not sources.RESTRICT_TO_YOUNGEST_CHILD_ELIGIBLE:
        return np.ones(len(np.asarray(sim.calculate("age", year))), bool)
    youngest = np.asarray(sim.calculate("youngest_child_age", year, map_to="person").values, float)
    return (youngest >= 1) & (youngest <= 4)


def _net_gain_to_work(
    sim,
    year: int,
    childcare_cost_when_working: np.ndarray,
    cost_contingent_support: np.ndarray,
    entrant_earnings: np.ndarray,
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
    frame = _gain_to_work(sim, year, entrant_earnings, count_adults)
    frame["childcare_cost_when_working"] = childcare_cost_when_working
    frame["in_work_income_net_of_childcare"] = frame["in_work_income"] - childcare_cost_when_working
    frame["out_of_work_income_net_of_childcare"] = (
        frame["out_of_work_income"] - cost_contingent_support
    )
    frame["gain_to_work"] = (
        frame["in_work_income_net_of_childcare"] - frame["out_of_work_income_net_of_childcare"]
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
    entrant_earnings = impute_entrant_earnings(baseline_sim, year)
    baseline = _net_gain_to_work(
        baseline_sim,
        year,
        baseline_childcare_cost,
        baseline_cost_contingent_support,
        entrant_earnings,
        count_adults,
    )
    reform = _net_gain_to_work(
        reform_sim,
        year,
        reform_childcare_cost,
        reform_cost_contingent_support,
        entrant_earnings,
        count_adults,
    )

    gtw_baseline = baseline["gain_to_work"].to_numpy()
    gtw_reform = reform["gain_to_work"].to_numpy()

    # Percentage change in the gain to work, the OBR framework's driver. Only
    # defined where the baseline gain to work is positive; where working does
    # not pay in the baseline there is no proportional change to scale.
    gtw_pct_change = np.zeros_like(gtw_baseline)
    positive = gtw_baseline > 0
    gtw_pct_change[positive] = (gtw_reform[positive] - gtw_baseline[positive]) / gtw_baseline[
        positive
    ]

    elasticity_wrt_income = calculate_participation_elasticities(
        baseline_sim, potential_earnings_quintile(baseline_sim, year, entrant_earnings)
    )

    # OBR Appendix E: an elasticity with respect to in-work income becomes an
    # elasticity with respect to the gain to work by scaling by
    # (1 - replacement rate).
    in_work = baseline["in_work_income"].to_numpy()
    out_of_work = baseline["out_of_work_income"].to_numpy()
    replacement_rate = np.zeros_like(in_work)
    working_positive = in_work > 0
    replacement_rate[working_positive] = out_of_work[working_positive] / in_work[working_positive]
    replacement_rate = np.clip(replacement_rate, 0, 1)
    elasticity_wrt_gain_to_work = elasticity_wrt_income * (1 - replacement_rate)

    employment_income = np.asarray(baseline_sim.calculate("employment_income", year), float)
    excluded = _excluded(baseline_sim, year, count_adults)
    eligible = ~excluded & responds_to_childcare(baseline_sim, year)
    currently_working = eligible & (employment_income > 0)
    currently_not_working = eligible & (employment_income == 0)

    weights = np.asarray(
        baseline_sim.calculate("household_weight", year, map_to="person").values, float
    )
    imputed_wages = entrant_earnings
    # For someone moving into work the exchequer gains their gross earnings less
    # the rise in their household's net income — income tax and National
    # Insurance paid, plus benefits withdrawn. Measured on the reform's
    # tax-benefit system, so a mover's newly-won childcare entitlements are
    # netted off the gain rather than double-counted.
    reform_gain = reform["in_work_income"].to_numpy() - reform["out_of_work_income"].to_numpy()

    return {
        "gtw_pct_change": gtw_pct_change,
        "elasticity_wrt_gain_to_work": elasticity_wrt_gain_to_work,
        "eligible": eligible,
        "currently_working": currently_working,
        "currently_not_working": currently_not_working,
        "employment_income": employment_income,
        "imputed_wages": imputed_wages,
        "reform_gain": reform_gain,
        "gain_to_work_reform": gtw_reform,
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
    entrants = float(MicroSeries(entry_probability, weights=weights).sum())
    leavers = float(MicroSeries(exit_probability, weights=weights).sum())
    net_entrants = entrants - leavers

    earnings_gained = float(MicroSeries(entry_probability * imputed_wages, weights=weights).sum())
    earnings_lost = float(MicroSeries(exit_probability * employment_income, weights=weights).sum())
    net_earnings = earnings_gained - earnings_lost

    ftes = net_entrants * (HOURS_FOR_NEW_ENTRANTS / FULL_TIME_HOURS)

    revenue_from_entrants = float(
        MicroSeries(entry_probability * (imputed_wages - reform_gain), weights=weights).sum()
    )
    revenue_lost_to_leavers = float(
        MicroSeries(exit_probability * (employment_income - reform_gain), weights=weights).sum()
    )
    net_revenue = revenue_from_entrants - revenue_lost_to_leavers

    # The same response at person level, so it can be allocated to households.
    # Entering work raises household net income by the gain to work; leaving
    # loses it. Expected values, so a person contributes their probability
    # times that gain rather than a drawn outcome.
    expected_net_income_change = (entry_probability - exit_probability) * prepared[
        "gain_to_work_reform"
    ]

    return {
        "expected_net_income_change_per_person": expected_net_income_change,
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
        "responding_adults_m": float(MicroSeries(eligible, weights=weights).sum()) / 1e6,
        "mean_gain_to_work_change_pct": float(
            MicroSeries(gtw_pct_change[eligible], weights=weights[eligible]).mean()
        )
        if float(np.sum(weights[eligible]))
        else 0.0,
    }


def _effective_subsidy_rate(sim, year: int, working: np.ndarray) -> float:
    """Share of childcare costs met by the cost-contingent subsidy, among workers.

    Read from the simulation rather than restated, so it reflects whichever
    scenario is being measured: Tax-Free Childcare's capped top-up in the
    baseline, the flat share under the reform. The Universal Credit childcare
    element is excluded because the reform leaves it unchanged, so it cancels
    out of the *difference* in the gain to work that drives the response.
    """
    expenses = np.asarray(sim.calculate("childcare_expenses", year, map_to="benunit").values, float)
    support = np.asarray(sim.calculate("tax_free_childcare", year, map_to="benunit").values, float)
    benunit_ids = np.asarray(sim.calculate("benunit_id", year).values)
    person_benunit_ids = np.asarray(sim.calculate("benunit_id", year, map_to="person").values)
    working_benunits = pd.Series(working, index=person_benunit_ids).groupby(level=0).max()
    mask = working_benunits.reindex(benunit_ids).fillna(False).to_numpy().astype(bool)
    total = expenses[mask].sum()
    return float(support[mask].sum() / total) if total else 0.0


def childcare_cost_when_working(
    sim,
    year: int,
    responding: np.ndarray,
    actual_cost: np.ndarray,
) -> np.ndarray:
    """Out-of-pocket childcare a person would pay while working.

    For someone already working this is what the model says they pay. For a
    potential entrant it has to be imputed, and without that imputation the
    whole analysis is one-sided.

    The reason is a gap in the upstream framework.
    ``impute_wages_for_nonworkers`` imputes what a non-worker would *earn*, but
    nothing imputes what they would *pay for childcare*, and
    ``childcare_expenses`` is a fixed input recording what they actually spend
    today — which for 85% of eligible non-workers is nothing, because they are
    at home with the child. A subsidy applied to zero is worth zero, so the
    channel by which cheaper childcare draws a parent into work is invisible
    for exactly the people who would move. Left uncorrected the gain-to-work
    model measures the reform's negative work-incentive effect in full and its
    positive one barely at all, and reports a downward-biased net.

    So a potential entrant is assigned the mean childcare spend of *working*
    families whose youngest child is the same age, pro-rated from those
    families' average hours to the entrant's assumed hours. Using observed
    spend among working families as the base means the free hours those
    families already receive are embedded in it, so the entitlement is not
    double-counted.

    The imputed figure is then taken net of the subsidy the scenario would pay
    on it. Workers need no such adjustment: the simulation computes their
    subsidy from their real spending and it is already inside their in-work
    income.
    """
    employment_income = np.asarray(sim.calculate("employment_income", year), float)
    hours = np.asarray(sim.calculate("hours_worked", year).values, float)
    youngest = np.asarray(sim.calculate("youngest_child_age", year, map_to="person").values, float)
    weights = np.asarray(sim.calculate("household_weight", year, map_to="person").values, float)
    working = employment_income > 0

    imputed = np.zeros_like(actual_cost)
    for age in np.unique(youngest[responding & np.isfinite(youngest)]):
        band = youngest == age
        donors = band & working & (hours > 0)
        entrants = band & ~working
        if not donors.any() or not entrants.any():
            continue
        donor_weight = weights[donors]
        mean_cost = float(MicroSeries(actual_cost[donors], weights=donor_weight).mean())
        mean_hours = float(MicroSeries(hours[donors], weights=donor_weight).mean()) / 52
        if mean_hours <= 0:
            continue
        imputed[entrants] = mean_cost * (HOURS_FOR_NEW_ENTRANTS / mean_hours)

    net_of_subsidy = 1 - _effective_subsidy_rate(sim, year, working)
    return np.where(working, actual_cost, imputed * net_of_subsidy)
