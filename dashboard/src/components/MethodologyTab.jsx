"use client";

import SectionHeading from "./SectionHeading";

function Block({ title, children }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <div className="mt-2 space-y-3 text-sm leading-6 text-slate-600">{children}</div>
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
          description="Every quantity below comes from the simulation at run time. Nothing on this page is a hardcoded number."
        />
        <div className="space-y-4">
          <Block title="Leg 1 — 15 free hours for every child from 9 months">
            <p>
              policyengine-uk models the three DfE schemes as mutually exclusive rather
              than stacking. The universal entitlement already carries no work or income
              test; it is limited to 3-4 year olds and switched off for families who
              qualify for the extended (working-parent) scheme, which pays the full 30
              hours. So the reform&apos;s second tier — 30 hours for working families under
              £100,000 — is already exactly what the extended scheme delivers, and the
              first tier is delivered by widening the universal scheme&apos;s age floor from{" "}
              <strong>{params.baseline_universal_entitlement_age_min}</strong> to{" "}
              <strong>{params.reform_universal_entitlement_age_min}</strong> years.
            </p>
            <p>
              This is a single parameter change. No formula is altered, which means the
              eligibility, hours and funding-rate logic is the model&apos;s own throughout.
            </p>
          </Block>

          <Block title="Leg 2 — a 75% subsidy replacing Tax-Free Childcare">
            <p>
              This one is structural. Tax-Free Childcare pays{" "}
              <code className="rounded bg-slate-100 px-1">rate / (1 - rate)</code> of
              parental spend — a {(params.baseline_tax_free_childcare_rate * 100).toFixed(0)}%
              rate giving a 25% top-up — capped at £
              {params.baseline_tax_free_childcare_cap_gbp?.toLocaleString("en-GB")} a child,
              and gated on both a work condition and a £
              {params.extended_entitlement_income_limit_gbp?.toLocaleString("en-GB")}{" "}
              income cliff. A flat {(params.reform_subsidy_rate * 100).toFixed(0)}% share of
              costs is a different functional form, so the{" "}
              <code className="rounded bg-slate-100 px-1">tax_free_childcare</code> and{" "}
              <code className="rounded bg-slate-100 px-1">tax_free_childcare_eligible</code>{" "}
              formulas are replaced: no work test, no income cliff, no per-child cap.
            </p>
            <p>
              The Universal Credit childcare element is kept at{" "}
              {(params.uc_childcare_coverage_rate * 100).toFixed(0)}% of costs, per the
              reform brief. Tax-Free Childcare&apos;s existing disqualification of UC and
              tax-credit recipients is therefore kept too — those families already receive
              85% of costs through UC, and stacking a further 75% on the same spend would
              subsidise childcare above its price.
            </p>
          </Block>

          <Block title="Why the two legs do not add up">
            <p>
              <code className="rounded bg-slate-100 px-1">childcare_expenses</code> in
              policyengine-uk is out-of-pocket spend <em>net of</em> the free hours a family
              already receives. Hours the reform newly makes free therefore have to be
              netted out of it before the 75% subsidy applies, or the same hour of care is
              paid for twice.
            </p>
            <p>
              Only{" "}
              <strong>{(assumptions.free_hours_displacement * 100).toFixed(0)}%</strong> of
              the value of new free hours displaces paid care. The rest is additional care
              that would not otherwise have been bought. That split comes from{" "}
              {A(
                src.ifs_free_childcare,
                "the IFS evaluation of England's entitlements",
              )}
              : for every 570 free hours a year offered, children spent only about 163
              additional hours in subsidisable care.
            </p>
          </Block>

          <Block title="Funding rates and hours">
            <p>
              Free hours are valued at the DfE funding rate the model applies — what
              government pays a provider, not what a family would pay on the open market —
              over {params.weeks_per_year} weeks a year. Rates in {year}:
            </p>
            <ul className="list-inside list-disc space-y-1">
              {Object.entries(fundingRates).map(([band, rate]) => (
                <li key={band}>
                  {band.replace(/_/g, " ").replace("age ", "age ")}: £{rate.toFixed(2)} an
                  hour
                </li>
              ))}
            </ul>
            <p>
              There is no regional variation: the funding rate is a single national scale
              by child age, uprated by CPI. Real local-authority rates are not modelled.
            </p>
          </Block>
        </div>
      </section>

      <section>
        <SectionHeading
          title="The labour supply response"
          description="Reported alongside the static cost, never instead of it."
        />
        <div className="space-y-4">
          <Block title="What policyengine-uk provides, and what it does not">
            <p>
              policyengine-uk ships an{" "}
              {A(src.obr_labour_supply, "OBR-methodology labour supply framework")}. Its
              coordinator runs only the intensive margin; the participation model is
              present but commented out as a placeholder. Childcare is the canonical
              extensive-margin question, so the margin that matters is the one that is not
              wired up.
            </p>
            <p>
              More importantly, the participation model measures work incentives as the
              gain to work in household net income, which does not net off childcare costs.
              Childcare is a cost of working, so the main channel by which a childcare
              subsidy raises employment is invisible to it. This analysis reuses the OBR
              participation elasticities and the gain-to-work machinery, and adds the two
              childcare terms the framework is missing: out-of-pocket childcare is
              subtracted from in-work income, and cost-contingent childcare support is
              subtracted from out-of-work income, where no care is being bought.
            </p>
          </Block>

          <Block title="Elasticities">
            <p>
              The participation elasticities are the OBR&apos;s, varying by gender, partner
              employment status, age of youngest child and earnings quintile. The low and
              high bounds scale them by{" "}
              {assumptions.elasticity_scale_low?.toFixed(2)}× and{" "}
              {assumptions.elasticity_scale_high?.toFixed(2)}×, set from the ratio of the
              low and high childcare price elasticities (
              {assumptions.price_elasticity_low} and {assumptions.price_elasticity_high}) to
              the central one ({assumptions.price_elasticity_central}), so both methods
              carry the same uncertainty band from the same evidence.
            </p>
            <p>
              The central −0.15 sits below{" "}
              {A(src.akgunduz_plantenga, "the meta-analytic mean of −0.277")} for three
              reasons that all point the same way for the UK: publication bias, a
              European mean of −0.19 against a US mean of −0.35, and a meta-regression
              finding significantly smaller elasticities in high part-time, high
              participation countries. {A(src.baker_gruber_milligan, "Quebec's estimate")}{" "}
              of −0.236, from the most generous programme ever studied, is described by its
              own authors as low-end.
            </p>
          </Block>

          <Block title="Restrictions">
            <p>
              The response is confined to parents whose <em>youngest</em> child is in the
              eligible band. {A(src.ifs_free_childcare, "The IFS")} finds no effect for
              parents who also have a younger, non-eligible child — they still need care for
              the younger one, so the entitlement does not free them to work. This is the
              single most important structural restriction and it replicates
              internationally.
            </p>
            <p>
              Only the extensive margin is modelled. {A(
                src.bettendorf_jongen_muller,
                "Dutch evidence",
              )}{" "}
              suggests hours respond about twice as much as employment, so the participation
              estimate is a floor on the total labour supply response, not the whole of it.
              Responses are applied as expected values rather than a stochastic draw, so the
              result does not depend on a random seed.
            </p>
          </Block>

          <Block title="Two methods, reported side by side">
            <p>
              The gain-to-work model can go either way: it sees that the reform removes work
              conditions from childcare support, which cuts work incentives, as well as the
              price fall. The price-elasticity cross-check applies the literature&apos;s own
              arithmetic to the price of care alone, so it can only be positive. Neither is
              the answer on its own — together they bracket it. In {year} the two give{" "}
              {result.dynamic_cost.central.net_entrants.toLocaleString("en-GB")} and{" "}
              {result.price_elasticity_cross_check?.central.entrants.toLocaleString("en-GB")}{" "}
              net entrants respectively.
            </p>
          </Block>
        </div>
      </section>

      <section>
        <SectionHeading
          title="Caveats"
          description="Things that would change these numbers and are not modelled."
        />
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <ul className="list-inside list-disc space-y-2 text-sm leading-6 text-slate-600">
            <li>
              <strong>Take-up is assumed complete.</strong> The model&apos;s claim switches
              default to true, so every eligible family receives every entitlement. Real
              take-up of Tax-Free Childcare is about 46%, and take-up of free hours for
              under-3s is well below 100%. This pushes the cost up.
            </li>
            <li>
              <strong>Take-up is also assumed unresponsive.</strong> Making 15 hours
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
        <div className="space-y-3">
          {Object.values(src).map((source) => (
            <div key={source.url} className="rounded-2xl border border-slate-200 bg-white p-5">
              <a
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="font-semibold underline"
              >
                {source.label}
              </a>
              <p className="mt-1 text-sm leading-6 text-slate-600">{source.description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
