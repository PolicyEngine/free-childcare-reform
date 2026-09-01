"use client";

import { formatFiscalYear } from "../lib/formatters";
import SectionHeading from "./SectionHeading";

function Block({ title, children }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <ul className="mt-3 list-disc space-y-3 pl-5 text-sm leading-6 text-slate-600">
        {children}
      </ul>
    </div>
  );
}

export default function MethodologyTab({ data, year }) {
  const src = data.sources || {};
  const assumptions = data.assumptions || {};
  const params = data.model_parameters || {};
  const result = data.by_year[String(year)];
  const A = (source, text) =>
    source ? (
      <a href={source.url} target="_blank" rel="noreferrer" className="underline">
        {text}
      </a>
    ) : (
      text
    );

  const fundingRates = params.childcare_funding_rate_gbp_per_hour || {};

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="How the reform is modelled"
          description="Model parameters below are read from the simulation at run time; the caveats quote fixed figures from the sources they cite."
        />
        <Block title="The two legs">
          <li>
            <strong>Free hours is a single parameter change.</strong> policyengine-uk
            models the three DfE schemes as mutually exclusive rather than stacking, and
            the universal entitlement already carries no work or income test — it is just
            limited to 3-4 year olds and switched off for families on the extended
            (working-parent) scheme, which pays the full 30 hours. So the reform&apos;s
            second tier is already what the extended scheme delivers, and the first is
            delivered by widening the universal age floor from{" "}
            <strong>{params.baseline_universal_entitlement_age_min}</strong> to{" "}
            <strong>{params.reform_universal_entitlement_age_min}</strong> years. One
            exclusion is added: the widened entitlement would otherwise stack on the
            disadvantaged two-year-old offer, giving those children 30 free hours where
            the reform gives 15.
          </li>
          <li>
            <strong>The subsidy is structural.</strong> Tax-Free Childcare pays{" "}
            <code className="rounded bg-slate-100 px-1">rate / (1 - rate)</code> of
            parental spend — a{" "}
            {(params.baseline_tax_free_childcare_rate * 100).toFixed(0)}% rate giving a 25%
            top-up — capped at £
            {params.baseline_tax_free_childcare_cap_gbp?.toLocaleString("en-GB")} a child,
            with a work test and a £
            {params.extended_entitlement_income_limit_gbp?.toLocaleString("en-GB")} cliff.
            A flat {(params.reform_subsidy_rate * 100).toFixed(0)}% share is a different
            functional form, so both formulas are replaced: no work test, no cliff, no cap.
            The UC childcare element is kept at{" "}
            {(params.uc_childcare_coverage_rate * 100).toFixed(0)}%, so UC families keep
            that rather than stacking a further 75% on the same spend.
          </li>
          <li>
            <strong>The legs are not additive.</strong>{" "}
            <code className="rounded bg-slate-100 px-1">childcare_expenses</code> is spend
            net of free hours already received, so hours the reform newly makes free are
            netted out before the subsidy applies. <strong>{(assumptions.free_hours_displacement * 100).toFixed(0)}%</strong> of new free
            hours displaces care a family was already getting —{" "}
            {A(src.ifs_free_childcare, "the IFS evaluation")} finds only about 54 additional
            hours of care outside the family for every 570 offered. Displacement is also
            capped at what a family actually spends, and that cap binds: realised
            displacement is about 12% of the value of the new free hours.
          </li>
          <li>
            Free hours are valued at the DfE funding rate — what government pays a
            provider, not the market price — over {params.weeks_per_year} weeks a year, on
            a single national scale by child age ({Object.entries(fundingRates)
              .map(([band, rate]) => `${band.replace(/_/g, " ")} £${rate.toFixed(2)}`)
              .join(", ")}
            ). Local-authority variation is not modelled.
          </li>
        </Block>
      </section>

      <section>
        <SectionHeading
          title="The labour supply response"
          description="Reported alongside the static cost, never instead of it — and switchable off entirely on the reform tab."
        />
        <Block title="What is added to policyengine-uk, and what is assumed">
          <li>
            policyengine-uk ships an{" "}
            {A(src.obr_labour_supply, "OBR-methodology labour supply framework")}, but its
            coordinator runs only the intensive margin and its participation model measures
            work incentives in household net income, which does not net off childcare
            costs. Childcare is a cost of working, so the main channel by which a childcare
            subsidy raises employment is invisible to it. This analysis reuses the OBR
            elasticities and gain-to-work machinery and adds the two missing terms:
            out-of-pocket childcare is subtracted from in-work income, and cost-contingent
            support from out-of-work income.
          </li>
          <li>
            Two upstream defects are worked around here and reported as{" "}
            <a
              href="https://github.com/PolicyEngine/policyengine-uk/issues/1839"
              target="_blank"
              rel="noreferrer"
              className="underline"
            >
              policyengine-uk#1839
            </a>
            : a units error crediting a non-worker with about <strong>£194</strong> of
            annual earnings for entering part-time work rather than roughly £21,600, and
            the absence of any imputation of what a potential entrant would{" "}
            <em>pay</em> for childcare, which leaves 85% of eligible non-workers with a
            subsidy applied to zero. Both suppress the extensive margin; the fixes belong
            upstream rather than in this repo.
          </li>
          <li>
            Elasticities are the OBR&apos;s, by gender, partner employment, age of youngest
            child and earnings quintile, scaled by{" "}
            {assumptions.elasticity_scale_low?.toFixed(2)}× and{" "}
            {assumptions.elasticity_scale_high?.toFixed(2)}× for the low and high bounds.
            The central childcare price elasticity of {assumptions.price_elasticity_central}{" "}
            sits below {A(src.akgunduz_plantenga, "the meta-analytic mean of −0.277")}{" "}
            because of publication bias, a European mean of −0.19 against a US −0.35, and
            smaller elasticities in high part-time, high participation countries.
          </li>
          <li>
            The response is a floor in three ways. Whole-year ages cannot separate the
            9-to-12-month cohort from younger babies, so that cohort is excluded with
            them — including the whole age-0 group would add roughly 14% to the central
            response, while sweeping in families whose youngest child is too young to
            qualify. The response is also confined to parents whose <em>youngest</em>{" "}
            child is eligible —{" "}
            {A(src.ifs_free_childcare, "the IFS")} finds no effect where a younger,
            non-eligible child still needs care. Only the extensive margin is modelled, and{" "}
            {A(src.bettendorf_jongen_muller, "Dutch evidence")} suggests hours respond about
            twice as much as employment, so this is a floor rather than the whole response.
            The elasticity bounds are the handle on uncertainty: the central childcare
            price elasticity of {assumptions.price_elasticity_central} scales to{" "}
            {assumptions.price_elasticity_low} and {assumptions.price_elasticity_high} for
            the low and high cases.
          </li>
        </Block>
      </section>

      <section>
        <SectionHeading
          title="Caveats"
          description="Things that would change these numbers and are not modelled."
        />
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <ul className="list-inside list-disc space-y-2 text-sm leading-6 text-slate-600">
            <li>
              <strong>The 9-month tier is modelled as starting at age 1.</strong> Family
              Resources Survey ages are whole years, so the reform&apos;s 0.75 age floor
              evaluates as &ldquo;age 1 or over&rdquo;, and no child recorded as age 0
              receives the entitlement — verified as exactly zero children. The
              9-to-12-month cohort the reform covers is therefore not costed here.
              Measured directly, lowering the floor to zero raises the leg from £1.97bn to
              £3.73bn, so the whole age-zero group is worth £1.76bn and a three-month
              share is about <strong>£0.44bn, or 22% of the free-hours leg</strong>, which
              is missing from the cost. Modelling it properly needs month-of-age and
              term-start rules — eligibility begins the term after a child turns nine
              months — not a different threshold. The labour supply response omits the
              same children, so both sides are consistent.
            </li>
            <li>
              <strong>The participation elasticities are read at 2025.</strong> The
              upstream OBR helper resolves its inputs at the model&apos;s default
              calculation period rather than the costed year, so the elasticities applied
              to 2027-28 to 2029-30 are 2025 elasticities. Because the dataset does not
              age people across projection years, only uprated earnings differ between
              them, so the effect today is negligible — but the figures are 2025
              assumptions, not year-specific ones.
            </li>
            <li>
              <strong>Take-up is held fixed at the baseline rates.</strong> The Enhanced
              FRS does apply a take-up haircut — about 88% for Tax-Free Childcare, 81% for
              the working-parent entitlement, 56% for universal and 59% for the
              disadvantaged offer — so this is not a full-take-up costing. What is assumed
              is that those rates do not change under the reform.
            </li>
            <li>
              <strong>That assumption is the important one.</strong> Making 15 hours
              unconditional would draw in families who use no formal childcare today, which
              pushes the cost the other way. The 2024-25 expansion came in 26-28% above
              forecast on take-up alone.
            </li>
            <li>
              <strong>Childcare supply is assumed to accommodate demand.</strong> No
              provider capacity constraint, no price response to a 75% subsidy. A subsidy
              that large would be expected to raise fees, which the model cannot show.
            </li>
            <li>
              <strong>Geography.</strong> The entitlements are England-only in law and in
              the model. Barnett consequentials for the devolved nations are not costed.
              Tax-Free Childcare and its replacement are UK-wide.
            </li>
            <li>
              <strong>The free-hours value is the funding rate, not the market price.</strong>{" "}
              Where providers charge above the funding rate, a family&apos;s true gain is
              larger than the model shows.
            </li>
            <li>
              <strong>No intensive margin, no macro feedback.</strong> Hours changes among
              existing workers are not modelled, and neither is any demand-side or
              multiplier effect. {A(src.de_henau, "One UK study")} finds 61-72% of the gross
              cost recouped once those are included, but it assumes the employment response
              rather than estimating it.
            </li>
          </ul>
        </div>
      </section>

      <section>
        <SectionHeading title="Sources" description="Every external number used, with its origin." />
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <ul className="list-disc space-y-3 pl-5">
            {Object.values(src).map((source) => (
              <li key={source.url} className="text-sm leading-6 text-slate-600">
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-semibold text-slate-900 underline"
                >
                  {source.label}
                </a>{" "}
                — {source.description}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
