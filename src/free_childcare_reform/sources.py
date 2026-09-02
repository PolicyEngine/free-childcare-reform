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

# Additionality of a free-hours expansion: of the free hours a family is newly
# offered, how much is care it was not already getting.
#
# 54 additional hours per 570 offered — about 9.5% additionality, 90%
# displacement. From IFS Briefing Note BN189 (2016): "when 3-year-olds become
# entitled to 570 hours a year of free care, they only spend an additional 54
# hours per year in childcare provided outside the immediate family". The
# peer-reviewed successor (Brewer, Cattan, Crawford and Rabe, Labour Economics
# 2022, and IFS WP20/09) corroborates it at about 57 hours per 570 on the
# comparable basis, though not significantly.
#
# An earlier version of this file used the same note's other figure — 163
# hours per 570, 29% additionality — which is the estimate for *subsidisable*
# care, a category that includes state-run infant and primary schools. On any
# care outside the family the figure is 54, because most of the difference is
# substitution out of informal care rather than out of paid care. The larger
# number also describes the part-time offer, and the note says the full-time
# offer's additional hours are smaller still.
#
# There is no single well-supported number here: displacement is roughly
# 70-90% measured on formal hours and 90-100% on total care hours. The choice
# matters less than that range suggests, because displacement is separately
# capped at what a family actually spends and that cap binds for most
# newly-eligible families, who are not working and buy little paid care.
# Running the whole analysis at 71% instead of 90% moves the combined cost by
# £0.03bn, or 0.4%, and moves neither leg on its own.
FREE_HOURS_ADDITIONALITY = 54 / 570  # ~0.095
FREE_HOURS_DISPLACEMENT = 1 - FREE_HOURS_ADDITIONALITY  # ~0.905

# Childcare price elasticity of maternal employment, extensive margin. Used for
# the low and high bounds on the participation response, by scaling the OBR
# elasticities in the same ratio.
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

# Childcare price elasticity of hours worked, for parents already in work.
#
# Derived from Brewer, Cattan, Crawford and Rabe (IFS WP20/09): full-time
# eligibility raised mothers' usual weekly hours by +0.600 (Table A.3, panel
# B, column 1, s.e. 0.264, file page 41) against a sample mean of 14.319 hours
# (Table 1, file page 17),
# a +4.19% change, taken against a 100% fall in the childcare price:
# 0.0419 / -1 = -0.042. Proposed for this analysis by Max Mosley.
#
# Two caveats that travel with the number. First, the +0.600 is measured on
# all mothers with zeros for non-workers, and 14.319 is that same all-mothers
# mean, so it is a total-hours effect — extensive and intensive together, not
# an intensive effect for those in work. The paper's own +3.5pp employment
# effect at typical part-time hours accounts for most of it, so this
# component overlaps with the participation response reported alongside it
# and the two should not be read as additive. Second, the +0.600 is the
# effect of full-time eligibility (school hours, 30-35 a week) relative to the
# part-time offer (12.5-15 a week) — a move of roughly 15-20 free hours a
# week in term time, not a 100% price fall — so as a per-unit-price
# elasticity this is a floor (treatment: file pages 8-9).
HOURS_PRICE_ELASTICITY = -0.042

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
#
# ASSUMPTION, not a published figure. There is no literature value for a
# numerical guard of this kind; 0.5 is chosen as a round bound that admits
# large but not implausible responses. It binds for 0.11% of the eligible
# population on the 2027-28 run, so the results are not sensitive to it — but
# it is a choice, not a citation.
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
#  * Tax-Free Childcare. On the like-for-like comparison — same year, and
#    children against children — the model pays £0.625bn at 2024 against
#    HMRC's £632.2m, 0.99x, on 1,099,437 children against 1,085,020, 1.01x.
#    The average award is £569 against £583.
#
#    This was 2.06x until Enhanced FRS 1.57.2 corrected the routed-spend proxy
#    (policyengine-uk-data #473) and the calibration targets (#472, #474).
#
#    An earlier version of this file reported a 1.28x caseload gap and a 0.87x
#    award and concluded the residual was a caseload problem. Both figures
#    were artefacts of the comparison: they set the model's 2027 benefit units
#    against HMRC's 2025-26 *families*. HMRC publishes 868,095 families and
#    1,085,020 children for the same outturn, so dividing a benefit-unit count
#    by a family count is not a caseload ratio, and the three-year gap adds
#    caseload growth on top. There is no residual to explain.
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
# Both bear on how the subsidy leg should be read; neither makes its cost a
# bound in either direction.
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
        "official_bn": 0.6322,
        "official_label": "HMRC £632.2m top-ups to 1,085,020 children in 825,950 families, UK, 2024-25",
        "geography": "UK",
        "period": "2024-25",
        "comparison_year": 2024,
        "kind": "Like-for-like",
        "note": (
            "Model £0.625bn against HMRC's £632.2m at 2024 — 0.99x — on "
            "1,099,437 children against 1,085,020, 1.01x. The average award is "
            "£569 against £583. That is the like-for-like comparison: same "
            "year, and children against children."
            "\n\n"
            "An earlier version of this file reported a 1.28x caseload gap and "
            "a 0.87x award, which was wrong on both counts. It set the model's "
            "2027 benefit units against HMRC's 2025-26 *families*, mixing the "
            "entity and the year. HMRC publishes both counts for the same "
            "outturn — 825,950 families and 1,085,020 children in 2024-25 — "
            "so a model "
            "benefit-unit count divided by a family count is not a caseload "
            "ratio, and comparing across three years adds the caseload growth "
            "on top."
            "\n\n"
            "The gap was 2.06x before the routed-spend correction in "
            "policyengine-uk-data #473 and the calibration targets in #472 and "
            "#474, all of which ship in Enhanced FRS 1.57.2. The release "
            "check now measures 0.989x on spending and 1.013x on child "
            "caseload."
        ),
        "url": "https://www.gov.uk/government/statistics/tax-free-childcare-statistics-june-2025",
    },
    {
        "measure": "Universal Credit childcare element",
        "model_variables": ["uc_childcare_element"],
        "model_measure": "uc_childcare_fiscal_cost",
        "official_bn": 0.611,
        "official_label": "DWP £611m, Great Britain, 2024-25 (a modelled element split of a measured UC total)",
        "geography": "Great Britain",
        "period": "2024-25",
        "kind": "Caseload gap",
        "note": (
            "Measured by abolishing it: the change in government spending when "
            "the 85% coverage rate is set to zero, at 2024 to match the "
            "published year. Summing uc_childcare_element instead gives "
            "£7.95bn, because it is a component of the UC maximum amount "
            "before the earnings taper — most of that face value never reaches "
            "a household."
            "\n\n"
            "Neither side is exact. DWP's £611m is a modelled split of a "
            "measured UC total: the workbook says element breakdowns are 'an "
            "estimate designed to be consistent with the OBR's Economic and "
            "Fiscal Outlook, although other credible breakdowns could be "
            "reached'. DWP's own caseload statistics do not reconcile with it "
            "either — 164,000 households at £400 a month implies about £790m."
            "\n\n"
            "The gap that remains is caseload: the model has about 427,000 "
            "benefit units gaining from the element against DWP's 164,000 to "
            "177,000 households, while paying a lower average award. Nothing "
            "in policyengine-uk-data targets UC elements and there is no "
            "element-specific take-up variable, unlike the four childcare "
            "schemes — see policyengine-uk-data#466. It does not affect this "
            "reform, which leaves the element unchanged."
        ),
        "url": "https://www.gov.uk/government/statistics/universal-credit-quarterly-statistics-29-april-2013-to-14-may-2026/universal-credit-childcare-element-statistics-to-may-2026",
    },
    {
        "measure": "Non-entitlement provider income, England, under-5s",
        "model_variables": ["childcare_expenses"],
        "model_restriction": "england_under_5",
        "official_bn": 5.10,
        "official_label": "~£5.1bn residual, England, under-5s, 2025-26 — provider income less entitlement funding, which is parent fees *and other sources*",
        "geography": "England",
        "period": "2025-26",
        "kind": "Fee base check",
        "note": (
            "Derived, not published: the CMA estimates England's early years "
            "sector income at about £14bn in 2025-26, of which £8.9bn is funded "
            "entitlements, leaving about £5.1bn that parents pay providers. "
            "Both terms are the CMA's: the entitlements row above "
            "uses the IFS's £8.7bn for the same quantity, and mixing the two "
            "sources inside one subtraction would make the residual an artefact "
            "of the mismatch. On the IFS figure the residual would be £5.3bn "
            "and the gap 1.20x rather than 1.25x. "
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
        "url": "https://explore-education-statistics.service.gov.uk/find-statistics/education-provision-children-under-5",
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
            "central estimate — the government's own labour supply assumption, "
            "and a cost anchor. Outturn ran above it: take-up 26% above the "
            "December 2023 estimate by March 2025, spending about 28% above "
            "budget in 2024-25."
        ),
        "url": "https://www.gov.uk/government/publications/spring-budget-2023",
    },
    {
        "proposal": "Nordic-style universal childcare, 40 hours, 6 months to school age",
        "source": "Women's Budget Group (De Henau)",
        "date": "2017 costing",
        "cost_bn": "33-55 gross, 1.7-6.1 net",
        "geography": "UK",
        "note": (
            "40 hours a week, 48 weeks a year, from 6 months — an upper bound. "
            "The net range is small because WBG puts tax and benefit recoupment "
            "at 89-95% of gross. Gross and net are both from the 2017 costing; "
            "the 2020 Budget representation's £38-57bn gross range is not used, "
            "as pairing it with the 2017 net range would mix vintages."
        ),
        "url": "https://www.wbg.org.uk/publication/costing-funding-childcare/",
    },
]


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

IFS_FREE_CHILDCARE = Source(
    "Brewer, Cattan, Crawford and Rabe — Does more free childcare help parents work more?",
    "England, 2005-2013. Regression discontinuity. Moving from 15 to 30-35 hours "
    "raised maternal participation 5.7pp and employment 3.5pp — about 12,000 more "
    "mothers a year — only where the youngest child was eligible. For every 570 free "
    "hours offered, only about 163 extra hours of subsidisable care were used.",
    "https://www.iser.essex.ac.uk/wp-content/uploads/files/misoc/reports/BN189%20free%20childcare.pdf",
)

AKGUNDUZ_PLANTENGA = Source(
    "Akgunduz and Plantenga — Child care prices and maternal employment: a meta-analysis",
    "International meta-analysis, 43 estimates from 36 studies. Mean childcare "
    "price elasticity of maternal employment -0.277; Europe and Canada -0.19 against "
    "the US -0.35. Elasticities are smaller in high part-time countries like the UK, "
    "though that result holds only when sample year is excluded from the regression.",
    "https://www.uu.nl/sites/default/files/rebo_use_dp_2015_15-14.pdf",
)

BAKER_GRUBER_MILLIGAN = Source(
    "Baker, Gruber and Milligan — Universal child care, maternal labor supply and family well-being",
    "Quebec, Canada. $5-a-day childcare raised married maternal participation "
    "7.7pp, an implied cost elasticity of 0.236 the authors call low-end. Quebec "
    "offered up to 10 hours a day; England's entitlements are term-time and "
    "school-day, the main reason cited for weaker UK results.",
    "https://www.nber.org/system/files/working_papers/w11832/w11832.pdf",
)

DFE_30_HOURS_EVALUATION = Source(
    "DfE — Evaluation of the national rollout of 30 hours free childcare",
    "England. Self-reported survey, not causal. Since starting the extended hours, "
    "2% of mothers entered work and 26% raised their hours, against under 1% and 7% "
    "of fathers; reported impact was far higher for lower-income mothers (56% "
    "against 29%).",
    "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/740168/Evaluation_of_national_rollout_of_30_hours_free-childcare.pdf",
)

DFE_CHILDCARE_EXPERIENCES = Source(
    "DfE — Expansion to early childcare entitlements: childcare experiences survey",
    "England. The 2024-25 under-3s expansion has no causal evaluation yet. In the "
    "pilot wave 13% increased hours and 7% decreased, 78% unchanged. Self-reported, "
    "unweighted, 17% response rate.",
    "https://explore-education-statistics.service.gov.uk/find-statistics/expansion-to-early-childcare-entitlements-childcare-experiences-survey/2024-25-autumn-term",
)

DE_HENAU = Source(
    "De Henau — Simulating employment and fiscal effects of universal childcare in the UK",
    "UK. UKMOD microsimulation with input-output multipliers: gross cost £26.6bn to "
    "£49.4bn a year, 61-72% recouped. Used here only as a ceiling — the employment "
    "response is assumed rather than estimated, part-time mothers are forced to "
    "full-time, and labour demand is assumed to absorb the supply in full.",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8853244/",
)

OBR_LABOUR_SUPPLY = Source(
    "OBR — The impact of a NICs cut on labour supply",
    "UK. The participation elasticities used here, by gender, partner employment, "
    "age of youngest child and earnings quintile, and the Appendix E conversion to "
    "an elasticity with respect to the gain to work. Shipped in policyengine-uk as "
    "policyengine_uk.dynamics.participation.",
    "https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf",
)

BETTENDORF_JONGEN_MULLER = Source(
    "Bettendorf, Jongen and Muller — Childcare subsidies and labour supply",
    "Netherlands, CPB. A joint reform — childcare subsidies plus an earned income "
    "tax credit — raised maternal hours 6.2% against employment 3.0%, so the "
    "intensive margin moved about twice as much. Cited only for that ratio, which "
    "is why the participation-only estimate here is a floor: the two instruments "
    "are not separately identified, so neither level is transferable.",
    "https://home.treasury.gov/system/files/136/The-Economics-of-Childcare-Supply-09-14-final.pdf",
)

BREWER_HOURS = Source(
    "Brewer, Cattan, Crawford and Rabe — Does more free childcare help parents work more? (IFS WP20/09)",
    "England. Table A.3 (file page 41): full-time eligibility raised mothers' usual "
    "weekly hours by 0.600 (s.e. 0.264), measured over all mothers with zeros for "
    "non-workers, against the Table 1 (file page 17) sample mean of 14.319 hours. "
    "The -0.042 hours elasticity used here is that +4.19% taken against a 100% "
    "price fall; the treatment was full-time eligibility (30-35 hours a week) "
    "relative to the part-time offer (12.5-15), file pages 8-9, not a 100% price "
    "fall. It is a total-hours effect that contains the participation "
    "channel, so it overlaps with the extensive-margin result.",
    "https://ifs.org.uk/sites/default/files/output_url_files/WP202009-Does-more-free-childcare-help-parents-work-more.pdf#page=41",
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
            "hours_price_elasticity": HOURS_PRICE_ELASTICITY,
            "restrict_to_youngest_child_eligible": RESTRICT_TO_YOUNGEST_CHILD_ELIGIBLE,
            "margin": (
                "extensive (participation) and intensive (hours among parents in work); "
                "the hours elasticity is a total-hours effect, so the two overlap"
            ),
            "incidence": (
                "Free hours are valued at the DfE funding rate the model applies; "
                "the subsidy is valued at its cash value to the family."
            ),
        },
        "comparable_costings": COMPARABLE_COSTINGS,
        "sources": {
            "ifs_free_childcare": asdict(IFS_FREE_CHILDCARE),
            "brewer_hours": asdict(BREWER_HOURS),
            "akgunduz_plantenga": asdict(AKGUNDUZ_PLANTENGA),
            "baker_gruber_milligan": asdict(BAKER_GRUBER_MILLIGAN),
            "dfe_30_hours_evaluation": asdict(DFE_30_HOURS_EVALUATION),
            "dfe_childcare_experiences": asdict(DFE_CHILDCARE_EXPERIENCES),
            "de_henau": asdict(DE_HENAU),
            "obr_labour_supply": asdict(OBR_LABOUR_SUPPLY),
            "bettendorf_jongen_muller": asdict(BETTENDORF_JONGEN_MULLER),
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
        "official_spending_bn": 1.7,
        "official_spending_label": "£1.7bn, England, 2024-25, from the dedicated schools grant early years block allocations",
        "official_caseload": 416_537,
        "official_caseload_label": "DfE, January 2024: 778,327 registered excluding reception, less 361,790 on the working-parent entitlement",
        "period": "January 2024",
        "comparison_year": 2024,
        "geography": "England",
        "spending_url": "https://skillsfunding.service.gov.uk/view-latest-funding/national-funding-allocations/DSG/2024-to-2025",
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
        "official_spending_bn": 2.5,
        "official_spending_label": "£2.5bn, England, 2024-25, from the dedicated schools grant early years block allocations",
        "official_caseload": 621_500,
        "official_caseload_label": "DfE, January 2025: 379,000 three- and four-year-olds plus 242,500 two-year-olds",
        "period": "January 2025",
        "comparison_year": 2024,
        "geography": "England",
        "spending_url": "https://skillsfunding.service.gov.uk/view-latest-funding/national-funding-allocations/DSG/2024-to-2025",
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
