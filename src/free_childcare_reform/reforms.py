"""The reform legs, expressed against policyengine-uk 2.153.

The reform has two independent parts, which the pipeline also runs separately
so their costs can be attributed:

1. **Free hours.** Replace the current split — 15 free hours for 3-4 year olds
   regardless of work, 30 free hours for under-5s whose parents work and earn
   under £100k — with 15 hours free for *every* child from 9 months to school
   age, plus a further 15 hours for children whose parents work and earn under
   £100k.

   In the model this is a parameter change plus one exclusion. policyengine-uk
   stacks the universal hours under the working-parent hours rather than
   treating the schemes as alternatives: ``universal_childcare_entitlement_eligible``
   carries no work or income test, and ``extended_childcare_entitlement_per_child``
   pays the working-parent total *less* the universal and targeted hours the
   child already gets. So the reform's second tier (30 hours for working
   families under £100k) is already what the working-parent scheme delivers,
   and the first tier is delivered by widening the universal scheme's age band
   from 3 down to 9 months. A working family's total is unchanged; its first 15
   hours move from the working-parent line to the universal one. The universal
   eligibility and amount formulas are overridden for three things: the 9-month
   floor is applied from the date of birth, term by term, the exclusion
   described in ``_universal_excludes_targeted`` is added, and take-up of the
   newly covered under-3 hours is read from ``free_hours_new_claim`` rather
   than the universal flag (see ``NEW_HOURS_TAKE_UP``).

2. **Childcare subsidy.** Replace Tax-Free Childcare with a 75% subsidy of
   childcare costs for all. This *is* structural. TFC's formula pays 20% of
   the gross spend routed through the account — ``expense * eligible_fraction
   * tax_free_childcare_spend_routed_share * rate``, the statutory 25% top-up
   on deposits — capped at £2,000 per child, and is gated on both a work
   condition and a £100k adjusted-net-income cliff.
   A "75% subsidy of costs" is a different functional form, so
   ``tax_free_childcare`` and ``tax_free_childcare_eligible`` are replaced.

   The Universal Credit childcare element is kept, per the reform brief. TFC's
   existing disqualification of UC and tax-credit recipients is therefore also
   kept: those families already receive 85% of costs through UC, and stacking
   a further 75% on the same spend would subsidise childcare above its price.
   ``SUBSIDY_INCLUDES_UC_FAMILIES`` runs the alternative for comparison.

The pipeline also runs both legs together. When it does, it applies a
displacement adjustment (see ``displaced_childcare_expenses``): the model's
``childcare_expenses`` input is documented as out-of-pocket spend *net of* free
hours, so newly-granted free hours must reduce it before the 75% subsidy is
applied, or the same hour of care is paid for twice.
"""

from __future__ import annotations

import numpy as np
from policyengine_uk.model_api import (
    GBP,
    YEAR,
    BenUnit,
    Person,
    Variable,
    max_,
    min_,
    where,
)
from policyengine_uk.utils.dates import add_months_to_yyyymmdd, birth_day, term_starts
from policyengine_uk.utils.scenario import Scenario

# 15 hours a week from 9 months, for every child, regardless of parental work
# or income. 0.75 is the age floor in years the extended (working-parent)
# scheme already uses, so the two tiers line up on the same age band.
#
# The floor is applied from the date of birth, not the whole-year age: a
# child gets universal hours from the first term (1 January, 1 April or
# 1 September) after it reaches 9 months, the same rule the engine uses for the
# working-parent hours (extended_childcare_entitlement_term_share). See
# _term_share_after_minimum_age. On Microcosm a133f37a in 2027-28 the leg's
# new hours by age are £0.40bn at age 0, £1.95bn at age 1 and £1.09bn at age 2,
# for about 155,000, 350,000 and 212,000 children.
UNIVERSAL_ENTITLEMENT_AGE_MIN = 0.75
# The subsidy that replaces Tax-Free Childcare: 75% of childcare costs, with no
# work test, no £100k cliff and no per-child cap.
SUBSIDY_RATE = 0.75
# Whether the 75% subsidy also reaches families on UC or tax credits, who
# already receive 85% of costs through the UC childcare element. Off by
# default: the reform brief keeps the UC childcare element, and stacking would
# subsidise childcare above cost.
SUBSIDY_INCLUDES_UC_FAMILIES = False
# Which take-up flag the subsidy inherits. Both are dataset inputs and
# neither is estimated for this reform. The coded case keeps Tax-Free
# Childcare's, on the argument that the subsidy is administered through the
# same account. The alternative — the extended (30-hour) entitlement's flag,
# proposed on the grounds that the reform drops TFC's restrictions — is costed
# alongside it. On Microcosm a133f37a the TFC flag is the higher of the two
# (0.96 against 0.85 among benefit units with a qualifying child, 2027), so
# the switch lowers the leg rather than raising it.
SUBSIDY_TAKE_UP_FLAG = "would_claim_tfc"
SUBSIDY_TAKE_UP_FLAG_EXTENDED = "would_claim_extended_childcare"

# Take-up of the newly covered hours (children under 3) in families outside
# the working-parent hours. Microcosm draws universal take-up nested under the
# working-parent flag and fits the conditional rate to zero, so every family
# with that flag — about 0.84 of families — takes up universal hours whatever
# its work status. No 15-hour offer for under-3s outside work exists today, so
# the data cannot calibrate that rate, and read off the nested flag 78% of
# 1-year-olds outside the working-parent hours would take the new hours up.
#
# - "central": such families claim on ``would_claim_targeted_childcare``, the
#   flag for the existing 15-hour offer to 2-year-olds outside work (0.655 in
#   the data, against DfE's 65.2% in January 2025).
# - "low": 60% of DfE's January 2026 take-up among *working* families by
#   age — 46% at 9-11 months, 76% at age 1, 92% at age 2 — drawn once per
#   benefit unit with a fixed seed.
# - "high": the dataset's universal flag, as the engine reads it.
#
# Families on the working-parent hours in the baseline keep the universal
# flag in every case, so the working parents who would leave work under the
# reform (the leavers) are unchanged. The flag is set from the baseline run
# and passed in, so the labour supply response cannot move it.
NEW_HOURS_TAKE_UP = "central"
NEW_HOURS_TAKE_UP_CASES = ("low", "central", "high")
NEW_HOURS_LOW_SHARE = 0.6
DFE_WORKING_FAMILY_TAKE_UP_BY_AGE = {0: 0.46, 1: 0.76, 2: 0.92}
NEW_HOURS_LOW_SEED = 20261024
# The universal entitlement's baseline minimum age. Children below it are the
# ones the reform newly covers.
BASELINE_UNIVERSAL_MIN_AGE = 3


def _new_claim_variable(new_claim: dict[int, np.ndarray] | None):
    """Person-level take-up of the newly covered hours, fixed from the baseline.

    ``new_claim`` maps a year to a boolean array over people. Years without an
    entry, or ``None``, fall back to the universal flag, which is the "high"
    case and the engine's own reading.
    """

    class free_hours_new_claim(Variable):
        value_type = bool
        entity = Person
        label = "would take up the reform's newly covered free hours"
        definition_period = YEAR

        def formula(person, period, parameters):
            if new_claim is not None and period.start.year in new_claim:
                return new_claim[period.start.year]
            return person.benunit("would_claim_universal_childcare", period)

    return free_hours_new_claim


def _universal_excludes_targeted():
    """The universal eligibility and amount overrides for the free-hours leg.

    The amount applies the 9-month floor from the date of birth (see
    ``_term_share_after_minimum_age``). The eligibility adds one exclusion:
    the widened universal entitlement must not stack on the 2-year-old offer.

    policyengine-uk stacks the universal hours under the working-parent
    hours, but `targeted_childcare_entitlement_eligible` was written for a
    system where universal started at age 3: a 2-year-old could not
    previously hold both the universal and the targeted entitlement.

    Widening the age floor to 0.75 breaks that assumption. Without this, a
    non-working family on qualifying benefits with a 2-year-old draws 570
    hours from the targeted offer *and* 570 from the universal one — 30 free
    hours a week where the reform gives 15. On Microcosm a133f37a in 2027-28
    that is 47,010 children and £0.19bn on the leg.

    It applies only where the family claims the targeted offer: the engine's
    targeted eligibility is legal eligibility, and a family that does not
    claim it keeps the universal hours.

    The targeted offer is left in place and the universal entitlement steps
    aside, rather than the other way round: both are 15 hours at the same
    age-based funding rate, and the targeted offer is the existing policy.
    """

    class universal_childcare_entitlement_eligible(Variable):
        value_type = bool
        entity = Person
        label = "eligible for universal childcare entitlement"
        definition_period = YEAR

        def formula(person, period, parameters):
            # policyengine-uk's own formula (2.147+, reception term from the
            # date of birth, universal stacking under the working-parent
            # hours), with one term added. It cannot be delegated to, because
            # overriding a variable and then reading it is circular.
            country = person.household("country", period)
            in_england = country == country.possible_values.ENGLAND
            age = person("age", period)
            p = parameters(period).gov.dfe.universal_childcare_entitlement
            # From the term after the child reaches the minimum age, read from
            # the date of birth rather than the whole-year age.
            meets_age_condition = (
                _term_share_after_minimum_age(person, period, parameters) > 0
            ) & (age < p.age.max)
            not_compulsory_age = ~person("is_of_compulsory_school_age", period)
            before_school = person("early_years_term_share_before_school", period)
            # The added term. The targeted offer is benefit-unit eligibility on
            # a 2-year-old, so it only displaces the universal entitlement for
            # a child of that age, and only where the family claims it: the
            # engine's targeted eligibility is legal eligibility, and a family
            # that does not claim the targeted offer keeps the universal hours.
            targeted = person.benunit(
                "targeted_childcare_entitlement_eligible", period
            ) & person.benunit("would_claim_targeted_childcare", period)
            targeted_p = parameters(period).gov.dfe.targeted_childcare_entitlement
            in_targeted_age = targeted_p.age_eligibility.calc(age) > 0
            return (
                in_england
                & meets_age_condition
                & not_compulsory_age
                & (before_school > 0)
                & ~(targeted & in_targeted_age)
            )

    class universal_childcare_entitlement(Variable):
        value_type = float
        entity = Person
        label = "universal childcare entitlement amount per year"
        definition_period = YEAR
        unit = GBP
        defined_for = "universal_childcare_entitlement_eligible"

        def formula(person, period, parameters):
            # policyengine-uk's own formula, with the hours paid only for the
            # terms after the child reaches the minimum age. That share is 1
            # from age 2 on, so only the newly covered under-2s are affected.
            p = parameters(period).gov.dfe
            age = person("age", period)
            hours = p.universal_childcare_entitlement.hours
            total_hours_used = person("max_free_entitlement_hours_used", period) * p.weeks_per_year
            hours_to_use = min_(total_hours_used, hours)
            before_school = person("early_years_term_share_before_school", period)
            base_value = (
                hours_to_use
                * before_school
                * _term_share_after_minimum_age(person, period, parameters)
                * p.childcare_funding_rate.calc(age)
            )
            # Children the baseline already covers claim on the universal
            # flag as before; the newly covered under-3s claim on
            # free_hours_new_claim (see NEW_HOURS_TAKE_UP).
            newly_covered = age < BASELINE_UNIVERSAL_MIN_AGE
            standalone_claim = where(
                newly_covered,
                person("free_hours_new_claim", period),
                person.benunit("would_claim_universal_childcare", period),
            )
            working_parent_total = person("extended_childcare_entitlement_total_per_child", period)
            # base_value already covers only the terms after the minimum age,
            # the same terms as the working-parent hours, so the engine's
            # extra term-share factor is not applied again here.
            participating_value = min_(base_value, working_parent_total)
            return min_(base_value, where(standalone_claim, base_value, participating_value))

    return universal_childcare_entitlement_eligible, universal_childcare_entitlement


def _term_share_after_minimum_age(person, period, parameters):
    """Share of the year's terms that begin after the child reaches the universal minimum age.

    The same rule as the engine's working-parent start
    (``extended_childcare_entitlement_term_share``): hours begin in the first
    term (1 January, 1 April or 1 September) after the day the child reaches
    the minimum age.
    """
    p = parameters(period).gov.dfe.universal_childcare_entitlement
    reaches_minimum_age = add_months_to_yyyymmdd(birth_day(person, period), 12 * p.age.min)
    starts = term_starts(period.start.year)
    return sum(reaches_minimum_age < start for start in starts) / len(starts)


def free_hours_scenario(
    years: list[int], new_claim: dict[int, np.ndarray] | None = None
) -> Scenario:
    """15 free hours from 9 months for all children, keeping the 30-hour tier.

    ``new_claim`` is the take-up of the newly covered hours, from
    ``new_hours_claim``; ``None`` reads the universal flag (the "high" case).
    """

    def modifier(simulation) -> None:
        simulation.tax_benefit_system.update_variable(_new_claim_variable(new_claim))
        for variable in _universal_excludes_targeted():
            simulation.tax_benefit_system.update_variable(variable)
        simulation.reset_calculations()

    return Scenario(
        parameter_changes={
            "gov.dfe.universal_childcare_entitlement.age.min": {
                year: UNIVERSAL_ENTITLEMENT_AGE_MIN for year in years
            }
        },
        simulation_modifier=modifier,
    )


def _array(values, dtype=None) -> np.ndarray:
    """A calculation as a plain array, from a microsimulation or a situation."""
    return np.asarray(getattr(values, "values", values), dtype=dtype)


def on_working_parent_hours(baseline_sim, year: int) -> np.ndarray:
    """Benefit units on the working-parent hours in the baseline, at person level.

    The parent and any partner meet the work condition and the family carries
    the working-parent take-up flag. Read on the family, not the child, so a
    working family whose child is under 9 months still counts.
    """
    work = _array(
        baseline_sim.calculate("extended_childcare_entitlement_work_condition", year), bool
    )
    adult = _array(baseline_sim.calculate("is_claimant_or_partner", year), bool)
    benunit_id = _array(baseline_sim.calculate("benunit_id", year, map_to="person"))
    _, index = np.unique(benunit_id, return_inverse=True)
    adults = np.bincount(index, weights=adult)
    failing = np.bincount(index, weights=adult & ~work)
    meets = (adults > 0) & (failing == 0)
    claims = _array(
        baseline_sim.calculate("would_claim_extended_childcare", year, map_to="person"), bool
    )
    return meets[index] & claims


def new_hours_claim(baseline_sim, year: int, case: str = NEW_HOURS_TAKE_UP) -> np.ndarray:
    """Person-level take-up of the newly covered hours for one ``case``.

    See ``NEW_HOURS_TAKE_UP``. Families on the working-parent hours keep the
    universal flag; only the rest change.
    """
    universal = _array(
        baseline_sim.calculate("would_claim_universal_childcare", year, map_to="person"), bool
    )
    if case == "high":
        return universal
    if case == "central":
        other = _array(
            baseline_sim.calculate("would_claim_targeted_childcare", year, map_to="person"), bool
        )
    elif case == "low":
        age = _array(baseline_sim.calculate("age", year), float)
        rate = np.select(
            [age < 1, age < 2, age < 3],
            [NEW_HOURS_LOW_SHARE * DFE_WORKING_FAMILY_TAKE_UP_BY_AGE[a] for a in (0, 1, 2)],
            default=0.0,
        )
        benunit_id = _array(baseline_sim.calculate("benunit_id", year, map_to="person"))
        ids, index = np.unique(benunit_id, return_inverse=True)
        draw = np.random.default_rng(NEW_HOURS_LOW_SEED + year).random(len(ids))[index]
        other = draw < rate
    else:
        raise ValueError(f"unknown take-up case {case!r}")
    return np.where(on_working_parent_hours(baseline_sim, year), universal, other)


def _subsidy_variables(
    rate: float, include_uc_families: bool, take_up_flag: str, routed_share: bool = False
):
    class tax_free_childcare_eligible(Variable):
        value_type = bool
        entity = BenUnit
        label = "eligibility for the universal childcare subsidy"
        definition_period = YEAR
        defined_for = take_up_flag

        def formula(benunit, period, parameters):
            has_qualifying_child = np.asarray(
                benunit.any(benunit.members("tax_free_childcare_qualifying_child", period))
            ).astype(bool)
            if include_uc_families:
                return has_qualifying_child
            # tax_free_childcare_program_eligible carries the UC/tax-credit
            # disqualification (gov.hmrc.tax_free_childcare.disqualifying_benefits).
            # The work condition and the £100k income cliff are dropped: the
            # subsidy is for all.
            program_eligible = np.asarray(
                benunit("tax_free_childcare_program_eligible", period)
            ).astype(bool)
            return has_qualifying_child & program_eligible

    class tax_free_childcare(Variable):
        value_type = float
        entity = Person
        label = "government contribution through the universal childcare subsidy"
        definition_period = YEAR
        unit = GBP
        defined_for = "tax_free_childcare_eligible"

        def formula(person, period, parameters):
            is_qualifying_child = person("tax_free_childcare_qualifying_child", period)
            expenses = person("childcare_expenses", period) * person(
                "tax_free_childcare_uses_qualifying_provider", period
            )
            if routed_share:
                # Only the spend families route through a Tax-Free Childcare
                # account today: the subsidy at current claiming behaviour.
                expenses = expenses * min_(
                    max_(person("tax_free_childcare_spend_routed_share", period), 0), 1
                )
            # A flat share of costs, uncapped — not TFC's rate/(1-rate) top-up
            # on parental spend, and not restricted to four declaration periods.
            return expenses * is_qualifying_child * rate

    return tax_free_childcare_eligible, tax_free_childcare


def subsidy_scenario(
    rate: float = SUBSIDY_RATE,
    include_uc_families: bool = SUBSIDY_INCLUDES_UC_FAMILIES,
    take_up_flag: str = SUBSIDY_TAKE_UP_FLAG,
    routed_share: bool = False,
) -> Scenario:
    """Replace Tax-Free Childcare with a flat ``rate`` subsidy of childcare costs.

    ``take_up_flag`` names the benefit-unit take-up input the subsidy is
    defined for; see ``SUBSIDY_TAKE_UP_FLAG``. ``routed_share`` pays only on the
    share of spend routed through a Tax-Free Childcare account today
    (``tax_free_childcare_spend_routed_share``), the low end of the leg's range.
    """
    eligible_variable, amount_variable = _subsidy_variables(
        rate, include_uc_families, take_up_flag, routed_share
    )

    def modifier(simulation) -> None:
        simulation.tax_benefit_system.update_variable(eligible_variable)
        simulation.tax_benefit_system.update_variable(amount_variable)
        simulation.reset_calculations()

    return Scenario(simulation_modifier=modifier)


def displaced_childcare_expenses(
    baseline_expenses: np.ndarray,
    new_free_hours_value: np.ndarray,
    displacement_rate: float,
) -> np.ndarray:
    """Out-of-pocket childcare spend after newly-free hours displace paid hours.

    ``childcare_expenses`` in policyengine-uk is out-of-pocket spend net of the
    free hours a family already receives, so hours the reform newly makes free
    have to be netted out of it before any cost-share subsidy is applied.

    Only ``displacement_rate`` of the value of new free hours displaces paid
    care. The rest is additional care that would not otherwise have been bought,
    which is the standard finding in evaluations of the English entitlements:
    a large share of a new free offer is taken up by families already paying
    for that care, but part of it is new demand.
    """
    displaced = new_free_hours_value * displacement_rate
    return max_(baseline_expenses - min_(displaced, baseline_expenses), 0)


def combined_scenario(years: list[int], new_claim: dict[int, np.ndarray] | None = None) -> Scenario:
    """Both legs at once, without the displacement adjustment.

    The pipeline applies displacement separately, so that the adjustment is
    visible as its own line rather than buried inside a scenario.
    """
    return free_hours_scenario(years, new_claim) + subsidy_scenario()
