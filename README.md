# Free childcare reform

Costing of a two-part childcare reform for the UK, fiscal years 2027-28 to 2029-30, on the PolicyEngine UK Enhanced FRS — static and with an extensive-margin labour supply response.

**Dashboard: https://free-childcare-reform.vercel.app/uk/free-childcare-reform**

## The reform

**Leg 1 — free hours.** Replace the current split (30 free hours for under-5s whose parents work and earn under £100,000; 15 hours for 3-4 year olds regardless) with **15 hours free for every child from 9 months to school age**, plus **a further 15 hours** where parents work and earn under £100,000.

**Leg 2 — childcare subsidy.** Replace Tax-Free Childcare (a 25% top-up on parental spend, capped at £2,000 a child, gated on work and a £100,000 income cliff) with a **75% subsidy of childcare costs for all**. The Universal Credit childcare element is kept unchanged at 85%.

## Headline results

Each leg costed against the current system, on the PolicyEngine UK Enhanced FRS:

| Fiscal year | Free hours | 75% subsidy |
| --- | --- | --- |
| 2027-28 | £1.97bn | £4.84bn |
| 2028-29 | £2.01bn | £4.96bn |
| 2029-30 | £2.06bn | £5.09bn |

**The two legs are reported separately and should not be added.** Free hours displace paid care, so running both at once shrinks the base the 75% subsidy applies to. Both together cost £6.64bn in 2027-28, not the £6.81bn the columns suggest.

The displacement assumption is that 90% of the value of a new free offer replaces care a family was already getting, but displacement is also capped at what they actually spend, and that cap binds hard: modelled childcare spending falls only £0.29bn, or **14% of the £1.97bn of new free hours**. Most newly-eligible families are not working and buy little paid care, so there is little for the free offer to displace. The 90% is the parameter; 14% is what happens — and running it at 71% instead moves the combined cost by £0.03bn.

**The childcare fee base is the largest uncertainty, but the rebasing is an illustrative scenario rather than a bound.** The subsidy pays a share of what families spend, and for England's under-5s the model has £6.36bn of fees against about £5.10bn implied by the CMA — **1.25×**. Scaling the model's under-5 fees to that figure takes the subsidy leg to £4.18bn and both legs to £6.00bn.

Do not read £6.00bn as a lower bound. The CMA does not publish £5.1bn as gross parent-paid fees: it is a residual of an uncertain £14bn sector-income estimate less £8.9bn of entitlement funding, and that residual contains other provider income too. The comparison also sets a 2025-26 residual against 2027-28 nominal fees. Scenarios in the other direction exceed the headline: full take-up within the coded scope gives £7.08bn, and including Universal Credit families in the subsidy gives £7.99bn. Treat £6.00bn as one fixed-quantity accounting scenario among several, not the end of an interval.

**The labour supply response is small and, on the central assumption, slightly positive.** Free hours give **−17,014** net entrants — making 15 hours unconditional removes a reason to work — while the subsidy gives **+13,022**, because cheaper childcare makes work pay. Together, **+3,662**, worth about £0.018bn.

The sign has moved twice under review and should not be leaned on. An earlier version reported +5,558 on a double-counted subsidy; correcting that gave −10,361; and correcting an entity-mapping error found in review — cost-contingent support was read on the child's row, where the payment sits, so every adult saw zero — gives +3,662. Two of the three were errors in this repository, found by audit rather than by its own tests. What is robust is the magnitude: the response is small against a £6.6bn reform on every version, and the two legs pull hard against each other.

Placing imputed entrant earnings at full-time equivalent, as policyengine-uk does, would move the figure again. That is an unvalidated upstream assumption and is not adopted here.

The response is a floor in several ways — whole-year ages exclude the 9-to-12-month cohort, the response is confined to parents whose youngest child is eligible, and only the extensive margin is modelled — but it is also not robust: see the audit findings below.

**Distributionally, the average gain broadly rises with income, but the free-hours leg does not.** Among families with a child under 5 in 2027-28, on the central labour supply assumption, the average annual gain runs Q1 £1,066, Q2 £942, Q3 £2,106, Q4 £2,393, Q5 £3,035 — the bottom two quintiles are close, Q2 is the lowest, and the gradient establishes itself from Q3 up. Low-income families gain less in cash because Universal Credit already covers 85% of their childcare costs, which this reform keeps, and because they use fewer paid hours.

The free-hours leg is U-shaped rather than rising. The share of under-5 families gaining runs Q1 13.0%, Q2 9.9%, Q3 6.4%, Q4 3.6%, **Q5 16.1%** — the top quintile is the most likely to gain, because it contains the families above £100,000 who are excluded from the working-parent entitlement today and who the unconditional 15 hours reaches. Averaging the two legs together hides that.

Computed on Enhanced FRS release **1.57.2** (HuggingFace `7b0a06f0`) with policyengine.py 5.3.0 and policyengine-uk 2.94.0.

## The modelled baseline against published figures

Each programme's baseline, compared at the year its published figure covers rather than at the costed year:

| Programme | Modelled spending | Official spending | Children, modelled | Children, official |
| --- | --- | --- | --- | --- |
| Universal entitlement, 3-4 | £1.30bn | £1.70bn | 0.39m | 0.42m |
| Working-parent entitlement | £2.77bn | £2.50bn | 0.72m | 0.62m |
| Disadvantaged two-year-olds | £0.43bn | £0.57bn | 0.09m | 0.12m |
| Tax-Free Childcare | £0.63bn | £0.63bn | 1.10m | 1.09m |

Spending for the two entitlements is the dedicated schools grant early years block allocation for 2024-25; caseloads are the DfE censuses and HMRC's outturn. The two entitlement rows point in opposite directions — universal is £0.40bn low, working-parent £0.27bn high — so they partly cancel in a total, which is why they are shown separately.

The four programme rows reproduce the comparison `policyengine-uk-data` checks its own release against, on the same published figures, so this table and the data build agree by construction.

**Each comparison is drawn at its own figure's year, not at 2027.** Setting a 2027 model figure against a January 2025 census measures the gap between the two dates as much as it measures the model: on the working-parent entitlement that reads 1.61×, and almost all of it is the September 2025 expansion to 30 hours for under-threes, which the census predates. The costed-year baseline is still reported in the dashboard's Baseline tab, labelled as such and deliberately not set against an older statistic.

Two rows are worth knowing about. The **working-parent entitlement**, at 719,707 children against 621,500, compares an annual model period against a January stock, on a scheme that was mid-rollout — a known mixed basis rather than a solved problem, and the subject of an open review point upstream. The **disadvantaged two-year-old offer**, at 90,587 against 115,852, is the weakest fit here; registrations have been falling year on year as the working-parent entitlement absorbs families who would previously have taken that offer, and DfE separately warns that some two-year-olds eligible for both were recorded under working-parent contrary to guidance, which moves children between those two rows.

## How it is modelled

Leg 1 is **a parameter change plus one exclusion**. policyengine-uk models the three DfE schemes as mutually exclusive rather than stacking: the universal entitlement already carries no work or income test, is limited to 3-4 year olds, and is switched off for families who qualify for the extended working-parent scheme, which pays the full 30 hours. So the reform's second tier is already what the extended scheme delivers, and the first is delivered by widening the universal age floor from 3 to 0.75.

The exclusion is needed because those mutual exclusions were written for a system where the universal entitlement started at 3: `targeted_childcare_entitlement_eligible` excludes extended-eligible families and nothing else, since a 2-year-old could not previously hold the universal entitlement. Widening the floor breaks that — a non-working family on qualifying benefits would draw 570 hours from the targeted offer *and* 570 from the universal one, 30 free hours a week where the reform gives 15. That was 35,252 children and £0.18bn. The universal entitlement now steps aside where the targeted offer applies, since the disadvantaged offer is funded at the 2-year-old rate (£8.28 an hour against £5.88) and is the existing policy.

Leg 2 is **structural**. Tax-Free Childcare's `rate / (1 - rate)` top-up on parental spend is a different functional form from a flat share of costs, so `tax_free_childcare` and `tax_free_childcare_eligible` are replaced: no work test, no income cliff, no per-child cap. TFC's existing disqualification of UC and tax-credit recipients is kept, because those families already receive 85% through UC and stacking would subsidise childcare above its price.

`childcare_expenses` in policyengine-uk is out-of-pocket spend *net of* free hours already received, so hours the reform newly makes free are netted out of it before the subsidy applies. Only 71% of new free hours displaces paid care — the IFS finds that for every 570 free hours offered, children spent only about 163 additional hours in subsidisable care.

### The labour supply response

policyengine-uk ships an OBR-methodology labour supply framework, but its coordinator runs only the intensive margin — the participation model is present and commented out as a placeholder. Childcare is the canonical extensive-margin question, so the margin that matters is the one that is not wired up.

**Three things in that module had to be replaced, not just extended.**

*A units bug upstream.* `impute_wages_for_nonworkers` computes `employment_income / (hours_worked * 52)`, but `hours_worked` in policyengine-uk is **annual** — mean 1,887 among workers, implying a sensible £22.12 hourly wage. Dividing by 52 a second time gives £0.43 an hour, so a non-worker is imputed **£194 of annual earnings** for entering part-time work instead of about £21,600. Entering work then appears to pay almost nothing, the extensive margin collapses to near-zero entrants, and the exchequer appears to recover nothing from anyone who does move. The package contradicts itself here: `dynamics/progression.py` reads `hours_worked / 52` as weekly hours, treating the variable as annual, which is the correct reading and the one used in `impute_entrant_earnings`. Because `calculate_gain_to_work` calls the broken helper internally, it is replaced too, keeping its structure and changing only the imputed earnings.

*Quintiles taken over the wrong population.* `calculate_earnings_quintile` applies `pd.qcut` to raw `employment_income` across every person in the dataset, children included. More than half that population has no earnings, so its bottom two quintiles are entirely non-earners and **every** potential entrant lands in Q1 or Q2 — where the OBR's Table A1 elasticities are at their highest. It also leaves those quintiles with no employed donors at all, which is why the upstream wage imputation draws its donors from the wrong place. `potential_earnings_quintile` takes quintiles over adults only, on potential earnings — actual for workers, imputed for non-workers — which is what the upstream docstring describes but not what it does. Assignment is by weighted rank rather than value cutoffs, because every non-worker in a band shares one imputed value and cutting on values drops whole point masses into a single quintile.

*No imputed childcare cost for entrants.* Nothing imputes what a non-worker would **pay for childcare** on entering work, and `childcare_expenses` records what they spend today — nothing, for 85% of eligible non-workers, because they are at home with the child. A subsidy applied to zero is worth zero, so the channel by which cheaper childcare draws a parent into work was invisible for exactly the people who would move. `childcare_cost_when_working` assigns a potential entrant the mean spend of *working* families whose youngest child is the same age, pro-rated to the entrant's assumed hours and taken net of the subsidy that scenario pays. Using working families' observed spend as the base means the free hours they already receive are embedded in it, so the entitlement is not double-counted.

All three defects pushed the same way — they suppressed the *positive* side of the response — so the uncorrected model was biased toward finding that the reform reduces employment.

More importantly, that framework measures work incentives as the gain to work in `household_net_income`, which does not net off childcare costs. Childcare is a cost of working, so the channel by which a childcare subsidy raises employment is invisible to it. `labour_supply.py` reuses what is right — the OBR participation elasticities (which vary by gender, partner employment status, age of youngest child and earnings quintile) and the gain-to-work machinery (which recomputes the whole tax-benefit system with employment switched off) — and adds the two childcare terms:

```
gain to work = in-work net income
             - childcare paid out of pocket while working
             - (out-of-work net income - cost-contingent childcare support)
```

The second correction matters because `childcare_expenses` is a fixed input: without it a non-worker is credited with a subsidy on care they are not buying, and the reform's work-condition-free subsidy would look worthless as a work incentive. Free-hours entitlements are deliberately *not* netted out of out-of-work income — their availability out of work is a real reduction in the gain to work, and the model should show it.

Central elasticity −0.15, bounds −0.05 and −0.30, from Akgündüz and Plantenga's meta-analysis adjusted downward for the UK (publication bias; a European mean of −0.19 against a US mean of −0.35; and significantly smaller elasticities in high part-time, high participation countries). The response is confined to parents whose *youngest* child is in the eligible band, following the IFS. Only the extensive margin is modelled, so this is a floor on the total response.

## Layout

- `src/free_childcare_reform/reforms.py` — the two legs, and the displacement adjustment.
- `src/free_childcare_reform/labour_supply.py` — the extensive-margin participation response.
- `src/free_childcare_reform/sources.py` — every non-PolicyEngine number, with a source URL.
- `src/free_childcare_reform/pipeline.py` — orchestration and results JSON.
- `dashboard/` — Next.js dashboard: Reform (budget impact and household effects), Baseline and Methodology.
- `data/` and `dashboard/public/data/` — generated results JSON.

## Run

```bash
pip install -e ".[dev]"
export HF_TOKEN=hf_xxx
python -m free_childcare_reform
```

Costs 2027, 2028 and 2029 by default; `--years 2027` for one. The Enhanced FRS 2024-25 is pinned to a revision for reproducibility.

```bash
cd dashboard
bun install
bun run dev
```

## Correcting the baseline

Neither gap above is a defect in this repo to patch here, and neither should be closed with a scalar applied to the results. Both are dataset properties, and the house pattern — the one the sibling `bus-fare-cap` analysis follows for `bus_fare_spending` — is to calibrate in `policyengine-uk-data` and consume the calibrated dataset downstream. Two upstream changes would close them.

**1. Add a calibration target for `childcare_expenses`.** The comparison has to be like-for-like, which the first version of this analysis got wrong. The CMA's figure covers **England and the under-5s**; the model's £11.1bn aggregate is **UK and all ages**, and about a third of it is school-age wraparound and holiday childcare, a separate market the CMA number excludes. On the comparable slice the model is **£6.36bn against a benchmark of about £5.1bn — a gap of roughly 1.25×, not 3×**. The benchmark must be gross of Tax-Free Childcare and the UC childcare element, since `childcare_expenses` is the fee both of those are computed from; an earlier version of this analysis netted them off and reported the gap as 1.7×. The Tax-Free Childcare award no longer corroborates a fee-base overstatement either way: on Enhanced FRS 1.57.2 the average award is £600 against HMRC's £691, slightly *below* rather than above. There is no published aggregate for school-age childcare spend, so that part of the base cannot be calibrated in either direction and should be left alone.

**One thing take-up is *not*.** An earlier version of this analysis reported a 1.52× take-up gap and recommended retargeting `would_claim_tfc`. That was wrong: it compared the model's annual claimant count against HMRC's *point-in-time* March 2026 figure of 601,000 families, a stock against a flow. On the annual figure the model is within 5%, and the take-up haircut the data build already applies is about right. The recommendation is withdrawn.

**Do not carry take-up into the reform unchanged.** A 75% subsidy with no work test and no cap is a far more valuable and far simpler benefit than a 20% top-up capped at £2,000 with a work test and a £100,000 cliff. The model holds take-up fixed between baseline and reform, which understates the reform's cost. Take-up under a universal subsidy is a separate assumption that has to be stated and defended on its own, and the cost is close to linear in it.

The Baseline tab reports the rebased figure as a sensitivity, rebasing only the under-5 slice: the subsidy leg falls from £4.84bn to **£4.18bn** and both legs from £6.64bn to **£6.00bn** in 2027-28. That is the honest lower bound.

## Known limitations found in review

**The 9-month tier is modelled as age 1.** FRS ages are whole years, so the reform's 0.75 age floor evaluates as `age >= 1`, and no child recorded as age 0 receives the entitlement — verified as exactly zero on the pinned dataset. The 9-to-12-month cohort the brief names is therefore not costed.

Measured directly rather than extrapolated: lowering the floor to 0 raises the free-hours leg from £1.97bn to £3.73bn, so the whole age-zero group is worth **£1.76bn** and a three-month share is about **£0.44bn — 22% of the leg**. An earlier version of this README estimated £0.28bn from the age-1 cohort, which was too low: age-zero children are likelier to be in non-working families, so more of them take the universal route rather than the working-parent one. Modelling the cohort properly needs month-of-age and term-start rules, not a different threshold. The labour supply side omits the same children, so the two are consistent.

**Displacement is now 90%, from the any-care figure rather than the subsidisable-care one.** The analysis previously used 163 additional hours per 570 (29% additionality) from IFS BN189, which is the estimate for *subsidisable* care — a category including state schools — and for the part-time offer. On any care outside the family the same note gives 54 per 570, and the peer-reviewed successor corroborates about 57, though not significantly. No single number is well supported: displacement is roughly 70-90% on formal hours and 90-100% on total care. The choice moves the combined cost by £0.03bn either way, because the cap binds first.

**Participation elasticities are read at 2025, not the costed year.** The upstream helper resolves its inputs at the default calculation period. Because the dataset does not age people across projection years, only uprated earnings differ, so this is latent rather than live — but it becomes real if the dataset starts ageing.

## Caveats

- **Take-up is modelled but targeted too high in the baseline, and assumed unchanged by the reform.** Both are addressed under *Correcting the baseline*. The 2024-25 expansion came in 26-28% above forecast on take-up alone, so an unresponsive take-up assumption understates an expansion's cost.
- **Childcare supply is assumed to accommodate demand.** No capacity constraint and no fee response to a 75% subsidy, which would be expected to raise prices.
- **Free hours are valued at the DfE funding rate**, not the market price, so a family's true gain is larger where providers charge above it. There is no regional variation in the rate.
- **The entitlements are England-only** in law and in the model; Barnett consequentials are not costed. Tax-Free Childcare and its replacement are UK-wide.
- **No intensive margin and no macro feedback.** Hours changes among existing workers are not modelled. One UK study finds 61-72% of gross cost recouped once demand-side effects are included, but it assumes the employment response rather than estimating it.
