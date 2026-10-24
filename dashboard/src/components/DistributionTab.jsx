"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { colors } from "../lib/colors";
import { formatBn, formatCurrency, formatPct , formatFiscalYear} from "../lib/formatters";
import { ucCoverageRate } from "../lib/params";
import SectionHeading from "./SectionHeading";
import TabLink from "./TabLink";

const MEASURES = [
  {
    id: "average_gain_gbp",
    label: "Average change in net income per household",
    format: formatCurrency,
    unit: "£/year",
  },
  {
    id: "average_gain_gbp_among_gainers",
    label: "Average change in net income per household that gains",
    format: formatCurrency,
    unit: "£/year",
  },
  {
    id: "total_gain_bn",
    label: "Total change in net income",
    format: formatBn,
    unit: "£bn",
  },
  {
    id: "average_gain_pct_of_income",
    label: "Change as a share of net income",
    format: (value) => formatPct(value, 2),
    unit: "% of net income",
  },
];

const POPULATIONS = [
  {
    id: "by_income_decile_families_with_under_5s",
    label: "Income decile — families with a child under 5",
    grouping: "income decile",
  },
  { id: "by_income_decile", label: "Income decile — all households", grouping: "income decile" },
  {
    id: "by_income_quintile_families_with_under_5s",
    label: "Income quintile — families with a child under 5",
    grouping: "income quintile",
  },
  { id: "by_income_quintile", label: "Income quintile — all households", grouping: "income quintile" },
  {
    id: "by_family_type_families_with_under_5s",
    label: "Family type — families with a child under 5",
    grouping: "family type",
  },
  { id: "by_family_type", label: "Family type — all households", grouping: "family type" },
];

const LEGS = [
  { id: "combined", label: "Both legs together" },
  { id: "free_hours", label: "15 free hours for all, from 9 months" },
  { id: "subsidy", label: "75% subsidy replacing Tax-Free Childcare" },
];

export default function DistributionTab({ data, year, bound, intensive, area, onTabChange }) {
  const [measureId, setMeasureId] = useState("average_gain_gbp");
  const [populationId, setPopulationId] = useState(
    "by_income_decile_families_with_under_5s",
  );
  const [legId, setLegId] = useState("combined");

  const result = data.by_year[String(year)];
  // The distribution on the same behavioural assumption as the cost. The
  // participation response is an expected value per person — a probability of
  // entering or leaving work times the gain to work — so it allocates to
  // households and can be read by decile like any other income change.
  const leg = result.legs[legId];
  const isEngland = area === "england";
  const suffix = isEngland ? "_england" : "";
  const hasExtensive = Boolean(bound) && bound !== "none";
  const hasIntensive = Boolean(intensive);
  // Each combination of the two margins is a separate block in the results,
  // so switching one off returns exactly the figures published without it.
  const selectEffects = (block) =>
    hasExtensive
      ? block[`household_effects_by_bound${hasIntensive ? "_with_hours" : ""}${suffix}`][bound]
      : hasIntensive
        ? block[`household_effects_hours${suffix}`]
        : block[`household_effects${suffix}`];
  const effects = selectEffects(leg);
  const measure = MEASURES.find((m) => m.id === measureId);
  const population = POPULATIONS.find((p) => p.id === populationId);
  const rows = effects[populationId] || [];
  const headline = effects.families_with_under_5s;
  const all = effects.all_households;

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="Change in household net income"
          description={
            <>
              Change in net income by income decile, ranking all{" "}
              {isEngland ? "UK households (English households shown)" : "UK households"}, not only
              those with young children. Free hours are valued at the{" "}
              {onTabChange ? (
                <TabLink onSelect={() => onTabChange("methodology")}>DfE funding rate</TabLink>
              ) : (
                "DfE funding rate"
              )}
              .{" "}
              {hasExtensive || hasIntensive
                ? "Includes the labour supply response chosen above."
                : "Static: no labour supply response."}
            </>
          }
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <div className="text-sm text-slate-500">
              Households with a child under 5
            </div>
            <div className="mt-1 text-3xl font-semibold text-slate-900">
              {formatCurrency(headline.average_gain_gbp)}
            </div>
            <div className="mt-2 text-sm text-slate-500">
              average change in net income a year, across{" "}
              {headline.households_m.toFixed(2)}m households.{" "}
              {formatPct(headline.share_gaining * 100, 0)} of them see their net income rise.
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <div className="text-sm text-slate-500">Among those that gain</div>
            <div className="mt-1 text-3xl font-semibold text-slate-900">
              {formatCurrency(headline.average_gain_gbp_among_gainers)}
            </div>
            <div className="mt-2 text-sm text-slate-500">
              average change in net income a year for a household whose net income rises.
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <div className="text-sm text-slate-500">All households</div>
            <div className="mt-1 text-3xl font-semibold text-slate-900">
              {formatCurrency(all.average_gain_gbp)}
            </div>
            <div className="mt-2 text-sm text-slate-500">
              average change across all {all.households_m.toFixed(1)}m UK households, most of which
              have no young children.
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <div className="mb-5 grid gap-3 sm:grid-cols-3">
            <label className="min-w-0">
              <span className="mb-1 block text-xs font-medium text-slate-500">Reform</span>
              <select
                value={legId}
                onChange={(event) => setLegId(event.target.value)}
                className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)] focus:ring-2 focus:ring-[color:var(--pe-color-primary-100)]"
              >
                {LEGS.map((leg) => (
                  <option key={leg.id} value={leg.id}>
                    {leg.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="min-w-0">
              <span className="mb-1 block text-xs font-medium text-slate-500">
                Breakdown
              </span>
              <select
                value={populationId}
                onChange={(event) => setPopulationId(event.target.value)}
                className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)] focus:ring-2 focus:ring-[color:var(--pe-color-primary-100)]"
              >
                {POPULATIONS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="min-w-0">
              <span className="mb-1 block text-xs font-medium text-slate-500">Measure</span>
              <select
                value={measureId}
                onChange={(event) => setMeasureId(event.target.value)}
                className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)] focus:ring-2 focus:ring-[color:var(--pe-color-primary-100)]"
              >
                {MEASURES.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <h3 className="mb-4 text-sm font-semibold text-slate-700">
            {measure.label}, {population.label.charAt(0).toLowerCase() + population.label.slice(1)} (
            {measure.unit}, {formatFiscalYear(year)})
          </h3>
          {rows.length === 0 ? (
            <div className="flex h-[320px] items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-500">
              These results are not in this data file yet.
            </div>
          ) : (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={rows} margin={{ left: 8, right: 16, top: 8, bottom: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
              <XAxis
                dataKey="group"
                tick={{ fontSize: population?.grouping === "income decile" ? 11 : 12 }}
                interval={population?.grouping === "income decile" ? 0 : "preserveEnd"}
              />
              <YAxis tick={{ fontSize: 12 }} width={48} />
              <Tooltip formatter={(value) => measure.format(value)} />
              <Bar dataKey={measureId} radius={[4, 4, 0, 0]} isAnimationActive={false}>
                {rows.map((_, index) => (
                  <Cell key={index} fill={colors.primary[500]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          )}
          <p className="mt-4 text-sm leading-6 text-slate-500">
            {population?.grouping === "income decile" || population?.grouping === "income quintile"
              ? `${population.grouping === "income decile" ? "D1 is the lowest-income tenth" : "Q1 is the lowest-income fifth"}. In the model, lower-income households gain less in cash from the subsidy because UC already covers ${(ucCoverageRate(data) * 100).toFixed(0)}% of childcare costs and, in the data, they report fewer paid hours.`
              : null}
          </p>
        </div>
      </section>

    </div>
  );
}
