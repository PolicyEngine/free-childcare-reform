"""Single registry of every non-PolicyEngine number used in the analysis.

Everything PolicyEngine UK models — childcare entitlements, Tax-Free Childcare,
the UC childcare element, childcare expenses, incomes, ages, weights — comes
from the Enhanced FRS at run time. Everything else lives here with a value, a
description and a source URL, and is emitted verbatim into the results JSON so
the dashboard renders no hardcoded numbers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Source:
    label: str
    description: str
    url: str


# ---------------------------------------------------------------------------
# Behavioural assumptions
# ---------------------------------------------------------------------------

# Additionality of a free-hours expansion. Brewer, Cattan, Crawford and Rabe
# (IFS WP20/09, Labour Economics 2022) evaluate England's free entitlements with
# a date-of-birth regression discontinuity and find that for every 570 hours a
# year of free care offered, children spent only about 163 additional hours a
# year in subsidisable care — roughly 29% additionality, 71% displacement of
# care families were already buying. Displacement is what makes a free-hours
# expansion mostly a transfer rather than a change in the price of working, so
# it scales the labour supply channel without changing the fiscal cost.
FREE_HOURS_ADDITIONALITY = 163 / 570  # ~0.286
FREE_HOURS_DISPLACEMENT = 1 - FREE_HOURS_ADDITIONALITY  # ~0.714

# Childcare price elasticity of maternal employment, extensive margin. Used for
# the independent cross-check of the gain-to-work model, not as its input.
# Akgunduz and Plantenga's meta-analysis of 43 estimates gives a mean of -0.277,
# but with a European/Canadian mean of -0.19 against a US mean of -0.35, clear
# publication bias (larger and peer-reviewed samples give smaller estimates),
# and a meta-regression finding significantly smaller elasticities in countries
# with high part-time incidence and mid-to-high female participation — which
# describes the UK. Morrissey's review, as cited by the US Treasury, puts most
# US estimates "on the order of -0.1". Baker, Gruber and Milligan's Quebec
# estimate of -0.236, from the most generous programme ever studied, is
# self-described as low-end. The UK causal evidence is weaker still: Brewer et
# al. find essentially no participation effect from the 15-hour offer and
# +3.5pp in work from a move to 30-35 hours, confined to mothers whose youngest
# child is eligible.
PRICE_ELASTICITY_CENTRAL = -0.15
PRICE_ELASTICITY_LOW = -0.05
PRICE_ELASTICITY_HIGH = -0.30

# Scale applied to the OBR participation elasticities for the low and high
# bounds of the gain-to-work model. Set to the ratio of the low and high price
# elasticities to the central one, so the two methods' uncertainty bands are
# the same width and come from the same evidence.
ELASTICITY_SCALE_CENTRAL = 1.0
ELASTICITY_SCALE_LOW = PRICE_ELASTICITY_LOW / PRICE_ELASTICITY_CENTRAL  # 1/3
ELASTICITY_SCALE_HIGH = PRICE_ELASTICITY_HIGH / PRICE_ELASTICITY_CENTRAL  # 2

# Cap on the modelled proportional change in any one person's probability of
# working. An elasticity applied to a large proportional change in a small
# baseline gain to work can otherwise imply a probability change above one.
PARTICIPATION_CHANGE_BOUND = 0.5

# Brewer et al. find no participation effect for mothers who also have a
# younger, non-eligible child — they still need care for the younger child, so
# the entitlement does not free them to work. This replicates internationally
# and is the single most important structural restriction on the response.
RESTRICT_TO_YOUNGEST_CHILD_ELIGIBLE = True


# ---------------------------------------------------------------------------
# External benchmarks
# ---------------------------------------------------------------------------

# Published figures the model's baseline and reform costs are checked against.
# None of these is an input to the estimate. Two of them matter enough to change
# how the results should be read, and both are flagged in the results JSON:
#
#  * Tax-Free Childcare. The model pays £0.67bn against HMRC's £599.8m
#    outturn — 1.11x. This was 2.06x until the Enhanced FRS release of
#    30 August 2026 (1.57.2), which corrected the routed-spend proxy and the
#    calibration target; policyengine-uk-data's own release check now measures
#    TFC spending at 0.99x its £632.2m target, against 1.87x before.
#
#    The correction also flipped where the residual sits. It used to be
#    entirely the average award — £1,353 against HMRC's £691, with claimants
#    close to right at 1.05x. It is now the other way round: the average award
#    is £600 against £691 (0.87x) and the claimant count is 1.11m against
#    868,095 (1.28x). Part of that is projection rather than error, since the
#    caseload has been growing about 5% a year and these are 2027 figures,
#    but not all of it. The remaining overshoot is a caseload question now,
#    not a fee-base one.
#
#    The comparison has to be annual on both sides. HMRC also publishes a
#    point-in-time monthly count (601,000 families in March 2026); setting an
#    annual model aggregate against that stock rather than the annual flow
#    manufactures a take-up gap that is not there.
#
#  * The childcare fee base. The CMA puts England's early years sector income
#    at about £14bn in 2025-26, of which £8.9bn is funded entitlements. The
#    residual, about £5.1bn, is what parents pay providers for the under-5s.
#
#    That £5.1bn is the comparator, not the £3.5-4bn an earlier version of
#    this file used. The smaller figure came from netting TFC and the UC
#    childcare element off the residual to reach what parents bear after
#    support — but childcare_expenses is the total fee, and both
#    tax_free_childcare and uc_childcare_element are computed *from* it.
#    Subtracting them and then comparing against the variable they derive
#    from double-counts the support. It is the same denominator mistake this
#    file warns about above for TFC stock-versus-flow.
#
#    The benchmark covers England and the under-5s only, so it must be
#    compared against the same slice of the model — not the £11.1bn UK,
#    all-ages aggregate, which also contains school-age wraparound and holiday
#    childcare (a separate market the CMA figure excludes) and the devolved
#    nations. On the comparable basis the model is about 1.25x the benchmark.
#    There is no published aggregate at all for school-age childcare spend, so
#    that part of the base is unbenchmarked in either direction.
#
#    One qualification stays open. The model treats childcare_expenses as the
#    gross fee, which is what makes £5.1bn the internally consistent
#    comparator. Whether the FRS response behind it is truly gross, or already
#    partly net of a TFC top-up, is not established here; if it is partly net
#    the true benchmark sits between £3.75bn and £5.1bn.
#
# Both point the same way: the subsidy leg's headline cost is an upper bound.
# Neither is a defect of this analysis to patch here — see README, "Correcting
# the baseline".
BENCHMARKS = [
    {
        "measure": "Free early years entitlements, total",
        "model_variables": [
            "universal_childcare_entitlement",
            "extended_childcare_entitlement",
            "targeted_childcare_entitlement",
        ],
        "official_bn": 8.7,
        "official_label": "IFS £8.7bn, England, 2025-26 prices",
        "geography": "England",
        "period": "2025-26",
        "kind": "Independent check",
        "url": "https://ifs.org.uk/publications/annual-report-education-spending-england-2025-26",
    },
    {
        "measure": "Disadvantaged 2-year-old offer",
        "model_variables": ["targeted_childcare_entitlement"],
        "official_bn": 0.57,
        "official_label": "IFS £570m, England, 2025-26",
        "geography": "England",
        "period": "2025-26",
        "kind": "Independent check",
        "url": "https://ifs.org.uk/publications/annual-report-education-spending-england-2025-26",
    },
    {
        "measure": "Tax-Free Childcare",
        "model_variables": ["tax_free_childcare"],
        "official_bn": 0.5998,
        "official_label": "HMRC £599.8m top-ups, 868,095 families, UK, 2025-26",
        "geography": "UK",
        "period": "2025-26",
        "kind": "Award gap",
        "note": (
            "Was 2.06x; now 1.11x, after the Enhanced FRS release of 30 August "
            "2026 (1.57.2) corrected the routed-spend proxy and the calibration "
            "target. policyengine-uk-data's own release check measures TFC "
            "spending at 0.99x its £632.2m target, against 1.87x before. The "
            "residual has changed character: the average award is now £600 "
            "against HMRC's £691 (0.87x) while claimants are 1.11m against "
            "868,095 (1.28x), where before the award was 1.96x and claimants "
            "1.05x. Some of the caseload gap is projection — these are 2027 "
            "figures and the caseload grows about 5% a year — but not all. "
            "Both sides must be annual: HMRC's point-in-time count of 601,000 "
            "families in March 2026 is a stock, not the annual flow."
        ),
        "url": "https://www.gov.uk/government/statistics/tax-free-childcare-statistics-march-2026",
    },
    {
        "measure": "Universal Credit childcare element",
        "model_variables": ["uc_childcare_element"],
        "official_bn": 0.61,
        "official_label": "DWP £611m, Great Britain, 2024-25 outturn",
        "geography": "Great Britain",
        "period": "2024-25",
        "kind": "Not comparable",
        "model_measure": "uc_childcare_fiscal_cost",
        "note": (
            "Measured by abolishing it: the change in government spending when "
            "the 85% coverage rate is set to zero. Summing uc_childcare_element "
            "instead gives £8.69bn, because it is a component of the UC maximum "
            "amount before the earnings taper — most of that face value never "
            "reaches a household, so setting it against an outturn produces a "
            "14x gap that is an artefact of the comparison rather than a model "
            "error. The counterfactual is the comparable quantity."
        ),
        "url": "https://www.gov.uk/government/publications/benefit-expenditure-and-caseload-tables-2026",
    },
    {
        "measure": "Parent-paid childcare fees, England, under-5s",
        "model_variables": ["childcare_expenses"],
        "model_restriction": "england_under_5",
        "official_bn": 5.10,
        "official_label": "~£5.1bn implied, England, under-5s, 2025-26",
        "geography": "England",
        "period": "2025-26",
        "kind": "Fee base check",
        "note": (
            "Derived, not published: the CMA estimates England's early years "
            "sector income at about £14bn in 2025-26, of which £8.9bn is funded "
            "entitlements, leaving about £5.1bn that parents pay providers. "
            "That gross figure is the comparator. An earlier version of this "
            "check used £3.75bn, netting TFC and the UC childcare element off "
            "the residual — but childcare_expenses is the total fee and both "
            "of those are computed from it, so subtracting them double-counts "
            "the support and overstated the gap as 1.70x rather than 1.25x. "
            "The CMA flags substantial uncertainty in the £14bn, and the "
            "residual on top of it is arithmetic rather than a published "
            "figure. Compared here against England under-5s only, which is "
            "what the benchmark covers; the model's full UK all-ages aggregate "
            "is shown separately below."
        ),
        "url": "https://assets.publishing.service.gov.uk/media/6a43cd6d065c5aec12a4e3ef/_Statement_of_scope_1_July.pdf",
    },
    {
        "measure": "Childcare spending, all children, UK",
        "model_variables": ["childcare_expenses"],
        "official_bn": None,
        "official_label": "No published aggregate exists",
        "geography": "UK",
        "period": "2027",
        "kind": "Unbenchmarked",
        "note": (
            "The full base the 75% subsidy applies to, since the subsidy reaches "
            "qualifying children up to 12. About two thirds is under-5s, a quarter "
            "school-age wraparound and holiday childcare, and the rest 12-plus. "
            "Only the under-5 England slice has a benchmark; no aggregate of "
            "school-age childcare spend is published by anyone, so that part is "
            "unchecked in either direction."
        ),
        "url": "https://www.gov.uk/government/collections/childcare-and-early-years-statistics",
    },
]

# Comparable published costings of this reform's first leg. NEF's is a direct
# analogue: 15 hours free for all children from 9 months to 4, no work test.
COMPARABLE_COSTINGS = [
    {
        "proposal": "15 hours free for all children 9 months to 4, no work test",
        "source": "New Economics Foundation, with Pregnant Then Screwed and JRF",
        "date": "July 2025",
        "cost_bn": "3.0-3.4 net",
        "geography": "England",
        "note": (
            "The closest published analogue to this reform's free-hours leg. NEF "
            "cost it at roughly cost-neutral at current usage, rising to £3-3.4bn "
            "net at expanded usage, and about 11% lower again once labour supply "
            "is allowed for."
        ),
        "url": "https://neweconomics.org/2025/07/the-universal-family-childcare-promise",
    },
    {
        "proposal": "30 hours for all 3-4 year olds, work test removed",
        "source": "Sutton Trust and IFS (Farquharson), A Fair Start?",
        "date": "August 2021",
        "cost_bn": "0.25 central",
        "geography": "England",
        "note": (
            "Predates the under-3 expansion entirely, so it cannot be scaled to "
            "today's system, but it is the only IFS-authored costing of removing "
            "a work test."
        ),
        "url": "https://www.suttontrust.com/our-research/a-fair-start-equalising-access-to-early-education/",
    },
    {
        "proposal": "The March 2023 expansion to under-3s, as originally costed",
        "source": "HM Treasury and OBR, Spring Budget 2023",
        "date": "March 2023",
        "cost_bn": "4.1 by 2027-28",
        "geography": "England",
        "note": (
            "Costed with about 60,000 entrants to employment by 2027-28, on a "
            "central estimate. (The OBR's 55,000 to 240,000 band is the "
            "uncertainty around the labour supply effect of all Spring Budget "
            "2023 measures, central 110,000 — not around this 60,000.) Useful "
            "both as a cost anchor "
            "and as the government's own labour supply assumption. Outturn ran "
            "above forecast: take-up reported in March 2025 ran 26% above the "
            "December 2023 estimate, and 2024-25 spending about 28% above "
            "budget."
        ),
        "url": "https://www.gov.uk/government/publications/spring-budget-2023",
    },
    {
        "proposal": "Nordic-style universal childcare, 40 hours, 6 months to school age",
        "source": "Women's Budget Group (De Henau)",
        "date": "2020",
        "cost_bn": "38-57 gross, 1.7-6.1 net",
        "geography": "UK",
        "note": (
            "A far larger offer than this reform — 40 hours a week, 48 weeks a "
            "year, from 6 months. Cited only as an upper bound. WBG puts "
            "tax and benefit recoupment at 89-95% of the gross cost, which is "
            "what makes the net range so much smaller. An earlier version of "
            "this file gave the net range as £9-16bn and the gross as £38-55bn; "
            "the first has no published source and the second mixed the 2017 "
            "base with the 2020 update."
        ),
        "url": "https://www.wbg.org.uk/publication/costing-funding-childcare/",
    },
]

# The £100,000 adjusted net income cliff the reform's second tier retains.
INCOME_CLIFF_CONTEXT = {
    "threshold_gbp": 100_000,
    "frozen_since": 2017,
    "inflation_indexed_equivalent_gbp": 137_000,
    "children_affected": "50,500-99,000 in 2025-26",
    "support_forgone_bn": 0.874,
    "note": (
        "DfE estimates released under FOI put 50,500 to 99,000 children in "
        "families above the threshold in 2025-26, with up to £874m of funded "
        "childcare support unavailable to them. A two-child family loses nearly "
        "£30,000 of support on crossing £100,000 and needs about £156,000 of "
        "gross income to restore its disposable income at £99,000. This reform "
        "keeps the cliff for the second 15 hours but removes it from the first, "
        "which cuts the size of the step without abolishing it."
    ),
    "url": "https://www.gov.uk/government/organisations/department-for-education",
}


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

IFS_FREE_CHILDCARE = Source(
    "Brewer, Cattan, Crawford and Rabe — Does more free childcare help parents work more?",
    "Regression-discontinuity evaluation of England's free entitlements, 2005-2013. "
    "The 15-hour part-time offer only marginally affected maternal labour force "
    "participation. Moving to 30-35 hours raised participation by 5.7pp and "
    "employment by 3.5pp, about 12,000 more mothers in work a year, concentrated "
    "in mothers whose youngest child was eligible and with no effect on fathers. "
    "For every 570 free hours offered, children spent only about 163 additional "
    "hours in subsidisable care.",
    "https://ifs.org.uk/sites/default/files/output_url_files/WP202009-Does-more-free-childcare-help-parents-work-more.pdf",
)

AKGUNDUZ_PLANTENGA = Source(
    "Akgunduz and Plantenga — Child care prices and maternal employment: a meta-analysis",
    "43 estimates from 36 studies. Mean childcare price elasticity of maternal "
    "employment -0.277, with a European and Canadian mean of -0.19 against a US "
    "mean of -0.35. Finds publication bias and significantly smaller elasticities "
    "in high part-time, mid-to-high participation countries.",
    "https://www.uu.nl/sites/default/files/rebo_use_dp_2015_15-14.pdf",
)

BAKER_GRUBER_MILLIGAN = Source(
    "Baker, Gruber and Milligan — Universal child care, maternal labor supply and family well-being",
    "Quebec's $5-a-day childcare raised married maternal participation by 7.7pp, "
    "an implied childcare-cost elasticity of 0.236 that the authors call low-end. "
    "About a third of the rise in reported childcare use was women already working "
    "shifting from informal to formal care. Quebec offered up to 10 hours a day; "
    "England's entitlements are school-day and term-time, which is the main reason "
    "cited for the weaker UK results.",
    "https://www.nber.org/system/files/working_papers/w11832/w11832.pdf",
)

DFE_30_HOURS_EVALUATION = Source(
    "DfE — Evaluation of the national rollout of 30 hours free childcare",
    "Survey evidence, self-reported rather than causal. Since starting the extended "
    "hours 2% of mothers entered work and 26% increased their hours, against under "
    "1% and 7% for fathers. Reported positive work impact was much higher for lower "
    "income (56%) than higher income (29%) mothers.",
    "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/740168/Evaluation_of_national_rollout_of_30_hours_free-childcare.pdf",
)

DFE_CHILDCARE_EXPERIENCES = Source(
    "DfE — Expansion to early childcare entitlements: childcare experiences survey",
    "The 2024-25 expansion to under-3s has no causal evaluation yet. In the pilot "
    "wave 13% of respondents increased hours and 7% decreased, with 78% unchanged. "
    "Self-reported, unweighted, 17% response rate.",
    "https://explore-education-statistics.service.gov.uk/find-statistics/expansion-to-early-childcare-entitlements-childcare-experiences-survey/2024-25-autumn-term",
)

DE_HENAU = Source(
    "De Henau — Simulating employment and fiscal effects of universal childcare in the UK",
    "UKMOD microsimulation with input-output multipliers. Gross cost £26.6bn to "
    "£49.4bn a year, with 61-72% recouped. Used here only as a stated ceiling: the "
    "employment response is assumed rather than estimated, part-time mothers are "
    "forced to full-time, labour demand is assumed to accommodate supply in full, "
    "and childcare-sector employment multipliers are counted alongside maternal "
    "labour supply.",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8853244/",
)

OBR_LABOUR_SUPPLY = Source(
    "OBR — The impact of a NICs cut on labour supply",
    "The participation elasticities used here, by gender, partner employment "
    "status, age of youngest child and earnings quintile, and the Appendix E "
    "conversion of an elasticity with respect to in-work income into one with "
    "respect to the gain to work. Shipped in policyengine-uk as "
    "policyengine_uk.dynamics.participation.",
    "https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf",
)

BETTENDORF_JONGEN_MULLER = Source(
    "Bettendorf, Jongen and Muller — Childcare subsidies and labour supply",
    "A Dutch reform roughly halving out-of-pocket childcare costs raised maternal "
    "hours by 6.2% against employment by 3.0%, so the intensive margin moved about "
    "twice as much as the extensive margin. Cited here as the reason the "
    "participation-only estimate is a floor on the total labour supply response.",
    "https://home.treasury.gov/system/files/136/The-Economics-of-Childcare-Supply-09-14-final.pdf",
)

POLICYENGINE_UK = Source(
    "PolicyEngine UK",
    "The open-source microsimulation model and the Enhanced FRS dataset used for "
    "every baseline and reform quantity in this analysis.",
    "https://github.com/PolicyEngine/policyengine-uk",
)


def as_json(model_parameters: dict[str, Any]) -> dict:
    """Registry as emitted to the results JSON.

    ``model_parameters`` is read from the simulation at run time (funding rates,
    weeks per year, entitlement hours, income limits) rather than duplicated
    here, so the dashboard displays what the simulation actually applied.
    """
    return {
        "model_parameters": model_parameters,
        "assumptions": {
            "free_hours_additionality": round(FREE_HOURS_ADDITIONALITY, 4),
            "free_hours_displacement": round(FREE_HOURS_DISPLACEMENT, 4),
            "price_elasticity_central": PRICE_ELASTICITY_CENTRAL,
            "price_elasticity_low": PRICE_ELASTICITY_LOW,
            "price_elasticity_high": PRICE_ELASTICITY_HIGH,
            "elasticity_scale_low": round(ELASTICITY_SCALE_LOW, 4),
            "elasticity_scale_high": round(ELASTICITY_SCALE_HIGH, 4),
            "participation_change_bound": PARTICIPATION_CHANGE_BOUND,
            "restrict_to_youngest_child_eligible": RESTRICT_TO_YOUNGEST_CHILD_ELIGIBLE,
            "margin": "extensive (participation) only; the intensive margin is not modelled",
            "incidence": (
                "Free hours are valued at the DfE funding rate the model applies; "
                "the subsidy is valued at its cash value to the family."
            ),
        },
        "comparable_costings": COMPARABLE_COSTINGS,
        "income_cliff_context": INCOME_CLIFF_CONTEXT,
        "sources": {
            "ifs_free_childcare": asdict(IFS_FREE_CHILDCARE),
            "akgunduz_plantenga": asdict(AKGUNDUZ_PLANTENGA),
            "baker_gruber_milligan": asdict(BAKER_GRUBER_MILLIGAN),
            "dfe_30_hours_evaluation": asdict(DFE_30_HOURS_EVALUATION),
            "dfe_childcare_experiences": asdict(DFE_CHILDCARE_EXPERIENCES),
            "de_henau": asdict(DE_HENAU),
            "obr_labour_supply": asdict(OBR_LABOUR_SUPPLY),
            "bettendorf_jongen_muller": asdict(BETTENDORF_JONGEN_MULLER),
            "policyengine_uk": asdict(POLICYENGINE_UK),
        },
    }


# Per-programme baseline check: what the model pays and how many children it
# covers, against the published figure for each scheme.
#
# The caseload targets are the ones policyengine-uk-data calibrates the
# Enhanced FRS against, corrected in its #472 and #474 and shipping in release
# 1.57.2. Citing them here keeps this analysis and the data build on the same
# published figures rather than two sets that can drift apart.
#
# Every official figure predates the costed years, so each row carries the
# model year it should be compared at and the ratio is taken there, not at
# 2027. That matters most for the working-parent entitlement: comparing the
# 2027 model against the January 2025 census gives 1.61x, but the scheme
# expanded to 30 hours for under-threes in September 2025, so most of that is
# the rollout rather than an error. At 2025 the same comparison is far closer.
# The model's 2027 value is still reported, because that is the baseline the
# reform is costed against — but it is labelled as such and not divided by an
# older published figure.
BASELINE_PROGRAMMES = [
    {
        "programme": "universal",
        "label": "Universal entitlement (15 hours, 3-4 year olds)",
        "spending_variable": "universal_childcare_entitlement",
        "caseload_variable": "is_child_receiving_universal_childcare",
        "official_spending_bn": None,
        "official_spending_label": "Not published separately; DfE reports one £8.7bn England total for all three entitlements (IFS, 2025-26 prices)",
        "shares_official_spending_with": ["extended", "targeted"],
        "official_caseload": 416_537,
        "official_caseload_label": "DfE, January 2024: 778,327 registered excluding reception, less 361,790 on the working-parent entitlement",
        "period": "January 2024",
        "comparison_year": 2024,
        "geography": "England",
        "url": "https://explore-education-statistics.service.gov.uk/find-statistics/funded-early-education-and-childcare/2026",
        "note": (
            "The comparator nets off the working-parent entitlement because "
            "policyengine-uk models the two as mutually exclusive: "
            "universal_childcare_entitlement_eligible ends with "
            "& ~has_extended_childcare. The headline 1.13 million is not the "
            "right figure to compare against."
        ),
    },
    {
        "programme": "extended",
        "label": "Working-parent entitlement (30 hours, under £100k)",
        "spending_variable": "extended_childcare_entitlement",
        "caseload_variable": "is_child_receiving_extended_childcare",
        "official_spending_bn": None,
        "official_spending_label": "Not published separately; DfE reports one £8.7bn England total for all three entitlements (IFS, 2025-26 prices)",
        "shares_official_spending_with": ["universal", "targeted"],
        "official_caseload": 621_500,
        "official_caseload_label": "DfE, January 2025: 379,000 three- and four-year-olds plus 242,500 two-year-olds",
        "period": "January 2025",
        "comparison_year": 2024,
        "geography": "England",
        "url": "https://explore-education-statistics.service.gov.uk/find-statistics/funded-early-education-and-childcare/2025",
        "note": (
            "The census is January 2025 but the model is read at 2024, which is "
            "the basis policyengine-uk-data calibrates on. January 2024 cannot "
            "serve this scheme — the two-year-old offer only began in April "
            "2024, so that census misses half of it — while the model's own "
            "2025 already contains the September 2025 expansion to 30 hours for "
            "under-threes, which the January 2025 census predates. Reading the "
            "model at 2025 against this figure gives 1.61x, almost all of it "
            "that expansion. The mixed basis is a known limitation rather than "
            "a solved problem. DfE also warns that some two-year-olds eligible "
            "for both this and the disadvantaged offer were recorded here "
            "contrary to guidance, which moves children between this row and "
            "the next."
        ),
    },
    {
        "programme": "targeted",
        "label": "Disadvantaged two-year-old offer",
        "spending_variable": "targeted_childcare_entitlement",
        "caseload_variable": "is_child_receiving_targeted_childcare",
        "official_spending_bn": 0.57,
        "official_spending_label": "IFS £570m, England, 2025-26",
        "official_caseload": 115_852,
        "official_caseload_label": "DfE, January 2024: 115,852 registered",
        "period": "January 2024 (caseload), 2025-26 (spending)",
        "comparison_year": 2024,
        "geography": "England",
        "url": "https://ifs.org.uk/publications/annual-report-education-spending-england-2025-26",
        "note": (
            "Registrations have been falling year on year as the working-parent "
            "entitlement absorbs families who would previously have taken this "
            "offer, so the direction of travel is downward."
        ),
    },
    {
        "programme": "tfc",
        "label": "Tax-Free Childcare",
        "spending_variable": "tax_free_childcare",
        "caseload_variable": "is_child_receiving_tax_free_childcare",
        "official_spending_bn": 0.6322,
        "official_spending_label": "HMRC £632.2m top-up, 2024-25",
        "official_caseload": 1_085_020,
        "official_caseload_label": "HMRC, 2024-25: 1,085,020 children with used accounts",
        "period": "2024-25",
        "comparison_year": 2024,
        "geography": "UK",
        "url": "https://www.gov.uk/government/statistics/tax-free-childcare-statistics-june-2025",
        "note": (
            "Both sides annual. HMRC also publishes a point-in-time monthly "
            "count; comparing an annual model aggregate against that stock "
            "manufactures a gap that is not there. This is the only programme "
            "here whose spending the Enhanced FRS is directly calibrated on, at "
            "0.99x its target on release 1.57.2."
        ),
    },
]
