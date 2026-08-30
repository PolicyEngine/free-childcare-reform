# Free childcare reform

Costing of a two-part universal childcare reform for the UK, 2027 to 2029, on the PolicyEngine UK Enhanced FRS — static and with an extensive-margin labour supply response.

## The reform

**Leg 1 — free hours.** Replace the current split (30 free hours for under-5s whose parents work and earn under £100,000; 15 hours for 3-4 year olds regardless) with **15 hours free for every child from 9 months to school age**, plus **a further 15 hours** where parents work and earn under £100,000.

**Leg 2 — childcare subsidy.** Replace Tax-Free Childcare (a 25% top-up on parental spend, capped at £2,000 a child, gated on work and a £100,000 income cliff) with a **75% subsidy of childcare costs for all**. The Universal Credit childcare element is kept unchanged at 85%.

## Headline results

Static cost of both legs together, and the same with the central labour supply response:

| Year | Free hours | 75% subsidy | Both, static | Both, with labour supply |
| --- | --- | --- | --- | --- |
| 2027 | £2.15bn | £4.84bn | £6.84bn | £6.82bn |
| 2028 | £2.20bn | £4.96bn | £7.01bn | £6.99bn |
| 2029 | £2.25bn | £5.09bn | £7.19bn | £7.17bn |

Computed on Enhanced FRS release **1.57.2** (HuggingFace `7b0a06f0`, 30 August 2026) with policyengine-uk 2.94.0. An earlier version of this analysis, on release 1.56.x and policyengine-uk 2.92.0, reported £2.28bn / £4.46bn / £6.60bn for 2027. The change is almost entirely the Tax-Free Childcare baseline correction described below, which raises the subsidy leg by about £0.38bn and the combined cost by about £0.25bn.

The legs do not sum to the combined figure: free hours displace paid care, which shrinks the base the subsidy applies to.

**The Tax-Free Childcare baseline has been corrected, and it is what moved these numbers.** Earlier versions of this analysis carried a baseline ~1.9× too high: the model paid £1.24bn of Tax-Free Childcare in 2027 against HMRC's £599.8m outturn, and the larger part of that was **TFC routing** — the scheme pays 25% of spend put *through a TFC account*, and the model routed £5,412 per claiming family where HMRC implies £2,764. That was fixed upstream in [policyengine-uk-data#473](https://github.com/PolicyEngine/policyengine-uk-data/pull/473) and the calibration target corrected in [#472](https://github.com/PolicyEngine/policyengine-uk-data/pull/472) and [#474](https://github.com/PolicyEngine/policyengine-uk-data/pull/474), all of which ship in release 1.57.2. The release build now measures TFC spending at **0.99×** its £632.2m target, against 1.87× before.

On this release the model pays **£0.67bn against HMRC's £599.8m — 1.11×**, and, as predicted, correcting a baseline that was nearly double its true size *raises* the reform's incremental cost: the subsidy leg goes from £4.46bn to £4.84bn. The earlier note that the £4.46bn was "understated by roughly £0.6bn once the baseline is corrected" was right in direction and somewhat high in magnitude; the realised move is £0.38bn.

**The residual has changed character, and the remaining question is now caseload, not fees.** The old gap was entirely the average award — £1,353 against £691, a ratio of 1.96×, with claimants about right at 1.05×. It is now the reverse: the average award is **£600 against £691 (0.87×)** while claimants are **1.11m against 868,095 (1.28×)**. Some of that caseload gap is projection rather than error — these are 2027 figures and the caseload has been growing about 5% a year — but not all of it. The fee-base sensitivity is still reported in the dashboard's Benchmarks tab; it now works against a baseline that is close to right rather than one that was doubled.

**The labour supply response is small and its sign is genuinely ambiguous.** Two forces pull against each other:

- *Downward.* The reform removes work conditions from childcare support. A parent of a child under 3 gets nothing today unless they work; under the reform they get 15 hours either way, so the gain to work falls for exactly the families the policy targets. Working parents under £100,000 already get 30 hours, so their position is unchanged.
- *Upward.* The 75% subsidy cuts the price of the care that working requires.

The gain-to-work model, which sees both, gives about **12,600 entrants against 8,100 leavers — a net +4,550**. The price-elasticity cross-check, which sees only the price fall and so cannot be negative, gives about **+28,200**. Either way the labour supply effect is small: it moves the cost by roughly 0.3%, well inside the uncertainty on the static number.

On the pre-correction baseline this figure was a net **−950**, and the analysis warned that the sign should not be leaned on. Correcting the Tax-Free Childcare baseline moved it positive — a smaller baseline means the 75% subsidy is a larger gain to work, so entrants rise and leavers fall. The sign is now positive on both methods, but at 4,550 net entrants against a working population in the millions it remains small enough that it should be read as "approximately zero, probably slightly positive" rather than as a participation finding.

For scale, the IFS found the move from 15 to 30 hours put about 12,000 more mothers into work a year, and the government's own costing of the 2023 expansion assumed about 60,000 entrants by 2027-28 — but both of those *added* work-conditional hours, where this reform makes existing hours unconditional.

**Distributionally, the cash gain rises with income.** Among households with a child under 5 in 2027, the average annual gain runs from about £1,160 in the bottom quintile to about £3,070 in the top. Low-income families gain less in cash because Universal Credit already covers 85% of their childcare costs — which this reform keeps — and because they use fewer paid hours. As a share of net income the gradient reverses at the bottom: Q1 gains most.

## How it is modelled

Leg 1 turns out to be a **single parameter change**. policyengine-uk models the three DfE schemes as mutually exclusive rather than stacking: the universal entitlement already carries no work or income test, is limited to 3-4 year olds, and is switched off for families who qualify for the extended working-parent scheme, which pays the full 30 hours. So the reform's second tier is already what the extended scheme delivers, and the first tier is delivered by widening the universal scheme's age floor from 3 to 0.75. No formula is altered.

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
- `src/free_childcare_reform/labour_supply.py` — extensive-margin response and the price-elasticity cross-check.
- `src/free_childcare_reform/sources.py` — every non-PolicyEngine number, with a source URL.
- `src/free_childcare_reform/pipeline.py` — orchestration and results JSON.
- `dashboard/` — Next.js dashboard with Budget impact, Household effects, Benchmarks and Methodology tabs.
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

**1. Add a calibration target for `childcare_expenses`.** The comparison has to be like-for-like, which the first version of this analysis got wrong. The CMA's figure covers **England and the under-5s**; the model's £11.4bn aggregate is **UK and all ages**, and about a third of it is school-age wraparound and holiday childcare, a separate market the CMA number excludes. On the comparable slice the model is **£6.35bn against a benchmark of about £3.75bn — a gap of roughly 1.7×, not 3×**. That is still a real gap, and it is corroborated independently by the 1.36× average-award gap in Tax-Free Childcare, which is the same overstatement seen through a different variable. There is no published aggregate for school-age childcare spend, so that part of the base cannot be calibrated in either direction and should be left alone.

**One thing take-up is *not*.** An earlier version of this analysis reported a 1.52× take-up gap and recommended retargeting `would_claim_tfc`. That was wrong: it compared the model's annual claimant count against HMRC's *point-in-time* March 2026 figure of 601,000 families, a stock against a flow. On the annual figure the model is within 5%, and the take-up haircut the data build already applies is about right. The recommendation is withdrawn.

**Do not carry take-up into the reform unchanged.** A 75% subsidy with no work test and no cap is a far more valuable and far simpler benefit than a 20% top-up capped at £2,000 with a work test and a £100,000 cliff. The model holds take-up fixed between baseline and reform, which understates the reform's cost. Take-up under a universal subsidy is a separate assumption that has to be stated and defended on its own, and the cost is close to linear in it.

Until that lands, the Benchmarks tab reports the rebased figure as a sensitivity, rebasing only the under-5 slice: the subsidy leg falls from £4.84bn to **£3.49bn** and the combined static cost from £6.84bn to **£5.53bn** in 2027. That is the honest lower bound. An earlier version of this analysis rebased the whole base against an England under-5 benchmark and reported £3.70bn, which was too aggressive by roughly £1.7bn.

## Caveats

- **Take-up is modelled but targeted too high in the baseline, and assumed unchanged by the reform.** Both are addressed under *Correcting the baseline*. The 2024-25 expansion came in 26-28% above forecast on take-up alone, so an unresponsive take-up assumption understates an expansion's cost.
- **Childcare supply is assumed to accommodate demand.** No capacity constraint and no fee response to a 75% subsidy, which would be expected to raise prices.
- **Free hours are valued at the DfE funding rate**, not the market price, so a family's true gain is larger where providers charge above it. There is no regional variation in the rate.
- **The entitlements are England-only** in law and in the model; Barnett consequentials are not costed. Tax-Free Childcare and its replacement are UK-wide.
- **No intensive margin and no macro feedback.** Hours changes among existing workers are not modelled. One UK study finds 61-72% of gross cost recouped once demand-side effects are included, but it assumes the employment response rather than estimating it.
