"""The reform legs, expressed against policyengine-uk 2.148.

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
   eligibility and amount formulas are overridden for two things: the 9-month
   floor is applied from the date of birth, term by term, and the exclusion
   described in ``_universal_excludes_targeted`` is added.

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
            standalone_claim = person.benunit("would_claim_universal_childcare", period)
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


def free_hours_scenario(years: list[int]) -> Scenario:
    """15 free hours from 9 months for all children, keeping the 30-hour tier."""
    return Scenario(
        parameter_changes={
            "gov.dfe.universal_childcare_entitlement.age.min": {
                year: UNIVERSAL_ENTITLEMENT_AGE_MIN for year in years
            }
        },
        simulation_modifier=_no_stacking_modifier,
    )


def _no_stacking_modifier(simulation) -> None:
    for variable in _universal_excludes_targeted():
        simulation.tax_benefit_system.update_variable(variable)
    simulation.reset_calculations()


def _subsidy_variables(rate: float, include_uc_families: bool, take_up_flag: str):
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
            # A flat share of costs, uncapped — not TFC's rate/(1-rate) top-up
            # on parental spend, and not restricted to four declaration periods.
            return expenses * is_qualifying_child * rate

    return tax_free_childcare_eligible, tax_free_childcare


def subsidy_scenario(
    rate: float = SUBSIDY_RATE,
    include_uc_families: bool = SUBSIDY_INCLUDES_UC_FAMILIES,
    take_up_flag: str = SUBSIDY_TAKE_UP_FLAG,
) -> Scenario:
    """Replace Tax-Free Childcare with a flat ``rate`` subsidy of childcare costs.

    ``take_up_flag`` names the benefit-unit take-up input the subsidy is
    defined for; see ``SUBSIDY_TAKE_UP_FLAG``.
    """
    eligible_variable, amount_variable = _subsidy_variables(rate, include_uc_families, take_up_flag)

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


def combined_scenario(years: list[int]) -> Scenario:
    """Both legs at once, without the displacement adjustment.

    The pipeline applies displacement separately, so that the adjustment is
    visible as its own line rather than buried inside a scenario.
    """
    return free_hours_scenario(years) + subsidy_scenario()
