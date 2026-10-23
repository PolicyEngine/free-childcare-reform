# Two childcare reforms: free hours and a 75% subsidy

Costing of a two-part childcare reform for the UK, fiscal years 2027-28 to 2029-30, on Microcosm UK 2024-25 with policyengine-uk — static and with a labour supply response on both margins: participation, and hours among parents in work.

**Dashboard: https://free-childcare-reform.vercel.app/uk/free-childcare-reform**

## The reform

**Leg 1 — free hours.** Replace the current split (30 free hours for under-5s whose parents work and earn under £100,000; 15 hours for 3-4 year olds regardless) with **15 hours free for every child from 9 months to school age**, plus **a further 15 hours** where parents work and earn under £100,000.

**Leg 2 — childcare subsidy.** Replace Tax-Free Childcare (a 25% top-up on parental spend, capped at £2,000 a child, gated on work and a £100,000 income cliff) with a **75% subsidy of childcare costs for all**. The Universal Credit childcare element is kept unchanged at 85%.

## Headline results

Each leg costed against the current system, on Microcosm UK 2024-25:

| Fiscal year | Free hours | 75% subsidy |
| --- | --- | --- |
| 2027-28 | £3.45bn | £5.55bn |
| 2028-29 | £3.47bn | £5.67bn |
| 2029-30 | £3.54bn | £5.81bn |

**The two legs are reported separately and should not be added.** Free hours displace paid care, so running both at once shrinks the base the 75% subsidy applies to. Both together cost £8.56bn in 2027-28, not the £8.99bn the columns suggest.

Two numbers describe displacement and they are not alternatives. **90%** is the assumed share of a new free offer that replaces care a family was already getting. **20%** is what actually happens in the run, because displacement is separately capped at what a family spends, and that cap binds: many newly-eligible families are not working and buy little paid care, so modelled childcare spending falls by £0.69bn against £3.45bn of new free hours. Running the parameter at 71% instead raises the combined cost by £0.08bn.

**The childcare fee base is a large uncertainty for the subsidy leg, but the rebasing is an illustrative scenario rather than a bound.** For the free-hours leg, two uncertainties are comparable: the split of new hours between age 0 and age 1, which may move on the first Microcosm release to include its under-2 age fix (a12885f9; see *What moved*), and the gap between the model and official figures for the universal entitlement, at £2.66bn of modelled spending against £1.70bn and 1.09m children against 0.78m (see *The modelled baseline against published figures*). The subsidy pays a share of what families spend, and for England's under-5s the model has £7.13bn of fees against about £5.10bn implied by the CMA — **1.40×**. Scaling the model's under-5 fees to that figure takes the subsidy leg to £4.40bn and both legs to £7.50bn.

Do not read £7.50bn as a lower bound. The CMA does not publish £5.1bn as gross parent-paid fees: it is a residual of an uncertain £14bn sector-income estimate less £8.9bn of entitlement funding, and that residual contains other provider income too. The comparison also sets a 2025-26 residual against 2027-28 nominal fees. Scenarios in the other direction exceed the headline. Each is a combined run with free hours displacing paid care, not standalone legs added together, which would overstate every scenario: full take-up within the coded scope gives £8.71bn, including Universal Credit families gives £10.14bn, and doing both gives £10.31bn. Treat £7.50bn as one fixed-quantity accounting scenario among several, not the end of an interval.

**The labour supply response is small and, on the central assumption, slightly negative in heads.** Free hours give **−18,544** net entrants — making 15 hours unconditional removes a reason to work — while the subsidy gives **+9,083**, because cheaper childcare raises the gain to work. Together, **−5,369**. The revenue effect is nonetheless a gain of about £0.03bn: in the combined run, leavers give up £0.32bn of earnings but the measure records only £5m of lost revenue, while entrants add £0.04bn. The measure is the change in the whole tax-benefit system, not tax on earnings alone. policyengine-uk counts funded hours in household net income (`household_benefits`), at the DfE funding rates (£12.04 an hour for under-2s in 2026-27, £12.32 in the 2027-28 run). A low-earning parent who leaves work gives up working-parent hours worth more to the exchequer than the tax on their earnings, which offsets the lost tax and higher benefits. In the free-hours leg alone, leavers raise net revenue by £7m.

The sign should not be leaned on. It moved four times under review on the Enhanced FRS: +5,558 on a double-counted subsidy; −10,361 after correcting that; +3,662 after fixing an entity-mapping error, where support was read on the child's row and every adult saw zero; and +2,804 after restricting the out-of-work support adjustment to people already in work, since for a non-worker it was a third credit. All four were errors here, found by audit rather than by this repository's own tests. It moved again with the data and engine (see *What moved*). What is robust is the magnitude: the response is small against an £8.6bn reform on every version, and the two legs pull hard against each other.

Placing imputed entrant earnings at full-time equivalent, as policyengine-uk does, would move the figure again. That is an unvalidated upstream assumption and is not adopted here.

The participation response leaves out parents whose youngest child is under 1, though the reform pays some of those children universal hours. The direction of that omission is not measured: working parents of those children on the 30-hour offer face the same lower gain to work as the free-hours leg's leavers. Only parents whose youngest child is eligible respond, following the IFS finding of no effect where a younger child still needs care. The response is also not robust: see the audit findings below.

**The intensive margin is much larger, and overlaps with it.** Parents already in work and paying for childcare see their out-of-pocket cost fall by about 63% under both legs together, and at a childcare price elasticity of hours of −0.042 that is 2.6% more hours: about 37,453 full-time equivalents, £2.12bn of earnings and **£0.88bn** back to the exchequer once the model has taxed the extra earnings and withdrawn benefits on them. Subtracting both margins from the static £8.56bn gives **£7.65bn**; the two margins overlap (below), so this sum counts part of the response twice and the £0.91bn offset is an upper estimate. Static cost less each margin separately is £8.53bn with the participation response only and £7.68bn with the hours response only. The elasticity was proposed by Max Mosley and is derived from Brewer et al. (+0.600 hours a week over a mean of 14.319, against a 100% price fall); it is a total-hours effect measured over all mothers including those not working, so it already contains the participation channel and the two margins should not be read as additive. The treatment it comes from was a move from the part-time offer (12.5-15 hours a week) to full-time school hours (30-35), not a price fall of 100%. See `hours_response.py` and `sources.HOURS_PRICE_ELASTICITY`.

**Distributionally, the average gain is lowest in the middle quintiles and highest at the top.** Among families with a child under 5 in 2027-28, on the central participation response without the hours response, the average annual gain runs Q1 £1,997, Q2 £1,642, Q3 £1,666, Q4 £3,394, Q5 £5,299. As a share of net income the same gains run Q1 3.85%, Q2 2.30%, Q3 2.20%, Q4 3.68%, Q5 3.42%. Families in the lower quintiles gain less from the subsidy in cash because Universal Credit already covers 85% of their childcare costs, which this reform keeps, and because they use fewer paid hours; the bottom quintile gains more than the next two because of the free-hours leg.

The free-hours leg falls with income and rises again at the top. On the static costing, the share of under-5 families gaining runs **Q1 30.6%**, Q2 23.6%, Q3 16.8%, Q4 14.8%, Q5 22.5% — the bottom quintile is the most likely to gain, and the top quintile contains the families above £100,000 who are excluded from it today and who the unconditional 15 hours reaches. Averaging the two legs together hides that.

Computed on Microcosm UK 2024-25, national release **a133f37a** (23 October 2026; `policyengine/populace-uk-private` at `c3a751d9`), with policyengine.py 6.10.1 and policyengine-uk 2.148.4.

## What moved from the Enhanced FRS 1.57.2 results

The previous results were computed on the Enhanced FRS 1.57.2 with policyengine-uk 2.94.0. The middle column runs this repository's current reform code on the same Enhanced FRS with policyengine-uk 2.148.4, so it separates the engine and code changes from the data change. It is a static rerun: the dynamic cost and net entrants were not recomputed on that combination after the displacement correction.

| | Enhanced FRS 1.57.2, pe-uk 2.94.0 | Enhanced FRS 1.57.2, pe-uk 2.148.4 | Microcosm a133f37a, pe-uk 2.148.4 |
| --- | --- | --- | --- |
| **2027-28** free-hours leg | £1.97bn | £2.58bn | £3.45bn |
| subsidy leg | £4.84bn | £4.80bn | £5.55bn |
| both legs, static | £6.64bn | £7.11bn | £8.56bn |
| both legs, both margins summed (central) | £5.95bn | — | £7.65bn |
| both legs, participation only (central) | — | — | £8.53bn |
| both legs, hours only | — | — | £7.68bn |
| net entrants (central) | +2,804 | — | −5,369 |
| **2028-29** free-hours leg | £2.01bn | £2.64bn | £3.47bn |
| subsidy leg | £4.96bn | £4.92bn | £5.67bn |
| both legs, static | £6.80bn | £7.28bn | £8.71bn |
| both legs, both margins summed (central) | £6.06bn | — | £7.77bn |
| both legs, participation only (central) | — | — | £8.67bn |
| both legs, hours only | — | — | £7.81bn |
| net entrants (central) | +2,842 | — | −6,102 |
| **2029-30** free-hours leg | £2.06bn | £2.70bn | £3.54bn |
| subsidy leg | £5.09bn | £5.04bn | £5.81bn |
| both legs, static | £6.98bn | £7.47bn | £8.91bn |
| both legs, both margins summed (central) | £6.22bn | — | £7.95bn |
| both legs, participation only (central) | — | — | £8.88bn |
| both legs, hours only | — | — | £7.98bn |
| net entrants (central) | +2,863 | — | −6,175 |

**Engine and code (first to second column).** The free-hours leg rises by £0.61bn in 2027-28. policyengine-uk 2.147 onwards stacks universal hours under the working-parent hours, starts the working-parent hours the term after a child reaches 9 months, removes reception-age children from the free hours from the term they start school, and funds 2027-28 hours at £12.32, £9.10 and £6.76 an hour for under-2s, 2-year-olds and 3-4 year olds. This repository's reform now applies the 9-month floor from the date of birth, which on the Enhanced FRS adds £0.51bn of hours at age 0. The subsidy leg barely moves, and both legs together rise by £0.47bn.

**Data (second to third column).** The free-hours leg rises by a further £0.87bn, almost all of it at age 1: new hours at age 1 are £1.95bn on Microcosm against £1.13bn on the Enhanced FRS, while age 0 falls from £0.51bn to £0.40bn and age 2 rises from £0.94bn to £1.09bn. Microcosm has more 1-year-olds in England outside the working-parent scheme whose families would take up universal hours — about 285,000 against 158,000, with `would_claim_universal_childcare` at 78% of those children against 52% — and fewer 1-year-olds receiving working-parent hours, 224,000 against 298,000. The subsidy leg rises by £0.75bn: Microcosm's England under-5 fee base is £7.13bn against £6.36bn, and its Tax-Free Childcare take-up flag is 0.96 against 0.89 among benefit units with a qualifying child.

**Labour supply, across both steps.** The dynamic figures were not rerun for the middle column, so they compare the first column with the third only. The participation response turns negative, mainly because the subsidy leg draws fewer entrants (+9,083 against +11,930) while the free-hours leg loses slightly more workers (−18,544 against −17,014); the hours response rises from £0.67bn to £0.88bn.

**The age 0 and age 1 split may move on the next Microcosm release.** Release a133f37a predates Microcosm's fix to how it draws under-2s (a12885f9, which keys the under-2 draw on DfE age). The free-hours leg turns on that split, so it should be rerun on the first release that includes the fix.

## The modelled baseline against published figures

Each programme's baseline, compared at the year its published figure covers rather than at the costed year:

| Programme | Modelled spending | Official spending | Children, modelled | Children, official |
| --- | --- | --- | --- | --- |
| Universal entitlement, 3-4 | £2.66bn | £1.70bn | 1.09m | 0.78m |
| Working-parent entitlement | £2.23bn | £2.50bn | 0.86m | 0.62m |
| Disadvantaged two-year-olds | £0.29bn | £0.57bn | 0.06m | 0.12m |
| Tax-Free Childcare | £0.58bn | £0.63bn | 1.15m | 1.09m |

Spending for the two entitlements is the dedicated schools grant early years block allocation for 2024-25; caseloads are the DfE censuses and HMRC's outturn. policyengine-uk now stacks the universal hours under the working-parent hours, so the model's universal row carries the first 15 hours of every 3-4 year old, working-parent children included, and the working-parent row only the hours above them. The universal caseload comparator is therefore the 778,327 children registered in January 2024 excluding reception, not the 416,537 left after netting off working-parent children that an earlier version used. The two entitlement rows point in opposite directions — universal is £0.96bn high, working-parent £0.27bn low — so they partly cancel in a total, which is why they are shown separately.

These are independent checks, not the data build's own targets. Microcosm UK 2024-25 calibrates the four schemes at 2025 on later releases — HMRC's March 2026 Tax-Free Childcare statistics (£599.8m to 1,151,515 children) and DfE's 2026 census (621,482 working-parent children aged 2-4, 95,031 disadvantaged two-year-olds and 396,965 universal-only children) — and its build reports each within 0.2%, measured on policyengine-uk 2.147.2. This table uses earlier releases at 2024 on 2.148.4, so it can differ from the calibration fit without either being wrong.

**Each comparison is drawn at its own figure's year, not at 2027.** Setting a 2027 model figure against a January 2025 census measures the gap between the two dates as much as it measures the model: on the working-parent entitlement that reads 1.75×, and much of it is the September 2025 expansion to 30 hours for under-threes, which the census predates. The costed-year baseline is still reported in the dashboard's Baseline tab, labelled as such and deliberately not set against an older statistic.

Three rows are worth knowing about. The **universal entitlement**, at 1,087,776 children against 778,327, counts every child who holds universal hours at any point in the year, including those who start reception in September and keep the summer term, against a January count that excludes reception. The **working-parent entitlement**, at 864,670 children against 621,500, compares an annual model period against a January stock, on a scheme that was mid-rollout — a known mixed basis rather than a solved problem. The **disadvantaged two-year-old offer**, at 64,222 against 115,852, is the weakest fit here; registrations have been falling year on year as the working-parent entitlement absorbs families who would previously have taken that offer, and DfE separately warns that some two-year-olds eligible for both were recorded under working-parent contrary to guidance, which moves children between those two rows.

## How it is modelled

Leg 1 is **a parameter change, a date-of-birth age rule and one exclusion**. policyengine-uk stacks the three DfE schemes rather than treating them as alternatives: the universal entitlement carries no work or income test and is limited to 3-4 year olds, and the working-parent entitlement pays the hours above the universal and targeted hours a child already gets, up to 30 a week. So the reform's second tier is already what the working-parent scheme delivers, and the first is delivered by widening the universal age floor from 3 to 0.75. The floor is applied from each child's date of birth: universal hours start the first term after the child reaches 9 months, the rule the engine already uses for the working-parent hours (see *Known limitations*). For a working family under £100,000 the total does not change; its first 15 hours move from the working-parent line to the universal one.

The exclusion is needed because the targeted two-year-old offer was written for a system where the universal entitlement started at 3. Widening the floor breaks that — a non-working family on qualifying benefits would draw 570 hours from the targeted offer *and* 570 from the universal one, 30 free hours a week where the reform gives 15. On Microcosm a133f37a in 2027-28 that is 47,010 children and £0.19bn. The universal entitlement now steps aside where the family claims the targeted offer: both are 15 hours at the same age-based funding rate, and the targeted offer is the existing policy.

Leg 2 is **structural**. Tax-Free Childcare pays 20% of the gross spend routed through the account — the statutory 25% top-up on what a parent pays in — pro-rated for the part of the year the family is eligible and capped at £2,000 a child. That is a different functional form from a flat share of costs, so `tax_free_childcare` and `tax_free_childcare_eligible` are replaced: no work test, no income cliff, no per-child cap. TFC's existing disqualification of UC and tax-credit recipients is kept, because those families already receive 85% through UC and stacking would subsidise childcare above its price.

`childcare_expenses` in policyengine-uk is out-of-pocket spend *net of* free hours already received, so hours the reform newly makes free are netted out of it before the subsidy applies. The assumed displacement is 90% of new free hours — the IFS finds only about 54 additional hours of care outside the family for every 570 offered — and realised displacement is 20%, because the cap at actual spend binds.

### The labour supply response

policyengine-uk ships an OBR-methodology labour supply framework, but its coordinator runs only the intensive margin — the participation model is present and commented out as a placeholder. Childcare is the canonical extensive-margin question, so the margin that matters is the one that is not wired up.

**Three things in that module had to be replaced when this analysis was first built on policyengine-uk 2.94.** The first two have since been fixed upstream; the local versions are kept, and the figures quoted for them were measured on the Enhanced FRS 1.57.2.

*A units bug upstream* ([policyengine-uk#1839](https://github.com/PolicyEngine/policyengine-uk/issues/1839)). `impute_wages_for_nonworkers` computed `employment_income / (hours_worked * 52)`, but `hours_worked` in policyengine-uk is **annual** — mean about 1,905 among workers on Microcosm a133f37a. Dividing by 52 a second time gave £0.43 an hour on the Enhanced FRS, so a non-worker was imputed **£194 of annual earnings** for entering part-time work instead of about £21,600. Entering work then appeared to pay almost nothing and the extensive margin collapsed to near-zero entrants. The local imputation is kept because its donor pool is working adults whose youngest child is the same age, which is the comparison group for a childcare reform.

*Quintiles taken over the wrong population.* `calculate_earnings_quintile` applied `pd.qcut` to raw `employment_income` across every person, children included, so its bottom two quintiles were entirely non-earners and **every** potential entrant landed in Q1 or Q2 — where the OBR's Table A1 elasticities are at their highest. `potential_earnings_quintile` places adults by their potential earnings — actual for workers, imputed for non-workers — against the weighted quintile thresholds of working adults' observed earnings, which is what policyengine-uk now does. An earlier version ranked by cumulative weight to split the point masses that imputed earnings create, but ranking forces equal population shares and splits a tied mass by input row order, so identical adults could draw different elasticities by file position.

*No imputed childcare cost for entrants.* Nothing imputes what a non-worker would **pay for childcare** on entering work, and `childcare_expenses` records what they spend today — nothing, for about three quarters of eligible non-workers on Microcosm a133f37a, because they are at home with the child. A subsidy applied to zero is worth zero, so the channel by which cheaper childcare draws a parent into work was invisible for exactly the people who would move. `childcare_cost_when_working` assigns a potential entrant the mean spend of *working* families whose youngest child is the same age, pro-rated to the entrant's assumed hours and taken net of the subsidy that scenario pays. Using working families' observed spend as the base means the free hours they already receive are embedded in it, so the entitlement is not double-counted.

All three pushed the same way — they suppressed the *positive* side of the response — so the uncorrected model was biased toward finding that the reform reduces employment. The corrected model still finds a small net fall on the central assumption, −5,369 net entrants in 2027-28, because the free-hours leg's leavers outweigh the subsidy leg's entrants: 12,938 leavers against 7,568 entrants in the combined run.

More importantly, that framework measures work incentives as the gain to work in `household_net_income`, which does not net off childcare costs. Childcare is a cost of working, so the channel by which a childcare subsidy raises employment is invisible to it. `labour_supply.py` reuses what is right — the OBR participation elasticities (which vary by gender, partner employment status, age of youngest child and earnings quintile) and the gain-to-work machinery (which recomputes the whole tax-benefit system with employment switched off) — and adds the two childcare terms:

```
gain to work = in-work net income
             - childcare paid out of pocket while working
             - (out-of-work net income - cost-contingent childcare support)
```

The second correction matters because `childcare_expenses` is a fixed input: without it a non-worker is credited with a subsidy on care they are not buying, and the reform's work-condition-free subsidy would look worthless as a work incentive. Free-hours entitlements are deliberately *not* netted out of out-of-work income — their availability out of work is a real reduction in the gain to work, and the model should show it.

Central elasticity −0.15, bounds −0.05 and −0.30, from Akgündüz and Plantenga's meta-analysis adjusted downward for the UK (publication bias; a European mean of −0.19 against a US mean of −0.35; and significantly smaller elasticities in high part-time, high participation countries). The response is confined to parents whose *youngest* child is in the eligible band, following the IFS. The hours response uses the same population, restricted to those in work with a positive out-of-pocket childcare cost, and scales with the same low/central/high multiplier.

## Layout

- `src/free_childcare_reform/reforms.py` — the two legs, and the displacement adjustment.
- `src/free_childcare_reform/labour_supply.py` — the extensive-margin participation response.
- `src/free_childcare_reform/hours_response.py` — the intensive-margin hours response for parents in work.
- `src/free_childcare_reform/sources.py` — every non-PolicyEngine number, with a source URL.
- `src/free_childcare_reform/pipeline.py` — orchestration and results JSON.
- `dashboard/` — Next.js dashboard: Reform (budget impact and household effects), Baseline and Methodology.
- `data/` and `dashboard/public/data/` — generated results JSON.

## Reproducing a result

`uv.lock` pins the full dependency set and CI installs from it with `uv sync --frozen`, so the tested environment is the one the results were built in. `.python-version` pins the interpreter patch. Each results file also records what produced it — the analysis commit, whether the working tree was dirty, the Python version, the generation time, the Microcosm revision and the PolicyEngine package versions — under `provenance`, including a SHA-256 digest of the analysis source — so a run from an uncommitted tree still identifies exactly what produced it, and a test fails if the committed results were generated from different source than is checked in. A figure can therefore be traced to a commit rather than only to a package version.

## Run

```bash
uv sync --frozen --extra dev
export HF_TOKEN=hf_xxx  # needs read access to policyengine/populace-uk-private
uv run --frozen python -m free_childcare_reform
```

`--frozen` is deliberate: `pip install -e` resolved fresh dependency versions and ignored the lockfile, so the documented command produced a different environment from the one the committed results were built in.

Costs 2027, 2028 and 2029 by default; `--years 2027` for one. Microcosm UK 2024-25 is read from `policyengine/populace-uk-private` at the commit of the a133f37a release's cut tag (`c3a751d9`) and checked against the sha256 in its release manifest, so the run fails rather than silently using a different file. The manifest pins policyengine-uk 2.147.2; the analysis runs on 2.148.4 through policyengine.py's `managed_microsimulation(allow_unmanaged=True)`.

```bash
cd dashboard
bun install
bun run dev
```

## Correcting the baseline

Neither gap above is a defect in this repo to patch here, and neither should be closed with a scalar applied to the results. Both are dataset properties, and the house pattern — the one the sibling `bus-fare-cap` analysis follows for `bus_fare_spending` — is to calibrate in the data build — Microcosm, for this dataset — and consume the calibrated dataset downstream. One upstream change would close the first.

**1. Add a calibration target for `childcare_expenses`.** The comparison has to be like-for-like, which the first version of this analysis got wrong. The CMA's figure covers **England and the under-5s**; the model's £11.0bn aggregate is **UK and all ages**, and about a quarter of it is school-age wraparound and holiday childcare, a separate market the CMA number excludes. On the comparable slice the model is **£7.13bn against a benchmark of about £5.1bn — a gap of roughly 1.40×**. The benchmark must be gross of Tax-Free Childcare and the UC childcare element, since `childcare_expenses` is the fee both of those are computed from; an earlier version of this analysis netted them off and reported the gap as 1.7×. The Tax-Free Childcare award does not corroborate a fee-base overstatement: at 2024 the model's average award is £505 a child against HMRC's £583, *below* rather than above, though the award also depends on the routed-spend share (see *Known limitations*). There is no published aggregate for school-age childcare spend, so that part of the base cannot be calibrated in either direction and should be left alone.

**One thing take-up is *not*.** An earlier version of this analysis reported a 1.52× take-up gap and recommended retargeting `would_claim_tfc`. That was wrong: it compared the model's annual claimant count against HMRC's *point-in-time* March 2026 figure of 601,000 families, a stock against a flow. On the annual figure the model's 2024 child caseload is 1.06× HMRC's, and Microcosm calibrates it at 2025 on HMRC's later release. The recommendation is withdrawn.

**Which take-up flag.** The subsidy is defined for `would_claim_tfc`, Tax-Free Childcare's take-up input. The alternative put to us — read take-up from the extended (30-hour) entitlement's flag instead, since the reform drops TFC's restrictions — is costed alongside it in `subsidy_take_up.extended_entitlement_flag`. It moves the leg the other way from the argument for it: on this data the TFC flag is the higher of the two (0.96 against 0.85 among benefit units with a qualifying child), so the subsidy leg falls from £5.55bn to £4.79bn and its net entrants from about 9,100 to 6,200 in 2027-28. Neither flag is estimated for this reform. The switch is one line, `reforms.SUBSIDY_TAKE_UP_FLAG`.

**Do not carry take-up into the reform unchanged.** A 75% subsidy with no work test and no cap is a far more valuable and far simpler benefit than a 20% top-up capped at £2,000 with a work test and a £100,000 cliff. The model holds take-up fixed between baseline and reform, which understates the reform's cost. Take-up under a universal subsidy is a separate assumption that has to be stated and defended on its own, and the cost is close to linear in it.

The Baseline tab reports the rebased figure as an illustrative sensitivity, rebasing only the under-5 slice: the subsidy leg falls from £5.55bn to **£4.40bn** and both legs from £8.56bn to **£7.50bn** in 2027-28. It is not a lower bound — the CMA residual it rests on is provider income less entitlement funding, which is parent fees *and other sources*, and scenarios in the other direction exceed the headline.

## Known limitations found in review

**The 9-month floor is modelled from the date of birth, term by term.** A child gets universal hours from the first term (1 January, 1 April or 1 September) after it reaches 9 months — the rule policyengine-uk already applies to the working-parent hours (`extended_childcare_entitlement_term_share`) — rather than from a whole-year age, which would make the floor age 1. In 2027-28 the leg's new hours are £0.40bn at age 0, £1.95bn at age 1 and £1.09bn at age 2, for about 155,000, 350,000 and 212,000 children. The day of birth comes from Microcosm's `age` and `months_since_last_birthday`, so the age-0 and age-1 split depends on how Microcosm draws under-2s (see *What moved*). The participation response still uses whole-year ages and leaves out parents whose youngest child is aged 0.

**Displacement is now 90%, from the any-care figure rather than the subsidisable-care one.** The analysis previously used 163 additional hours per 570 (29% additionality) from IFS BN189, which is the estimate for *subsidisable* care — a category including state schools — and for the part-time offer. On any care outside the family the same note gives 54 per 570, and the peer-reviewed successor corroborates about 57, though not significantly. No single number is well supported: displacement is roughly 70-90% on formal hours and 90-100% on total care. Running it at 71% instead raises the 2027-28 combined cost from £8.56bn to £8.64bn, because the cap at actual spend binds first.

**The subsidy applies to all reported childcare spend; Tax-Free Childcare in the baseline does not.** The baseline award applies `tax_free_childcare_spend_routed_share`, the share of spend paid through the account, which Microcosm sets at a flat 0.593. The 75% subsidy applies to the whole of `childcare_expenses`, which assumes every pound a qualifying family spends would be claimed. Applying the same routed share to the subsidy would take the 2027-28 subsidy leg from £5.55bn to £3.05bn. That is a sensitivity, not a change to the costing: the routed share describes how families use today's 20% top-up, and how they would use a 75% subsidy is not observed.


**Participation elasticities are read at 2025, not the costed year.** The upstream helper resolves its inputs at the default calculation period. Because the dataset does not age people across projection years, only uprated earnings differ, so this is latent rather than live — but it becomes real if the dataset starts ageing.

## Caveats

- **Take-up is modelled, and assumed unchanged by the reform.** Both are discussed under *Correcting the baseline*. The 2024-25 expansion came in 26-28% above forecast on take-up alone, so an unresponsive take-up assumption understates an expansion's cost.
- **Childcare supply is assumed to accommodate demand.** No capacity constraint and no fee response to a 75% subsidy, which would be expected to raise prices.
- **Free hours are valued at the DfE funding rate**, not the market price, so a family's true gain is larger where providers charge above it. There is no regional variation in the rate.
- **The entitlements are England-only** in law and in the model; Barnett consequentials are not costed. Tax-Free Childcare and its replacement are UK-wide.
- **The hours response is a single elasticity applied at a constant wage, and no macro feedback.** It assumes labour demand absorbs the extra hours at the current wage, and the elasticity contains the participation channel (above). One UK study finds 61-72% of gross cost recouped once demand-side effects are included, but it assumes the employment response rather than estimating it.
