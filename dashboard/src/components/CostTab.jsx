"use client";

import { useState } from "react";
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
import { formatBn, formatCount } from "../lib/formatters";
import SectionHeading from "./SectionHeading";

function Stat({ label, value, sub, tone = "default" }) {
  const valueClass =
    tone === "negative" ? "text-slate-900" : "text-slate-900";
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-semibold ${valueClass}`}>{value}</div>
      {sub ? <div className="mt-2 text-sm leading-6 text-slate-500">{sub}</div> : null}
    </div>
  );
}

const LEG_LABELS = {
  free_hours: "15 free hours for all, from 9 months",
  subsidy: "75% subsidy replacing Tax-Free Childcare",
  combined: "Both legs together",
};

export default function CostTab({ data, year, onYearChange }) {
  const [bound, setBound] = useState("central");
  const result = data.by_year[String(year)];
  const legs = result.legs;
  const dynamic = result.dynamic_cost[bound];
  const response = result.labour_supply[bound];
  const priceCheck = result.price_elasticity_cross_check?.[bound];
  const src = data.sources || {};
  const A = (source, text) =>
    source ? (
      <a href={source.url} target="_blank" rel="noreferrer" className="underline">
        {text}
      </a>
    ) : (
      text
    );

  // The two legs do not sum to the combined cost: free hours displace paid
  // care, which shrinks the base the 75% subsidy applies to.
  const feeBase = result.fee_base_sensitivity;
  const cliff = data.income_cliff_context;
  const legSum = legs.free_hours.static_cost_bn + legs.subsidy.static_cost_bn;
  const interaction = legs.combined.static_cost_bn - legSum;

  const yearRows = data.years.map((y) => ({
    year: String(y),
    free_hours: data.by_year[String(y)].legs.free_hours.static_cost_bn,
    subsidy: data.by_year[String(y)].legs.subsidy.static_cost_bn,
    combined: data.by_year[String(y)].legs.combined.static_cost_bn,
    dynamic: data.by_year[String(y)].dynamic_cost[bound].dynamic_cost_bn,
  }));

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="Budget impact, 2027 to 2029"
          description={
            <>
              Both legs of the reform, costed on the PolicyEngine UK Enhanced FRS. The{" "}
              <strong>static</strong> cost holds behaviour fixed. The{" "}
              <strong>dynamic</strong> cost adds an extensive-margin labour supply response
              built on {A(src.obr_labour_supply, "the OBR's participation elasticities")},
              with childcare treated as a cost of working. Free hours are valued at the DfE
              funding rate the model applies; the subsidy at its cash value.
            </>
          }
        />
        <div className="mb-5 grid gap-3 sm:grid-cols-2">
          <label className="min-w-0">
            <span className="mb-1 block text-xs font-medium text-slate-500">Year</span>
            <select
              value={year}
              onChange={(event) => onYearChange(Number(event.target.value))}
              className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)] focus:ring-2 focus:ring-[color:var(--pe-color-primary-100)]"
            >
              {data.years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </label>
          <label className="min-w-0">
            <span className="mb-1 block text-xs font-medium text-slate-500">
              Labour supply assumption
            </span>
            <select
              value={bound}
              onChange={(event) => setBound(event.target.value)}
              className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)] focus:ring-2 focus:ring-[color:var(--pe-color-primary-100)]"
            >
              <option value="central">Central</option>
              <option value="low">Low response</option>
              <option value="high">High response</option>
            </select>
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Stat
            label={`Static cost, ${year}`}
            value={`${formatBn(feeBase.combined_cost_bn)} to ${formatBn(legs.combined.static_cost_bn)}`}
            sub={`Both legs, behaviour held fixed. The range is the childcare fee base: the model's England under-5 spend is ${feeBase.model_england_under_5_bn.toFixed(2)}bn against a ${feeBase.benchmark_england_under_5_bn.toFixed(2)}bn benchmark, and the subsidy is a share of that base. See Benchmarks.`}
          />
          <Stat
            label={`Cost with labour supply response, ${year}`}
            value={formatBn(dynamic.dynamic_cost_bn)}
            sub={`Labour supply changes the cost by ${formatBn(-dynamic.labour_supply_offset_bn)}.`}
          />
          <Stat
            label="Net change in employment"
            value={`${dynamic.net_entrants >= 0 ? "+" : "−"}${formatCount(
              Math.abs(dynamic.net_entrants),
            )}`}
            sub={`${formatCount(Math.abs(dynamic.net_ftes))} full-time equivalents, among ${response.responding_adults_m.toFixed(1)}m parents whose youngest child is in the eligible band.`}
          />
        </div>
      </section>

      <section>
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold tracking-tight text-slate-900">
            What is being costed
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Two changes, priced separately and together. Support is shown as it lands on a
            family, by where its income sits.
          </p>
          <dl className="mt-5 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-4">
              <dt className="text-sm font-semibold text-slate-900">
                Leg 1 — 15 free hours for everyone, plus 15 more for working parents
              </dt>
              <dd className="mt-2 text-sm leading-6 text-slate-600">
                Today: 15 hours for 3-4 year olds, and 30 hours where parents work and earn
                under £100,000. After: <strong>15 hours free for every child</strong> from 9
                months to school age, with no work or income test, and{" "}
                <strong>a further 15 hours</strong> where parents work and earn under
                £100,000. A non-working family gains 15 hours it does not have today; a
                working family under £100,000 keeps the 30 it already has.
              </dd>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <dt className="text-sm font-semibold text-slate-900">
                Leg 2 — a 75% subsidy replacing Tax-Free Childcare
              </dt>
              <dd className="mt-2 text-sm leading-6 text-slate-600">
                Today: Tax-Free Childcare tops up 25% of what a parent pays into an account,
                capped at £2,000 a child, with a work test and a £100,000 cliff. After:{" "}
                <strong>75% of childcare costs</strong>, uncapped, with no work test and no
                cliff — so it reaches above £100,000 too. Families on Universal Credit keep
                the <strong>85% childcare element</strong> instead, unchanged, rather than
                stacking the two.
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
              The two legs do not sum to the combined cost. Free hours displace paid care —{" "}
              {A(src.ifs_free_childcare, "about 71% of a new free offer")} replaces care
              families were already buying — which shrinks the base the 75% subsidy applies
              to. That interaction is worth {formatBn(Math.abs(interaction))} in {year}.
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
              <Bar
                dataKey="combined"
                name={LEG_LABELS.combined}
                fill={colors.primary[700]}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="py-2 pr-4 font-medium">Year</th>
                  <th className="py-2 pr-4 font-medium">Free hours</th>
                  <th className="py-2 pr-4 font-medium">75% subsidy</th>
                  <th className="py-2 pr-4 font-medium">Both, static</th>
                  <th className="py-2 pr-4 font-medium">Both, with labour supply</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {yearRows.map((row) => (
                  <tr key={row.year} className={String(year) === row.year ? "font-semibold" : ""}>
                    <td className="py-2 pr-4">{row.year}</td>
                    <td className="py-2 pr-4">{formatBn(row.free_hours)}</td>
                    <td className="py-2 pr-4">{formatBn(row.subsidy)}</td>
                    <td className="py-2 pr-4">{formatBn(row.combined)}</td>
                    <td className="py-2 pr-4">{formatBn(row.dynamic)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section>
        <SectionHeading
          title="Why the labour supply response is small, and which way it points"
          description={
            <>
              Two forces pull in opposite directions, and the model reports the net of
              them.
            </>
          }
        />
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-900">
              Downward: the reform removes work conditions
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Today a parent of a child under 3 gets nothing unless they work. Under the
              reform they get 15 hours whether they work or not, so the gain to work falls
              for exactly the families the policy targets. Working parents earning under
              £100,000 already get 30 hours, so their position is unchanged. This is a real
              effect, not a modelling artefact, and the gain-to-work model below captures
              it.
            </p>
            <dl className="mt-4 space-y-1 text-sm text-slate-600">
              <div className="flex justify-between">
                <dt>Modelled entrants</dt>
                <dd className="font-semibold">{formatCount(response.entrants)}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Modelled leavers</dt>
                <dd className="font-semibold">{formatCount(response.leavers)}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Net revenue effect</dt>
                <dd className="font-semibold">
                  {formatBn(response.net_revenue_gbp / 1e9)}
                </dd>
              </div>
            </dl>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-900">
              Upward: the price of childcare falls
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              The 75% subsidy cuts the price of the care that working requires. Applying{" "}
              {A(src.akgunduz_plantenga, "a childcare price elasticity of maternal employment")}{" "}
              to that price fall, scaled by{" "}
              {A(src.ifs_free_childcare, "29% additionality")}, gives an upper bound on the
              positive channel on its own. It cannot be negative by construction, so it
              brackets the answer from the other side rather than confirming it.
            </p>
            {priceCheck ? (
              <dl className="mt-4 space-y-1 text-sm text-slate-600">
                <div className="flex justify-between">
                  <dt>Price elasticity used</dt>
                  <dd className="font-semibold">{priceCheck.price_elasticity}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Effective price change</dt>
                  <dd className="font-semibold">
                    {(priceCheck.effective_price_change * 100).toFixed(1)}%
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Implied entrants</dt>
                  <dd className="font-semibold">{formatCount(priceCheck.entrants)}</dd>
                </div>
              </dl>
            ) : null}
          </div>
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-600">
          For scale: {A(src.ifs_free_childcare, "the IFS")} found the move from 15 to 30
          hours put about 12,000 more mothers into work a year, and the government&apos;s own
          costing of the 2023 expansion assumed about 60,000 entrants by 2027-28 on a
          plausible range of 55,000 to 240,000. Both are policies that{" "}
          <em>added</em> work-conditional hours. This reform does the opposite: it makes
          existing hours unconditional.
        </p>
      </section>
      {cliff ? (
        <section>
          <SectionHeading
            title="The £100,000 cliff the reform half-removes"
            description="The reform makes the first 15 hours unconditional but keeps the work and income test on the second 15, so the cliff shrinks rather than disappears."
          />
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <dl className="grid gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-sm text-slate-500">Threshold, frozen since {cliff.frozen_since}</dt>
                <dd className="mt-1 text-2xl font-semibold text-slate-900">
                  £{cliff.threshold_gbp.toLocaleString("en-GB")}
                </dd>
                <dd className="mt-1 text-sm text-slate-500">
                  £{cliff.inflation_indexed_equivalent_gbp.toLocaleString("en-GB")} if it had
                  been indexed.
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-500">Children above it</dt>
                <dd className="mt-1 text-2xl font-semibold text-slate-900">
                  {cliff.children_affected}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-500">Support forgone</dt>
                <dd className="mt-1 text-2xl font-semibold text-slate-900">
                  {formatBn(cliff.support_forgone_bn)}
                </dd>
              </div>
            </dl>
            <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600">{cliff.note}</p>
          </div>
        </section>
      ) : null}
    </div>
  );
}
