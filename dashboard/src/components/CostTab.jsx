"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { colors } from "../lib/colors";
import {
  formatBn,
  formatCount,
  formatFiscalYear,
  formatSignedBn,
} from "../lib/formatters";
import SectionHeading from "./SectionHeading";

function Stat({ label, value, sub, footnote, tone = "default" }) {
  const valueClass =
    tone === "negative" ? "text-slate-900" : "text-slate-900";
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-semibold ${valueClass}`}>{value}</div>
      {sub ? <div className="mt-2 text-sm leading-6 text-slate-500">{sub}</div> : null}
      {footnote ? (
        <div className="mt-3 border-t border-slate-100 pt-2 text-xs leading-5 text-slate-500">
          {footnote}
        </div>
      ) : null}
    </div>
  );
}

// What each labour supply assumption actually is, in the reader's view.
const BOUND_NOTES = {
  central: (a) =>
    `Central: the OBR participation elasticities as published, with a childcare price elasticity of ${a.price_elasticity_central} for the cross-check.`,
  low: (a) =>
    `Low: OBR elasticities scaled by ${a.elasticity_scale_low?.toFixed(2)}×, the ratio of a ${a.price_elasticity_low} price elasticity to the central ${a.price_elasticity_central}.`,
  high: (a) =>
    `High: OBR elasticities scaled by ${a.elasticity_scale_high?.toFixed(2)}×, the ratio of a ${a.price_elasticity_high} price elasticity to the central ${a.price_elasticity_central}.`,
};

const LEG_LABELS = {
  free_hours: "15 free hours for all, from 9 months",
  subsidy: "75% subsidy replacing Tax-Free Childcare",
};

export default function CostTab({ data, year, bound }) {
  const result = data.by_year[String(year)];
  const legs = result.legs;
  const isStatic = bound === "none";
  const dynamic = isStatic ? null : result.dynamic_cost[bound];
  const response = isStatic ? null : result.labour_supply[bound];
  const priceCheck = isStatic ? null : result.price_elasticity_cross_check?.[bound];
  const src = data.sources || {};
  const A = (source, text) =>
    source ? (
      <a href={source.url} target="_blank" rel="noreferrer" className="underline">
        {text}
      </a>
    ) : (
      text
    );

  const assumptions = data.assumptions || {};
  const feeBase = result.fee_base_sensitivity;
  const cliff = data.income_cliff_context;

  const yearRows = data.years.map((y) => ({
    year: formatFiscalYear(y),
    free_hours: data.by_year[String(y)].legs.free_hours.static_cost_bn,
    subsidy: data.by_year[String(y)].legs.subsidy.static_cost_bn,
  }));

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title={`Budget impact, ${formatFiscalYear(data.years[0])} to ${formatFiscalYear(data.years[data.years.length - 1])}`}
          description={
            <>
              Each leg of the reform costed against the current system, on the PolicyEngine
              UK Enhanced FRS. They are shown separately and should not be added: free
              hours displace paid care, so running both at once costs less than the sum.
              The costs below hold behaviour fixed; choosing a labour supply assumption
              adds an extensive-margin response built on{" "}
              {A(src.obr_labour_supply, "the OBR's participation elasticities")}, with
              childcare treated as a cost of working. Free hours are valued at the DfE
              funding rate the model applies; the subsidy at its cash value.
            </>
          }
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Stat
            label={`Free hours, ${formatFiscalYear(year)}`}
            value={formatBn(
              isStatic
                ? legs.free_hours.static_cost_bn
                : legs.free_hours.dynamic_cost[bound].dynamic_cost_bn,
            )}
            sub={
              isStatic
                ? "15 hours for every child from 9 months, plus 15 more where parents work and earn under £100,000."
                : `15 hours for every child from 9 months, plus 15 more where parents work and earn under £100,000. Static ${formatBn(legs.free_hours.static_cost_bn)}; labour supply ${formatSignedBn(-legs.free_hours.dynamic_cost[bound].labour_supply_offset_bn)} on ${legs.free_hours.dynamic_cost[bound].net_entrants.toLocaleString("en-GB")} net entrants — making 15 hours unconditional removes a reason to work, so this leg costs more once behaviour moves.`
            }
          />
          <Stat
            label={`75% subsidy, ${formatFiscalYear(year)}`}
            value={formatBn(
              isStatic
                ? legs.subsidy.static_cost_bn
                : legs.subsidy.dynamic_cost[bound].dynamic_cost_bn,
            )}
            sub={
              isStatic
                ? `Replacing Tax-Free Childcare. On the published fee base this is ${formatBn(feeBase.subsidy_cost_bn)} — see Baseline.`
                : `Replacing Tax-Free Childcare. Static ${formatBn(legs.subsidy.static_cost_bn)}; labour supply ${formatSignedBn(-legs.subsidy.dynamic_cost[bound].labour_supply_offset_bn)} on ${legs.subsidy.dynamic_cost[bound].net_entrants.toLocaleString("en-GB")} net entrants — cutting the price of childcare makes work pay, so this leg costs less.`
            }
          />
          {isStatic ? (
            <Stat
              label="Behavioural response"
              value="None"
              sub="Static costing: nobody changes their hours or whether they work. Choose a response above to add an extensive-margin labour supply effect."
            />
          ) : (
            <Stat
              label="Labour supply, both legs together"
              value={formatSignedBn(-dynamic.labour_supply_offset_bn)}
              sub={`${dynamic.net_entrants >= 0 ? "+" : "−"}${formatCount(
                Math.abs(dynamic.net_entrants),
              )} net entrants (${formatCount(
                Math.abs(dynamic.net_ftes),
              )} full-time equivalents), among ${response.responding_adults_m.toFixed(1)}m parents whose youngest child is eligible. The two legs pull against each other — free hours remove a work condition, the subsidy cuts the price of working — so this is not the sum of the two figures above. At ${(
                dynamic.offset_share_of_static_cost * 100
              ).toFixed(1)}% of the static cost the effect is small on every assumption.`}
              footnote={BOUND_NOTES[bound]?.(assumptions)}
            />
          )}
        </div>
      </section>

      <section>
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold tracking-tight text-slate-900">
            What is being costed
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Two changes, priced separately and never added together. Support is shown as
            it lands on a family, by where its income sits.
          </p>
          <dl className="mt-5 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-4">
              <dt className="text-sm font-semibold text-slate-900">
                Leg 1 — 15 free hours for everyone, plus 15 more for working parents
              </dt>
              <dd className="mt-2 text-sm leading-6 text-slate-600">
                <ul className="list-disc space-y-1 pl-5">
                  <li>Today: 15 hours for 3-4 year olds; 30 where parents work and earn under £100,000.</li>
                  <li>
                    After: <strong>15 hours for every child</strong> from 9 months to school
                    age, no work or income test.
                  </li>
                  <li>
                    Plus <strong>a further 15 hours</strong> where parents work and earn
                    under £100,000.
                  </li>
                  <li>
                    So a non-working family gains 15 hours; a working family under £100,000
                    keeps the 30 it has.
                  </li>
                </ul>
              </dd>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <dt className="text-sm font-semibold text-slate-900">
                Leg 2 — a 75% subsidy replacing Tax-Free Childcare
              </dt>
              <dd className="mt-2 text-sm leading-6 text-slate-600">
                <ul className="list-disc space-y-1 pl-5">
                  <li>
                    Today: Tax-Free Childcare tops up 25% of what a parent pays into an
                    account, capped at £2,000 a child, with a work test and a £100,000 cliff.
                  </li>
                  <li>
                    After: <strong>75% of childcare costs</strong>, uncapped, no work test,
                    no cliff — so it reaches above £100,000 too.
                  </li>
                  <li>
                    Families on Universal Credit keep the{" "}
                    <strong>85% childcare element</strong> instead, unchanged, rather than
                    stacking the two.
                  </li>
                </ul>
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section>
        <SectionHeading
          title="Cost by year and by leg"
          description={
            <>
              Each leg on its own, against the current system. They are deliberately not
              added together: free hours displace paid care —{" "}
              {A(src.ifs_free_childcare, "about 71% of a new free offer")} replaces care
              families were already buying — so running both at once costs less than the
              sum of the two, and adding these figures would overstate it.
            </>
          }
        />
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={yearRows} margin={{ left: 8, right: 16, top: 8, bottom: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} unit="bn" />
              <Tooltip formatter={(value) => formatBn(value)} />
              <Legend />
              <Bar
                dataKey="free_hours"
                name={LEG_LABELS.free_hours}
                fill={colors.primary[300]}
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="subsidy"
                name={LEG_LABELS.subsidy}
                fill={colors.primary[500]}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {isStatic ? null : (
        <section>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">
              What moves employment, and in which direction
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Two forces pull against each other. The reported response is the net of
              them, which is why it is small.
            </p>
            <dl className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4">
                <dt className="text-sm font-semibold text-slate-900">
                  Downward — the reform removes work conditions
                </dt>
                <dd className="mt-2 text-sm leading-6 text-slate-600">
                  <ul className="list-disc space-y-1 pl-5">
                    <li>
                      Today a parent of a child under 3 gets nothing unless they work.
                    </li>
                    <li>
                      Under the reform they get 15 hours either way, so the gain to work
                      falls for exactly the families the policy targets.
                    </li>
                    <li>
                      Working parents under £100,000 already get 30 hours, so their
                      position is unchanged.
                    </li>
                    <li>
                      Modelled: <strong>{formatCount(response.entrants)}</strong> entrants
                      against <strong>{formatCount(response.leavers)}</strong> leavers, a
                      net revenue effect of{" "}
                      <strong>{formatBn(response.net_revenue_gbp / 1e9)}</strong>.
                    </li>
                  </ul>
                </dd>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <dt className="text-sm font-semibold text-slate-900">
                  Upward — the price of childcare falls
                </dt>
                <dd className="mt-2 text-sm leading-6 text-slate-600">
                  <ul className="list-disc space-y-1 pl-5">
                    <li>
                      The 75% subsidy cuts the price of the care that working requires.
                    </li>
                    <li>
                      Applying{" "}
                      {A(
                        src.akgunduz_plantenga,
                        "a childcare price elasticity of maternal employment",
                      )}{" "}
                      to that price fall, scaled by{" "}
                      {A(src.ifs_free_childcare, "29% additionality")}, brackets the
                      positive channel on its own — it cannot be negative by construction.
                    </li>
                    {priceCheck ? (
                      <li>
                        Elasticity <strong>{priceCheck.price_elasticity}</strong>, effective
                        price change{" "}
                        <strong>
                          {(priceCheck.effective_price_change * 100).toFixed(1)}%
                        </strong>
                        , implying <strong>{formatCount(priceCheck.entrants)}</strong>{" "}
                        entrants.
                      </li>
                    ) : null}
                  </ul>
                </dd>
              </div>
            </dl>
          </div>
        </section>
      )}

      {cliff ? (
        <section>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">
              The £100,000 cliff, half-removed
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              The first 15 hours become unconditional, but the work and income test stays
              on the second 15. So the cliff gets smaller — it does not go away.
            </p>
            <dl className="mt-5 grid gap-6 sm:grid-cols-3">
              <div>
                <dt className="text-sm text-slate-500">
                  Threshold, frozen since {cliff.frozen_since}
                </dt>
                <dd className="mt-1 text-3xl font-semibold text-slate-900">
                  £{cliff.threshold_gbp.toLocaleString("en-GB")}
                </dd>
                <dd className="mt-1 text-sm text-slate-500">
                  £{cliff.inflation_indexed_equivalent_gbp.toLocaleString("en-GB")} had it
                  been indexed.
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-500">Children in families above it</dt>
                <dd className="mt-1 text-3xl font-semibold text-slate-900">
                  {cliff.children_affected}
                </dd>
                <dd className="mt-1 text-sm text-slate-500">
                  England, 2025-26, from DfE estimates released under FOI.
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-500">Support they cannot claim</dt>
                <dd className="mt-1 text-3xl font-semibold text-slate-900">
                  {formatBn(cliff.support_forgone_bn)}
                </dd>
                <dd className="mt-1 text-sm text-slate-500">
                  A two-child family loses nearly £30,000 of support on crossing the
                  threshold.
                </dd>
              </div>
            </dl>
            <p className="mt-5 max-w-3xl text-sm leading-6 text-slate-600">
              Because the loss is a cliff rather than a taper, a two-child family earning
              £99,000 needs about <strong>£156,000</strong> of gross income to get back to
              the same disposable income once it crosses. This reform removes the test from
              the first 15 hours, which cuts the size of the step; keeping it on the second
              15 means a step remains.
            </p>
          </div>
        </section>
      ) : null}
    </div>
  );
}
