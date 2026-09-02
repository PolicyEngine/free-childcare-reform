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
import SectionHeading from "./SectionHeading";

const MEASURES = [
  {
    id: "average_gain_gbp",
    label: "Average gain per household",
    format: formatCurrency,
    unit: "£/year",
  },
  {
    id: "average_gain_gbp_among_gainers",
    label: "Average gain per gaining household",
    format: formatCurrency,
    unit: "£/year",
  },
  {
    id: "total_gain_bn",
    label: "Total gain",
    format: formatBn,
    unit: "£bn",
  },
  {
    id: "average_gain_pct_of_income",
    label: "Gain as a share of net income",
    format: (value) => formatPct(value, 2),
    unit: "% of net income",
  },
];

const POPULATIONS = [
  {
    id: "by_income_quintile_families_with_under_5s",
    label: "Income quintile — families with a child under 5",
    grouping: "quintile",
  },
  { id: "by_income_quintile", label: "Income quintile — all households", grouping: "quintile" },
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

export default function DistributionTab({ data, year, bound, area }) {
  const [measureId, setMeasureId] = useState("average_gain_gbp");
  const [populationId, setPopulationId] = useState(
    "by_income_quintile_families_with_under_5s",
  );
  const [legId, setLegId] = useState("combined");

  const result = data.by_year[String(year)];
  // The distribution on the same behavioural assumption as the cost. The
  // participation response is an expected value per person — a probability of
  // entering or leaving work times the gain to work — so it allocates to
  // households and can be read by quintile like any other income change.
  const leg = result.legs[legId];
  const isEngland = area === "england";
  const dynamicKey = isEngland ? "household_effects_by_bound_england" : "household_effects_by_bound";
  const staticKey = isEngland ? "household_effects_england" : "household_effects";
  const effects =
    bound && bound !== "none" && leg[dynamicKey]?.[bound]
      ? leg[dynamicKey][bound]
      : leg[staticKey];
  const measure = MEASURES.find((m) => m.id === measureId);
  const population = POPULATIONS.find((p) => p.id === populationId);
  const rows = effects[populationId] || [];
  const headline = effects.families_with_under_5s;
  const all = effects.all_households;

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="Who gains, and by how much"
          description={
            <>
              The change in household net income, by income quintile.{" "}
              {isEngland
                ? "Restricted to English households, which is the population the free entitlements reach. Quintiles remain the UK ranking, so an English household sits where it sits nationally. "
                : "Households are UK-wide, but the two legs are not: the free entitlements are England-only, so households in Scotland, Wales and Northern Ireland are ranked and counted here while gaining nothing from that leg. Switch the area above to see England alone. "}
              Quintiles fold
              PolicyEngine&apos;s published household income deciles, so they rank all
              households in the UK — not only those with young children. Free childcare
              hours are counted at the DfE funding rate the model applies, which is what
              the government pays a provider, not what a family would have paid on the open
              market.{" "}
              {bound && bound !== "none"
                ? "These figures include the labour supply response at the assumption chosen above, on both margins: each person's expected change in net income from entering or leaving work, and the net gain from parents in work adding hours as childcare gets cheaper, are added to their household's gain. The participation part falls mostly on the bottom quintile, where the entrants are; the hours part on working families paying for childcare, which sit higher up."
                : "These figures are static. Choosing a labour supply assumption above adds each person's expected gain from entering or leaving work."}
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
              average gain a year, across {headline.households_m.toFixed(2)}m households.{" "}
              {formatPct(headline.share_gaining * 100, 0)} of them gain anything.
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <div className="text-sm text-slate-500">Among those that gain</div>
            <div className="mt-1 text-3xl font-semibold text-slate-900">
              {formatCurrency(headline.average_gain_gbp_among_gainers)}
            </div>
            <div className="mt-2 text-sm text-slate-500">
              average gain a year for a household that gains at all.
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <div className="text-sm text-slate-500">All households</div>
            <div className="mt-1 text-3xl font-semibold text-slate-900">
              {formatCurrency(all.average_gain_gbp)}
            </div>
            <div className="mt-2 text-sm text-slate-500">
              average across all {all.households_m.toFixed(1)}m UK households, most of which
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
            {measure.label} by {population.grouping} — {population.label.toLowerCase()} (
            {measure.unit}, {formatFiscalYear(year)})
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={rows} margin={{ left: 8, right: 16, top: 8, bottom: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
              <XAxis dataKey="group" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value) => measure.format(value)} />
              <Bar dataKey={measureId} radius={[4, 4, 0, 0]}>
                {rows.map((_, index) => (
                  <Cell key={index} fill={colors.primary[500]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="mt-4 text-sm leading-6 text-slate-500">
            {population?.grouping === "quintile"
            ? "Q1 is the lowest-income fifth of households. Lower quintiles gain less in cash because families on Universal Credit already receive 85% of childcare costs through the UC childcare element, which this reform keeps unchanged, and because low-income families use fewer paid childcare hours to begin with. As a share of net income the picture is different — switch the measure above."
: null}
          </p>
        </div>
      </section>

    </div>
  );
}
