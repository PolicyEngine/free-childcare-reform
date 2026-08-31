"""The three reform legs, expressed against policyengine-uk 2.92.

The reform has two independent parts, which the pipeline also runs separately
so their costs can be attributed:

1. **Free hours.** Replace the current split — 15 free hours for 3-4 year olds
   regardless of work, 30 free hours for under-5s whose parents work and earn
   under £100k — with 15 hours free for *every* child from 9 months to school
   age, plus a further 15 hours for children whose parents work and earn under
   £100k.

   In the model this is a single parameter change. The three DfE schemes are
   modelled as mutually exclusive rather than stacking:
   ``universal_childcare_entitlement_eligible`` already carries no work or
   income test and ends with ``& ~has_extended_childcare``, while
   ``extended_childcare_entitlement`` pays the full 30 hours to working
   families under £100k. So the reform's second tier (30 hours for working
   families under £100k) is already exactly what the extended scheme delivers,
   and the first tier is delivered by widening the universal scheme's age band
   from 3 down to 9 months. No formula change is needed, and none is made.

2. **Childcare subsidy.** Replace Tax-Free Childcare with a 75% subsidy of
   childcare costs for all. This *is* structural. TFC's formula is a top-up on
   parental spend, ``expense * rate / (1 - rate)``, capped at £2,000 per child
   and gated on both a work condition and a £100k adjusted-net-income cliff.
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
)
from policyengine_uk.utils.scenario import Scenario

# 15 hours a week from 9 months, for every child, regardless of parental work
# or income. 0.75 is the age floor in years the extended (working-parent)
# scheme already uses, so the two tiers line up on the same age band.
UNIVERSAL_ENTITLEMENT_AGE_MIN = 0.75
# The subsidy that replaces Tax-Free Childcare: 75% of childcare costs, with no
# work test, no £100k cliff and no per-child cap.
SUBSIDY_RATE = 0.75
# Whether the 75% subsidy also reaches families on UC or tax credits, who
# already receive 85% of costs through the UC childcare element. Off by
# default: the reform brief keeps the UC childcare element, and stacking would
# subsidise childcare above cost.
SUBSIDY_INCLUDES_UC_FAMILIES = False


def _universal_excludes_targeted():
    """Stop the widened universal entitlement stacking on the 2-year-old offer.

    policyengine-uk models the DfE schemes as mutually exclusive, but the
    exclusions were written for a system where universal started at age 3:
    `targeted_childcare_entitlement_eligible` excludes extended-eligible
    families and nothing else, because a 2-year-old could not previously hold
    the universal entitlement.

    Widening the age floor to 0.75 breaks that assumption. Without this, a
    non-working family on qualifying benefits with a 2-year-old draws 570
    hours from the targeted offer *and* 570 from the universal one — 30 free
    hours a week where the reform gives 15. That is 35,252 children and
    £0.18bn on the pinned dataset.

    The targeted offer is left in place and the universal entitlement steps
    aside, rather than the other way round: the disadvantaged offer is funded
    at the 2-year-old rate (£8.28 an hour against £5.88), so keeping it is
    both the larger entitlement and the existing policy.
    """

    class universal_childcare_entitlement_eligible(Variable):
        value_type = bool
        entity = Person
        label = "eligible for universal childcare entitlement"
        definition_period = YEAR
        defined_for = "would_claim_universal_childcare"

        def formula(person, period, parameters):
            # policyengine-uk's own formula, with one term added. It cannot be
            # delegated to, because overriding a variable and then reading it
            # is circular.
            country = person.household("country", period)
            in_england = country == country.possible_values.ENGLAND
            age = person("age", period)
            p = parameters(period).gov.dfe.universal_childcare_entitlement
            meets_age_condition = (age >= p.age.min) & (age < p.age.max)
            not_compulsory_age = ~person("is_of_compulsory_school_age", period)
            has_extended_childcare = person.benunit(
                "extended_childcare_entitlement_eligible", period
            )
            # The added term. The targeted offer is benefit-unit eligibility on
            # a 2-year-old, so it only displaces the universal entitlement for
            # a child of that age.
            targeted = person.benunit(
                "targeted_childcare_entitlement_eligible", period
            )
            targeted_p = parameters(period).gov.dfe.targeted_childcare_entitlement
            in_targeted_age = targeted_p.age_eligibility.calc(age) > 0
            return (
                in_england
                & meets_age_condition
                & not_compulsory_age
                & ~has_extended_childcare
                & ~(targeted & in_targeted_age)
            )

    return universal_childcare_entitlement_eligible


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
    simulation.tax_benefit_system.update_variable(_universal_excludes_targeted())
    simulation.reset_calculations()


def _subsidy_variables(rate: float, include_uc_families: bool):
    class tax_free_childcare_eligible(Variable):
        value_type = bool
        entity = BenUnit
        label = "eligibility for the universal childcare subsidy"
        definition_period = YEAR
        defined_for = "would_claim_tfc"

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
) -> Scenario:
    """Replace Tax-Free Childcare with a flat ``rate`` subsidy of childcare costs."""
    eligible_variable, amount_variable = _subsidy_variables(rate, include_uc_families)

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
