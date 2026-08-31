"""Free childcare reform pipeline.

Costs, for 2027, 2028 and 2029, a reform that

* replaces the current split — 15 free hours for 3-4 year olds and 30 free
  hours for under-5s whose parents work and earn under £100k — with 15 hours
  free for every child from 9 months to school age, plus a further 15 hours
  where parents work and earn under £100k; and
* replaces Tax-Free Childcare with a 75% subsidy of childcare costs for all,
  keeping the Universal Credit childcare element.

Each leg is costed on its own and then together, statically and with an
extensive-margin labour supply response. Household effects are reported by
income quintile. Results are written to JSON for the dashboard.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.utils.scenario import Scenario

from . import sources
from .labour_supply import (
    childcare_cost_when_working,
    participation_response,
    prepare,
    price_elasticity_response,
    responds_to_childcare,
)
from .reforms import (
    SUBSIDY_RATE,
    UNIVERSAL_ENTITLEMENT_AGE_MIN,
    displaced_childcare_expenses,
    free_hours_scenario,
    subsidy_scenario,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
# The PolicyEngine UK Enhanced FRS, downloaded from the private release at a
# pinned revision for reproducibility.
DATASET = "enhanced_frs_2024_25.h5"
PRIVATE_REPO = "policyengine/policyengine-uk-data-private"
DATASET_REVISION = "7b0a06f0f08bec4bdb81c5d0fdb4057fe4e7fd1a"
YEARS = [2027, 2028, 2029]
# The parameter changes need to be in force from before the first costed year.
PARAMETER_YEARS = [2026, 2027, 2028, 2029, 2030]


def _dataset() -> UKSingleYearDataset:
    from huggingface_hub import hf_hub_download

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_TOKEN")
    path = hf_hub_download(
        repo_id=PRIVATE_REPO,
        filename=DATASET,
        repo_type="model",
        revision=DATASET_REVISION,
        token=token,
    )
    return UKSingleYearDataset(path)


def _label(level: str) -> str:
    return str(level).replace("_", " ").title().replace(" Of ", " of ")


def _model_parameters(sim, year: int) -> dict:
    """The parameters the simulation applied, read back rather than restated."""
    p = sim.tax_benefit_system.parameters(f"{year}-01-01").gov
    funding_rate = p.dfe.childcare_funding_rate
    return {
        "childcare_funding_rate_gbp_per_hour": {
            f"age_{int(threshold)}_plus": round(float(amount), 3)
            for threshold, amount in zip(funding_rate.thresholds, funding_rate.amounts, strict=True)
        },
        "weeks_per_year": float(p.dfe.weeks_per_year),
        "baseline_universal_entitlement_hours_per_year": float(
            p.dfe.universal_childcare_entitlement.hours
        ),
        "baseline_universal_entitlement_age_min": float(
            p.dfe.universal_childcare_entitlement.age.min
        ),
        "reform_universal_entitlement_age_min": UNIVERSAL_ENTITLEMENT_AGE_MIN,
        "extended_entitlement_income_limit_gbp": float(
            p.dfe.extended_childcare_entitlement.income.limit
        ),
        "extended_entitlement_minimum_weekly_hours": float(
            p.dfe.extended_childcare_entitlement.minimum_weekly_hours
        ),
        "baseline_tax_free_childcare_rate": float(p.hmrc.tax_free_childcare.contribution.rate),
        "baseline_tax_free_childcare_cap_gbp": float(
            p.hmrc.tax_free_childcare.contribution.standard_child
        ),
        "reform_subsidy_rate": SUBSIDY_RATE,
        "uc_childcare_coverage_rate": float(
            p.dwp.universal_credit.elements.childcare.coverage_rate
        ),
    }


def _person_from_benunit(sim, year: int, benunit_values: np.ndarray) -> np.ndarray:
    benunit_ids = np.asarray(sim.calculate("benunit_id", year).values)
    person_benunit_ids = np.asarray(sim.calculate("benunit_id", year, map_to="person").values)
    lookup = pd.Series(benunit_values, index=benunit_ids)
    return np.asarray(lookup.reindex(person_benunit_ids).to_numpy(), float)


def _benunit_variable_per_person(sim, year: int, variable: str) -> np.ndarray:
    """A benefit-unit total, projected onto every member of the benefit unit."""
    return _person_from_benunit(
        sim, year, np.asarray(sim.calculate(variable, year, map_to="benunit").values, float)
    )


def _childcare_cost_per_person(sim, year: int) -> np.ndarray:
    """Benefit-unit childcare spend, borne by each of its adults.

    ``childcare_expenses`` sits on the child, but the cost of working falls on
    the adults, so it is summed within the benefit unit and projected back.
    """
    return _benunit_variable_per_person(sim, year, "childcare_expenses")


def _quintile(sim, year: int, entity: str = "household") -> np.ndarray:
    decile = np.asarray(sim.calculate("household_income_decile", year, map_to=entity).values, float)
    # Quintiles fold PolicyEngine's published household income deciles. Deciles
    # below 1 are the model's marker for households it does not rank.
    return np.where(decile >= 1, np.clip(((decile - 1) // 2 + 1).astype(int), 1, 5), 0)


def _household_effects(baseline_sim, reform_sim, year: int) -> dict:
    """Change in household net income, by income quintile and by family type."""
    baseline_income = np.asarray(baseline_sim.calculate("household_net_income", year).values, float)
    reform_income = np.asarray(reform_sim.calculate("household_net_income", year).values, float)
    weights = np.asarray(baseline_sim.calculate("household_weight", year).values, float)
    quintile = _quintile(baseline_sim, year)
    # family_type is a benefit-unit enum and youngest_child_age a benefit-unit
    # number, so neither maps straight to the household: policyengine-core would
    # try to average them. Both are read at person level, where the mapping is a
    # projection, and then collapsed onto the household — the first benefit
    # unit's family type, and the youngest child across the whole household.
    household_ids = np.asarray(baseline_sim.calculate("household_id", year).values)
    person_household_ids = np.asarray(
        baseline_sim.calculate("household_id", year, map_to="person").values
    )
    person_frame = pd.DataFrame(
        {
            "household_id": person_household_ids,
            "family_type": np.asarray(
                baseline_sim.calculate("family_type", year, map_to="person").values
            ).astype(str),
            "youngest_child_age": np.asarray(
                baseline_sim.calculate("youngest_child_age", year, map_to="person").values,
                float,
            ),
        }
    )
    collapsed = (
        person_frame.groupby("household_id")
        .agg(
            family_type=("family_type", "first"),
            youngest_child_age=("youngest_child_age", "min"),
        )
        .reindex(household_ids)
    )
    family_type = collapsed["family_type"].to_numpy().astype(str)
    has_young_child = collapsed["youngest_child_age"].to_numpy() <= 4

    frame = pd.DataFrame(
        {
            "gain": reform_income - baseline_income,
            "baseline_income": baseline_income,
            "weight": weights,
            "quintile": quintile,
            "family_type": [_label(f) for f in family_type],
            "has_young_child": has_young_child,
        }
    )

    def summarise(group: pd.DataFrame) -> dict:
        weight = group["weight"].sum()
        gaining = group[group["gain"] > 1]
        return {
            "households_m": round(float(weight) / 1e6, 3),
            "total_gain_bn": round(float((group["gain"] * group["weight"]).sum()) / 1e9, 4),
            "average_gain_gbp": round(
                float((group["gain"] * group["weight"]).sum() / weight) if weight else 0.0, 2
            ),
            "average_gain_gbp_among_gainers": round(
                float((gaining["gain"] * gaining["weight"]).sum() / gaining["weight"].sum())
                if gaining["weight"].sum()
                else 0.0,
                2,
            ),
            "share_gaining": round(float(gaining["weight"].sum() / weight) if weight else 0.0, 4),
            "average_gain_pct_of_income": round(
                float(
                    (group["gain"] * group["weight"]).sum()
                    / (group["baseline_income"] * group["weight"]).sum()
                    * 100
                )
                if (group["baseline_income"] * group["weight"]).sum()
                else 0.0,
                4,
            ),
        }

    ranked = frame[frame["quintile"] > 0]
    by_quintile = [
        {"group": f"Q{q}", **summarise(group)} for q, group in ranked.groupby("quintile")
    ]
    families = frame[frame["has_young_child"]]
    by_quintile_with_children = [
        {"group": f"Q{q}", **summarise(group)}
        for q, group in families[families["quintile"] > 0].groupby("quintile")
    ]
    # "Couple no children" survives the has_young_child filter for a handful of
    # weighted households — an artefact of family type and child presence being
    # recorded on different entities — and contributes 0.002m households and
    # nothing to the gain. Reporting a row of zeroes invites the reader to
    # wonder what it means, so it is dropped rather than shown.
    by_family_type = sorted(
        (
            {"group": name, **summarise(group)}
            for name, group in families.groupby("family_type")
            if summarise(group)["total_gain_bn"] > 0
        ),
        key=lambda row: row["average_gain_gbp"],
        reverse=True,
    )
    return {
        "by_income_quintile": by_quintile,
        "by_income_quintile_families_with_under_5s": by_quintile_with_children,
        "by_family_type_families_with_under_5s": by_family_type,
        "all_households": {"group": "All", **summarise(frame)},
        "families_with_under_5s": {"group": "Families with a child under 5", **summarise(families)},
    }


def _spending(sim, year: int) -> dict:
    # The four programmes policyengine-uk counts in gov_spending. The UC
    # childcare element is deliberately not among them: uc_childcare_element is
    # the childcare element of the UC *maximum amount*, before the earnings
    # taper reduces the award, so it is an entitlement component rather than
    # spending. It is reported separately below and never added to a total.
    programs = [
        "universal_childcare_entitlement",
        "extended_childcare_entitlement",
        "targeted_childcare_entitlement",
        "tax_free_childcare",
    ]
    out = {
        program: round(float(sim.calculate(program, year).sum()) / 1e9, 4) for program in programs
    }
    out["total_childcare_support_bn"] = round(sum(out.values()), 4)
    out["uc_childcare_element_maximum_bn"] = round(
        float(sim.calculate("uc_childcare_element", year).sum()) / 1e9, 4
    )
    out["gov_spending_bn"] = round(float(sim.calculate("gov_spending", year).sum()) / 1e9, 3)
    out["childcare_expenses_bn"] = round(
        float(sim.calculate("childcare_expenses", year).sum()) / 1e9, 4
    )
    return out


def _baseline_programmes(sim, year: int) -> list[dict]:
    """Each childcare programme's modelled baseline against its published figure.

    Spending and caseload side by side, because the two answer different
    questions: whether the model pays the right amount, and whether it covers
    the right children. Tax-Free Childcare showed why that matters — it was
    close on caseload while paying nearly double, so a caseload-only check
    would have passed it.

    Every official figure predates the costed years, and the periods differ by
    programme. The ratios are indicative rather than a calibration check, and
    each row carries the period it is drawn from.
    """
    rows = []
    for programme in sources.BASELINE_PROGRAMMES:
        compare_year = programme["comparison_year"]
        # Costed-year values, for context: this is the baseline the reform is
        # measured against.
        costed_spending = round(
            float(sim.calculate(programme["spending_variable"], year).sum()) / 1e9, 4
        )
        costed_caseload = round(float(sim.calculate(programme["caseload_variable"], year).sum()))
        # Comparison-year values, evaluated at the year the published figure
        # covers. Ratios are taken here and nowhere else.
        model_spending = round(
            float(sim.calculate(programme["spending_variable"], compare_year).sum()) / 1e9,
            4,
        )
        model_caseload = round(
            float(sim.calculate(programme["caseload_variable"], compare_year).sum())
        )
        official_spending = programme["official_spending_bn"]
        official_caseload = programme["official_caseload"]
        rows.append(
            {
                "programme": programme["programme"],
                "label": programme["label"],
                "costed_year": year,
                "costed_year_spending_bn": costed_spending,
                "costed_year_caseload": costed_caseload,
                "comparison_year": compare_year,
                "model_spending_bn": model_spending,
                "official_spending_bn": official_spending,
                "official_spending_label": programme["official_spending_label"],
                "spending_ratio": (
                    round(model_spending / official_spending, 3) if official_spending else None
                ),
                "model_caseload": model_caseload,
                "official_caseload": official_caseload,
                "official_caseload_label": programme["official_caseload_label"],
                "caseload_ratio": (
                    round(model_caseload / official_caseload, 3) if official_caseload else None
                ),
                "period": programme["period"],
                "geography": programme["geography"],
                "url": programme["url"],
                "note": programme["note"],
            }
        )
    return rows


UC_CHILDCARE_COMPARISON_YEAR = 2024
# The abolition counterfactual needs the parameter changed from before the
# year it is measured at, so this runs wider than PARAMETER_YEARS.
UC_COUNTERFACTUAL_YEARS = [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]


def _uc_childcare_fiscal_cost(dataset, baseline, year: int) -> dict:
    """What the UC childcare element actually costs, by abolishing it.

    `uc_childcare_element` is a component of the UC *maximum amount*, before
    the earnings taper. Reporting its sum as spending gives £8.69bn against
    DWP's £611m outturn — a 14x gap that is an artefact of comparing an
    entitlement component with an outturn, not a model error.

    The comparable quantity is the counterfactual: set the coverage rate to
    zero and measure the change in government spending. Most of the face
    value never reaches a household, because the taper would have withdrawn
    it anyway.
    """
    abolished = _build(
        dataset,
        scenario=Scenario(
            parameter_changes={
                "gov.dwp.universal_credit.elements.childcare.coverage_rate": {
                    parameter_year: 0 for parameter_year in UC_COUNTERFACTUAL_YEARS
                }
            }
        ),
    )
    # Measured at the year DWP's outturn covers, not the costed year. A 2027
    # figure against a 2024-25 outturn would measure three years of caseload
    # growth as much as it measures the model.
    compare = UC_CHILDCARE_COMPARISON_YEAR
    uc_baseline = baseline.calculate("universal_credit", compare)
    lost = uc_baseline - abolished.calculate("universal_credit", compare)
    losing = lost > 1
    receiving = round(float(losing.sum()))
    return {
        "comparison_year": compare,
        "fiscal_cost_bn": round(
            (
                float(baseline.calculate("gov_spending", compare).sum())
                - float(abolished.calculate("gov_spending", compare).sum())
            )
            / 1e9,
            4,
        ),
        "maximum_amount_component_bn": round(
            float(baseline.calculate("uc_childcare_element", compare).sum()) / 1e9, 4
        ),
        "benefit_units_receiving": receiving,
        "average_monthly_award_gbp": (
            round(float(lost[losing].sum()) / receiving / 12) if receiving else None
        ),
        "costed_year": year,
        "costed_year_fiscal_cost_bn": round(
            (
                float(baseline.calculate("gov_spending", year).sum())
                - float(abolished.calculate("gov_spending", year).sum())
            )
            / 1e9,
            4,
        ),
    }


def _benchmark_comparison(sim, year: int, measures: dict | None = None) -> list[dict]:
    """The model's baseline against published outturns.

    Nothing here feeds the estimate. Where the model and the outturn disagree
    the reason is stated, because two of the gaps — Tax-Free Childcare take-up
    and the size of the childcare fee base — change how the subsidy leg's cost
    should be read.
    """
    rows = []
    for benchmark in sources.BENCHMARKS:
        restriction = benchmark.get("model_restriction")
        if restriction == "england_under_5":
            # The CMA benchmark covers England and the under-5s only. Comparing
            # it against the model's UK all-ages aggregate would count school-age
            # wraparound and holiday childcare — a separate market the benchmark
            # excludes — and the devolved nations, and would overstate the gap.
            ours = _childcare_expenses_slice(sim, year, england_only=True, under_5=True) / 1e9
        elif benchmark.get("model_measure"):
            # Some rows cannot be measured by summing a variable. The UC
            # childcare element is one: its variable is a maximum-amount
            # component, so the comparable figure is what abolishing it costs.
            ours = (measures or {})[benchmark["model_measure"]]["fiscal_cost_bn"]
        else:
            ours = (
                sum(
                    float(sim.calculate(variable, year).sum())
                    for variable in benchmark["model_variables"]
                )
                / 1e9
            )
        row = {key: value for key, value in benchmark.items() if key != "model_variables"}
        row["model_bn"] = round(ours, 3)
        row["model_variables"] = ", ".join(benchmark["model_variables"])
        if benchmark.get("model_measure"):
            row["model_variables"] = "abolition counterfactual on gov_spending"
        row["ratio_model_to_official"] = (
            round(ours / benchmark["official_bn"], 2) if benchmark.get("official_bn") else None
        )
        rows.append(row)
    return rows


def _childcare_expenses_slice(sim, year: int, england_only: bool, under_5: bool) -> float:
    """Weighted childcare spending, optionally restricted to England or under-5s."""
    spending = sim.calculate("childcare_expenses", year)
    values = np.asarray(spending.values, float)
    weights = np.asarray(spending.weights, float)
    mask = np.ones(len(values), bool)
    if england_only:
        country = np.asarray(sim.calculate("country", year, map_to="person").values).astype(str)
        mask &= country == "ENGLAND"
    if under_5:
        mask &= np.asarray(sim.calculate("age", year).values, float) < 5
    return float((values * weights * mask).sum())


def _new_free_hours_value(baseline_sim, free_hours_sim, year: int) -> np.ndarray:
    """Person-level value of free hours the reform newly grants."""
    baseline = np.asarray(
        baseline_sim.calculate("universal_childcare_entitlement", year).values, float
    )
    reform = np.asarray(
        free_hours_sim.calculate("universal_childcare_entitlement", year).values, float
    )
    return np.maximum(reform - baseline, 0)


def _build(dataset, scenario=None, childcare_expenses=None, year=None):
    sim = Microsimulation(dataset=dataset, scenario=scenario)
    if childcare_expenses is not None:
        sim.set_input("childcare_expenses", year, childcare_expenses)
        sim.reset_calculations()
    return sim


def run_year(dataset, year: int) -> dict:
    print(f"  {year}: baseline ...")
    baseline = _build(dataset)

    print(f"  {year}: leg 1 — 15 free hours for all from 9 months ...")
    free_hours = _build(dataset, scenario=free_hours_scenario(PARAMETER_YEARS))

    print(f"  {year}: leg 2 — 75% childcare subsidy replacing Tax-Free Childcare ...")
    subsidy = _build(dataset, scenario=subsidy_scenario())

    # Both legs together. childcare_expenses is out-of-pocket spend net of the
    # free hours a family already receives, so the hours the reform newly makes
    # free are netted out of it before the 75% subsidy applies — otherwise the
    # same hour of care is paid for twice. Only the additional share of new free
    # hours displaces paid care; the rest is care that would not otherwise have
    # been bought.
    print(f"  {year}: both legs, with free hours displacing paid care ...")
    baseline_expenses = np.asarray(baseline.calculate("childcare_expenses", year).values, float)
    displaced_expenses = displaced_childcare_expenses(
        baseline_expenses,
        _new_free_hours_value(baseline, free_hours, year),
        sources.FREE_HOURS_DISPLACEMENT,
    )
    combined = _build(
        dataset,
        scenario=free_hours_scenario(PARAMETER_YEARS) + subsidy_scenario(),
        childcare_expenses=displaced_expenses,
        year=year,
    )

    baseline_spending = _spending(baseline, year)
    print(f"  {year}: UC childcare element, abolition counterfactual ...")
    uc_childcare = _uc_childcare_fiscal_cost(dataset, baseline, year)
    legs = {}
    for name, sim, label in [
        ("free_hours", free_hours, "15 free hours for all from 9 months"),
        ("subsidy", subsidy, "75% childcare subsidy replacing Tax-Free Childcare"),
        ("combined", combined, "Both legs together"),
    ]:
        spending = _spending(sim, year)
        legs[name] = {
            "label": label,
            "spending": spending,
            "static_cost_bn": round(
                spending["gov_spending_bn"] - baseline_spending["gov_spending_bn"], 3
            ),
            "household_effects": _household_effects(baseline, sim, year),
        }

    print(f"  {year}: extensive-margin labour supply response ...")
    # Childcare support that only arises because the family is paying for care:
    # Tax-Free Childcare in the baseline, the 75% subsidy under the reform. It
    # is netted out of out-of-work income, where no care is being bought. The
    # free-hours entitlements are not — those are genuinely available whether or
    # not the parent works, which is part of what the reform does.
    # A potential entrant's childcare cost has to be imputed: the model records
    # what they spend today, which for most eligible non-workers is nothing, so
    # a subsidy applied to it would be worth nothing and the reform's positive
    # work-incentive channel would be invisible for exactly the people who
    # might move. See childcare_cost_when_working.
    responding = responds_to_childcare(baseline, year)

    def _responses_against(reform_sim) -> dict:
        """Participation response of one reform against the baseline.

        Run per leg as well as for both together, because a reader choosing a
        labour supply assumption expects the cost of the thing they are looking
        at to move. The legs pull in opposite directions — free hours remove a
        work condition, the subsidy cuts the price of working — so the response
        to each is not the response to both, and neither is a share of it.
        """
        prepared = prepare(
            baseline,
            reform_sim,
            year,
            childcare_cost_when_working(
                baseline, year, responding, _childcare_cost_per_person(baseline, year)
            ),
            childcare_cost_when_working(
                reform_sim, year, responding, _childcare_cost_per_person(reform_sim, year)
            ),
            _benunit_variable_per_person(baseline, year, "tax_free_childcare"),
            _benunit_variable_per_person(reform_sim, year, "tax_free_childcare"),
        )
        return {
            bound: {
                key: (round(value, 4) if isinstance(value, float) else value)
                for key, value in participation_response(
                    prepared, elasticity_scale=scale
                ).items()
            }
            for bound, scale in [
                ("central", sources.ELASTICITY_SCALE_CENTRAL),
                ("low", sources.ELASTICITY_SCALE_LOW),
                ("high", sources.ELASTICITY_SCALE_HIGH),
            ]
        }

    responses = _responses_against(combined)
    for name, sim in (("free_hours", free_hours), ("subsidy", subsidy)):
        leg_responses = _responses_against(sim)
        legs[name]["labour_supply"] = leg_responses
        legs[name]["dynamic_cost"] = {
            bound: {
                "static_cost_bn": legs[name]["static_cost_bn"],
                "labour_supply_offset_bn": round(response["net_revenue_gbp"] / 1e9, 4),
                "dynamic_cost_bn": round(
                    legs[name]["static_cost_bn"] - response["net_revenue_gbp"] / 1e9, 3
                ),
                "net_entrants": round(response["net_entrants"]),
                "net_ftes": round(response["net_ftes"]),
            }
            for bound, response in leg_responses.items()
        }

    # Independent cross-check on the participation result, using the childcare
    # price elasticity directly rather than the whole tax-benefit system.
    price_check = {
        bound: price_elasticity_response(baseline, combined, year, elasticity)
        for bound, elasticity in [
            ("central", sources.PRICE_ELASTICITY_CENTRAL),
            ("low", sources.PRICE_ELASTICITY_LOW),
            ("high", sources.PRICE_ELASTICITY_HIGH),
        ]
    }

    # Fee-base sensitivity. The subsidy leg is a flat share of childcare
    # spending, so its cost is linear in the spending base. The model's
    # childcare_expenses aggregate is well above the fee base implied by the
    # CMA's estimate of England's early years sector income, so this restates
    # the subsidy leg on that smaller base. It is a scaling of the headline
    # result, not a re-run, and it is reported as a sensitivity rather than
    # substituted for the model's own answer.
    fee_base = next(
        row
        for row in _benchmark_comparison(baseline, year, {"uc_childcare_fiscal_cost": uc_childcare})
        if row.get("model_restriction") == "england_under_5"
    )
    # Only the under-5 slice has a benchmark, so only it is rebased. School-age
    # wraparound and holiday childcare — about a third of the base — is left
    # alone, because no published aggregate exists to rebase it against.
    # Rebasing the whole base on an under-5 England benchmark would be the same
    # mistake in reverse.
    slice_ratio = fee_base["official_bn"] / fee_base["model_bn"] if fee_base["model_bn"] else 1.0
    total_base = float(baseline.calculate("childcare_expenses", year).sum()) / 1e9
    under_5_base = _childcare_expenses_slice(baseline, year, False, True) / 1e9
    rebased_base = under_5_base * slice_ratio + (total_base - under_5_base)
    fee_base_ratio = rebased_base / total_base if total_base else 1.0
    subsidy_only_cost = legs["combined"]["static_cost_bn"] - legs["free_hours"]["static_cost_bn"]
    fee_base_sensitivity = {
        "model_childcare_expenses_bn": round(total_base, 3),
        "model_under_5_bn": round(under_5_base, 3),
        "model_england_under_5_bn": fee_base["model_bn"],
        "benchmark_england_under_5_bn": fee_base["official_bn"],
        "under_5_slice_ratio": round(slice_ratio, 3),
        "rebased_childcare_expenses_bn": round(rebased_base, 3),
        "ratio": round(fee_base_ratio, 3),
        "subsidy_cost_bn": round(legs["subsidy"]["static_cost_bn"] * fee_base_ratio, 3),
        "combined_cost_bn": round(
            legs["free_hours"]["static_cost_bn"] + subsidy_only_cost * fee_base_ratio, 3
        ),
        "note": (
            "Only the under-5 slice is rebased, on the England benchmark of "
            "about £5.1bn of parent-paid fees; the school-age third of the base "
            "is left as modelled because nothing is published to rebase it "
            "against. The benchmark is gross of Tax-Free Childcare and the UC "
            "childcare element, matching childcare_expenses, which both are "
            "computed from. The CMA flags substantial uncertainty in the "
            "sector-income figure this derives from. Treat this as a lower bound "
            "on the subsidy leg, as the headline is an upper bound."
        ),
    }

    static_cost = legs["combined"]["static_cost_bn"]
    dynamic = {}
    for bound, response in responses.items():
        offset_bn = response["net_revenue_gbp"] / 1e9
        dynamic[bound] = {
            "static_cost_bn": static_cost,
            "labour_supply_offset_bn": round(offset_bn, 3),
            "dynamic_cost_bn": round(static_cost - offset_bn, 3),
            "offset_share_of_static_cost": round(offset_bn / static_cost, 4)
            if static_cost
            else 0.0,
            "net_entrants": round(response["net_entrants"]),
            "net_ftes": round(response["net_ftes"]),
        }

    return {
        "year": year,
        "baseline_spending": baseline_spending,
        "baseline_programmes": _baseline_programmes(baseline, year),
        "uc_childcare_fiscal_cost": uc_childcare,
        "benchmarks": _benchmark_comparison(
            baseline, year, {"uc_childcare_fiscal_cost": uc_childcare}
        ),
        "legs": legs,
        "labour_supply": responses,
        "price_elasticity_cross_check": price_check,
        "fee_base_sensitivity": fee_base_sensitivity,
        "dynamic_cost": dynamic,
        "model_parameters": _model_parameters(baseline, year),
    }


def run(args: argparse.Namespace) -> None:
    years = args.years or YEARS
    print(f"Step 1: Loading {DATASET} at revision {DATASET_REVISION[:8]} ...")
    dataset = _dataset()

    print("Step 2: Costing each year ...")
    by_year = {str(year): run_year(dataset, year) for year in years}

    print("Step 3: Writing results JSON ...")
    output = {
        "years": years,
        "currency": "GBP",
        "dataset": "PolicyEngine UK Enhanced FRS (enhanced_frs_2024_25)",
        "dataset_revision": DATASET_REVISION,
        "policyengine_uk_version": importlib.metadata.version("policyengine-uk"),
        "policyengine_version": importlib.metadata.version("policyengine"),
        "reform_definition": {
            "free_hours": (
                "15 hours a week of free childcare for every child from 9 months to "
                "school age, plus a further 15 hours where parents work and earn "
                "under £100,000 — replacing 30 hours for working parents under "
                "£100,000 and 15 hours for 3-4 year olds."
            ),
            "subsidy": (
                "A 75% subsidy of childcare costs for all, replacing Tax-Free "
                "Childcare's 25% top-up on parental spend capped at £2,000 a child. "
                "The Universal Credit childcare element is kept unchanged."
            ),
        },
        **sources.as_json(by_year[str(years[0])]["model_parameters"]),
        "by_year": by_year,
    }

    for destination in [
        REPO_ROOT / "data" / "free_childcare_reform_results.json",
        REPO_ROOT / "dashboard" / "public" / "data" / "free_childcare_reform_results.json",
    ]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(output, indent=2, default=str))
        print(f"    wrote {destination}")

    for year in years:
        result = by_year[str(year)]
        print(
            f"Done {year}: static £{result['legs']['combined']['static_cost_bn']:.2f}bn, "
            f"dynamic £{result['dynamic_cost']['central']['dynamic_cost_bn']:.2f}bn "
            f"({result['dynamic_cost']['central']['net_entrants']:,} net entrants)."
        )
