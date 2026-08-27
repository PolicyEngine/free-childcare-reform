# Free childcare reform

Costing of a two-part universal childcare reform for the UK, 2027 to 2029, on the PolicyEngine UK Enhanced FRS — static and with an extensive-margin labour supply response.

## The reform

**Leg 1 — free hours.** Replace the current split (30 free hours for under-5s whose parents work and earn under £100,000; 15 hours for 3-4 year olds regardless) with **15 hours free for every child from 9 months to school age**, plus **a further 15 hours** where parents work and earn under £100,000.

**Leg 2 — childcare subsidy.** Replace Tax-Free Childcare (a 25% top-up on parental spend, capped at £2,000 a child, gated on work and a £100,000 income cliff) with a **75% subsidy of childcare costs for all**. The Universal Credit childcare element is kept unchanged at 85%.

## Headline results

Static cost of both legs together, and the same with the central labour supply response:

| Year | Free hours | 75% subsidy | Both, static | Both, with labour supply |
| --- | --- | --- | --- | --- |
| 2027 | £2.28bn | £4.46bn | £6.60bn | £6.62bn |
| 2028 | £2.34bn | £4.56bn | £6.77bn | £6.79bn |
| 2029 | £2.42bn | £4.68bn | £6.96bn | £6.98bn |

The legs do not sum to the combined figure: free hours displace paid care, which shrinks the base the subsidy applies to.

**Read the subsidy leg as an upper bound.** The model pays £1.24bn of Tax-Free Childcare against HMRC's £600m outturn. The gap decomposes into two roughly equal parts: **1.52× too many claimants** (914,000 against HMRC's 601,000) and **1.36× too large an average award** (£1,353 against about £998). The second half is the childcare fee base, so the two are one problem, not two. Restating the subsidy leg on the benchmark fee base is reported in the dashboard's Benchmarks tab as a sensitivity. See *Correcting the baseline* below for what would actually fix it.

**The labour supply response is small and its sign is genuinely ambiguous.** Two forces pull against each other:

- *Downward.* The reform removes work conditions from childcare support. A parent of a child under 3 gets nothing today unless they work; under the reform they get 15 hours either way, so the gain to work falls for exactly the families the policy targets. Working parents under £100,000 already get 30 hours, so their position is unchanged.
- *Upward.* The 75% subsidy cuts the price of the care that working requires.

The gain-to-work model, which sees both, gives about **−7,200 net entrants**. The price-elasticity cross-check, which sees only the price fall and so cannot be negative, gives about **+26,000**. For scale, the IFS found the move from 15 to 30 hours put about 12,000 more mothers into work a year, and the government's own costing of the 2023 expansion assumed about 60,000 entrants by 2027-28 — but both of those *added* work-conditional hours, where this reform makes existing hours unconditional.

**Distributionally, the cash gain rises with income.** Among households with a child under 5 in 2027, the average annual gain runs from about £1,290 in the bottom quintile to about £3,270 in the top. Low-income families gain less in cash because Universal Credit already covers 85% of their childcare costs — which this reform keeps — and because they use fewer paid hours. As a share of net income the gradient reverses at the bottom: Q1 gains most.

## How it is modelled

Leg 1 turns out to be a **single parameter change**. policyengine-uk models the three DfE schemes as mutually exclusive rather than stacking: the universal entitlement already carries no work or income test, is limited to 3-4 year olds, and is switched off for families who qualify for the extended working-parent scheme, which pays the full 30 hours. So the reform's second tier is already what the extended scheme delivers, and the first tier is delivered by widening the universal scheme's age floor from 3 to 0.75. No formula is altered.

Leg 2 is **structural**. Tax-Free Childcare's `rate / (1 - rate)` top-up on parental spend is a different functional form from a flat share of costs, so `tax_free_childcare` and `tax_free_childcare_eligible` are replaced: no work test, no income cliff, no per-child cap. TFC's existing disqualification of UC and tax-credit recipients is kept, because those families already receive 85% through UC and stacking would subsidise childcare above its price.

`childcare_expenses` in policyengine-uk is out-of-pocket spend *net of* free hours already received, so hours the reform newly makes free are netted out of it before the subsidy applies. Only 71% of new free hours displaces paid care — the IFS finds that for every 570 free hours offered, children spent only about 163 additional hours in subsidisable care.

### The labour supply response

policyengine-uk ships an OBR-methodology labour supply framework, but its coordinator runs only the intensive margin — the participation model is present and commented out as a placeholder. Childcare is the canonical extensive-margin question, so the margin that matters is the one that is not wired up.

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

**1. Retarget `would_claim_tfc` to the HMRC caseload.** Take-up is already modelled, contrary to first appearances: the variable's default is `True`, but the Enhanced FRS carries `would_claim_tfc` at about 87%, so the data build already applies a haircut. It is simply targeted too high. HMRC reports 601,000 families using Tax-Free Childcare in March 2026 against the model's 914,000 claimants from about 1,046,000 eligible, implying true take-up nearer **57%** of the model's eligible population. Because the imputation should be correlated with the value of the award rather than uniform — the families who do not claim are disproportionately those with least to gain — this belongs in the data build's take-up routine, not in a random mask applied here.

**2. Add a calibration target for `childcare_expenses`.** The comparison has to be like-for-like, which the first version of this analysis got wrong. The CMA's figure covers **England and the under-5s**; the model's £11.4bn aggregate is **UK and all ages**, and about a third of it is school-age wraparound and holiday childcare, a separate market the CMA number excludes. On the comparable slice the model is **£6.35bn against a benchmark of about £3.75bn — a gap of roughly 1.7×, not 3×**. That is still a real gap, and it is corroborated independently by the 1.36× average-award gap in Tax-Free Childcare, which is the same overstatement seen through a different variable. There is no published aggregate for school-age childcare spend, so that part of the base cannot be calibrated in either direction and should be left alone.

**Do not carry baseline take-up into the reform.** A 75% subsidy with no work test and no cap is a far more valuable and far simpler benefit than a 20% top-up capped at £2,000 with a work test and a £100,000 cliff. Modelling it at the baseline's 57% take-up would understate its cost as badly as 87% overstates it. Take-up under the reform is a separate assumption that has to be stated and defended on its own — the honest range is probably 80-95%, and the cost is close to linear in it.

Until those land, the Benchmarks tab reports the rebased figure as a sensitivity, rebasing only the under-5 slice: the subsidy leg falls from £4.46bn to **£3.23bn** and the combined static cost from £6.60bn to **£5.40bn** in 2027. That is the honest lower bound. An earlier version of this analysis rebased the whole base against an England under-5 benchmark and reported £3.70bn, which was too aggressive by roughly £1.7bn.

## Caveats

- **Take-up is modelled but targeted too high in the baseline, and assumed unchanged by the reform.** Both are addressed under *Correcting the baseline*. The 2024-25 expansion came in 26-28% above forecast on take-up alone, so an unresponsive take-up assumption understates an expansion's cost.
- **Childcare supply is assumed to accommodate demand.** No capacity constraint and no fee response to a 75% subsidy, which would be expected to raise prices.
- **Free hours are valued at the DfE funding rate**, not the market price, so a family's true gain is larger where providers charge above it. There is no regional variation in the rate.
- **The entitlements are England-only** in law and in the model; Barnett consequentials are not costed. Tax-Free Childcare and its replacement are UK-wide.
- **No intensive margin and no macro feedback.** Hours changes among existing workers are not modelled. One UK study finds 61-72% of gross cost recouped once demand-side effects are included, but it assumes the employment response rather than estimating it.
