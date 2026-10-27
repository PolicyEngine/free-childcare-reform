"use client";

import { formatBn } from "../lib/formatters";

import { displacementShare } from "../lib/params";
import SectionHeading from "./SectionHeading";

function Block({ title, children }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      {title ? <h3 className="mb-3 text-base font-semibold text-slate-900">{title}</h3> : null}
      <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">{children}</ul>
    </div>
  );
}

// First sentence of a source description, used as its one-line scope. The
// text itself comes from the results JSON and is not edited here.
function splitDescription(description = "") {
  const match = description.match(/^(.+?[.;])\s+(?=[A-Z])/);
  return match
    ? [match[1], description.slice(match[0].length)]
    : [description, ""];
}

// Age in years as plain English: 3 -> "3 years", 0.75 -> "9 months".
function ageLabel(years) {
  const value = Number(years);
  return Number.isInteger(value) ? `${value} years` : `${Math.round(value * 12)} months`;
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
  const pct = (share) => `${(share * 100).toFixed(0)}%`;

  // Realised displacement: the fall in modelled childcare spending in the
  // combined run, as a share of the free-hours leg's static cost (UK).
  const realisedDisplacementPct =
    ((result.baseline_spending.childcare_expenses_bn -
      result.legs.combined.spending.childcare_expenses_bn) /
      result.legs.free_hours.static_cost_bn) *
    100;

  // Implied price elasticity of the central run (by_year[year].
  // implied_price_elasticity.subsidy_leg). Shown only once the pipeline emits it.
  const impliedElasticity = result.implied_price_elasticity?.subsidy_leg;
  const takeUp = result.free_hours_take_up?.cases;

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="The two legs"
          description="Model parameters on this tab are read from the simulation."
        />
        <Block>
          <li>
            <strong>Free hours.</strong> The universal age floor is widened from{" "}
            {ageLabel(params.baseline_universal_entitlement_age_min)} to{" "}
            {ageLabel(params.reform_universal_entitlement_age_min)}, starting the
            term after the child reaches that age. The working-parent scheme still adds
            hours up to 30. Families claiming the disadvantaged 2-year-old offer are
            excluded, so they get 15 hours, not 30.
          </li>
          {takeUp ? (
            <li>
              <strong>Take-up of the new hours.</strong> Families already on the
              working-parent hours keep their current take-up. Other families take up the
              new hours at the 2-year-old offer&apos;s rate (
              {(takeUp.central.take_up_rate_outside_working_parent_hours * 100).toFixed(0)}%
              in the model); no 15-hour offer for under-3s outside work exists today to
              calibrate it. The Reform tab shows the range this gives, from{" "}
              {(takeUp.low.take_up_rate_outside_working_parent_hours * 100).toFixed(0)}% to{" "}
              {(takeUp.high.take_up_rate_outside_working_parent_hours * 100).toFixed(0)}%.
            </li>
          ) : null}
          <li>
            <strong>Subsidy.</strong> Tax-Free Childcare is replaced by{" "}
            {(params.reform_subsidy_rate * 100).toFixed(0)}% of childcare costs, with no
            cap, work test or income cliff. The Universal Credit childcare element is kept.
          </li>
          <li>
            <strong>Not additive.</strong> In the model, new free hours displace paid care:{" "}
            {pct(displacementShare(data))} of them replace care a family already buys, but
            displacement cannot exceed what a family spends, so realised displacement is
            about {realisedDisplacementPct.toFixed(0)}%.
          </li>
          <li>
            <strong>Valuation.</strong> Free hours are valued at the DfE funding rate, not
            the market price.
          </li>
        </Block>
      </section>

      <section>
        <SectionHeading
          title="Labour supply"
          description="Reported alongside the static cost, and can be switched off on the Reform tab."
        />
        <Block>
          <li>
            <strong>Participation.</strong> In the model, parents respond to the change in
            their gain to work, using the{" "}
            {A(src.obr_labour_supply, "OBR elasticities")} by gender, partner, youngest
            child&apos;s age and earnings quintile. Only parents whose youngest child is
            eligible respond.
          </li>
          <li>
            The central case uses the OBR elasticities as published; the low and high cases
            scale them by {assumptions.elasticity_scale_low?.toFixed(2)}× and{" "}
            {assumptions.elasticity_scale_high?.toFixed(2)}×.
            {impliedElasticity !== undefined && impliedElasticity !== null ? (
              <>
                {" "}
                For the subsidy leg, the central response amounts to a childcare price
                elasticity of employment of {impliedElasticity.toFixed(3)}.
              </>
            ) : null}
          </li>
          <li>
            <strong>Hours.</strong> Parents in work who pay for childcare change their hours
            with an elasticity of {assumptions.hours_price_elasticity}, from{" "}
            {A(src.brewer_hours, "Brewer et al.")} That figure already includes people
            moving into work, so it overlaps with participation and the two are not added.
          </li>
        </Block>
      </section>

      <section>
        <SectionHeading title="Caveats" description="Not modelled, and would change the numbers." />
        <Block>
          <li>
            The 9-month floor follows date of birth, but the labour supply response uses
            whole-year ages, so it leaves out parents whose youngest child is aged 0.
          </li>
          <li>Participation elasticities are read at 2025 for every costed year.</li>
          <li>
            The Baseline tab compares the model with each published figure at the year that
            figure covers, not the costed year, so the gap measures the model rather than
            the time between two dates.
          </li>
          <li>
            Apart from the new free hours, take-up is held at baseline rates, with no
            take-up response from families who use no formal childcare today.
          </li>
          <li>No provider capacity constraint is modelled, and fees are held fixed.</li>
          {result.fee_base_sensitivity ? (
            <li>
              The fee base is the main uncertainty for the subsidy leg. The model has{" "}
              {formatBn(result.fee_base_sensitivity.model_england_under_5_bn)} of under-5 fees
              in England against about{" "}
              {formatBn(result.fee_base_sensitivity.benchmark_england_under_5_bn)} from CMA
              figures; scaling to that would take the subsidy leg from{" "}
              {formatBn(result.legs.subsidy.static_cost_bn)} to{" "}
              {formatBn(result.fee_base_sensitivity.subsidy_cost_bn)}.
            </li>
          ) : null}
          <li>
            Household figures and the labour supply response carry statistical noise: each
            survey household&apos;s change is scaled by a fixed factor 8-12% from 1, so the
            households behind a small group cannot be identified. Static costs are exact. A
            figure resting on one or two survey households is withheld.
          </li>
          <li>
            Early years is devolved: there is no UK free-hours figure, and Barnett
            consequentials are not costed.
          </li>
          <li>
            Where providers charge above the funding rate, a family&apos;s gain may be
            larger than shown.
          </li>
          <li>No macro feedback: labour demand absorbs the extra hours at current wages.</li>
        </Block>
      </section>

      <section>
        <SectionHeading title="Sources" />
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <ul className="space-y-3">
            {Object.values(src).map((source) => {
              const [scope, rest] = splitDescription(source.description);
              return (
                <li key={source.url} className="text-sm leading-6 text-slate-600">
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold text-slate-900 underline [overflow-wrap:anywhere]"
                  >
                    {source.label}
                  </a>
                  <div>{scope}</div>
                  {rest ? (
                    <details>
                      <summary className="cursor-pointer text-xs text-slate-500">More</summary>
                      <p className="mt-1">{rest}</p>
                    </details>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      </section>
    </div>
  );
}
