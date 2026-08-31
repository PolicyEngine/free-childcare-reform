"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
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

function Stat({ label, value, sub, footnote }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-3xl font-semibold text-slate-900">{value}</div>
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
    `Central: the OBR participation elasticities as published, matching a childcare price elasticity of ${a.price_elasticity_central}.`,
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
  // Each panel below describes one leg's channel, so it must show that leg's
  // own response rather than the response to both legs together.
  const freeHoursResponse = isStatic ? null : legs.free_hours.labour_supply[bound];
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
                : `Static ${formatBn(legs.free_hours.static_cost_bn)}, plus ${formatSignedBn(-legs.free_hours.dynamic_cost[bound].labour_supply_offset_bn)} of labour supply on ${formatCount(legs.free_hours.dynamic_cost[bound].net_entrants)} net entrants. Unconditional hours remove a reason to work, so this leg costs more.`
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
                : `Static ${formatBn(legs.subsidy.static_cost_bn)}, plus ${formatSignedBn(-legs.subsidy.dynamic_cost[bound].labour_supply_offset_bn)} of labour supply on ${formatCount(legs.subsidy.dynamic_cost[bound].net_entrants)} net entrants. Cheaper childcare makes work pay, so this leg costs less.`
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
              )} net entrants among ${response.responding_adults_m.toFixed(1)}m eligible parents. The legs pull against each other — free hours remove a work condition, the subsidy cuts the price of working — so this is not their sum, and the net sign depends on which dominates. At ${(
                dynamic.offset_share_of_static_cost * 100
              ).toFixed(1)}% of the static cost, small on every assumption.`}
              footnote={
                <>
                  {BOUND_NOTES[bound]?.(assumptions)}{" "}
                  {A(src.obr_labour_supply, "OBR participation elasticities")}
                  {src.akgunduz_plantenga ? (
                    <>
                      {" · "}
                      {A(src.akgunduz_plantenga, "price elasticity evidence")}
                    </>
                  ) : null}
                </>
              }
            />
          )}
        </div>
      </section>

      <section>
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold tracking-tight text-slate-900">
            What is being costed
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
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
              added together: free hours displace paid care, so running both at once costs
              less than the sum of the two. The assumption is that{" "}
              {A(src.ifs_free_childcare, "90% of a new free offer")} replaces care a family
              was already buying, but displacement is capped at what they actually spend,
              and that cap binds — most newly-eligible families are not working and buy
              little paid care, so modelled childcare spending falls by only about 12% of
              the value of the new free hours.
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
            <p className="mt-2 text-sm leading-6 text-slate-600">
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
                      On the free-hours leg alone:{" "}
                      <strong>{formatCount(freeHoursResponse.entrants)}</strong> entrants
                      against <strong>{formatCount(freeHoursResponse.leavers)}</strong>{" "}
                      leavers, a net revenue effect of{" "}
                      <strong>
                        {formatSignedBn(freeHoursResponse.net_revenue_gbp / 1e9)}
                      </strong>
                      .
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
                      The 75% subsidy cuts the price of the care that working requires, so
                      the gain to work rises for parents who would be paying for childcare.
                    </li>
                    <li>
                      This is the channel that produces the subsidy leg&apos;s{" "}
                      <strong>
                        {formatCount(result.legs.subsidy.dynamic_cost[bound].net_entrants)}
                      </strong>{" "}
                      net entrants.
                    </li>
                  </ul>
                </dd>
              </div>
            </dl>
          </div>
        </section>
      )}

    </div>
  );
}
