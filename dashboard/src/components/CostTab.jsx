"use client";

import { useState } from "react";
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
  formatSignedCount,
  formatSignedPct,
} from "../lib/formatters";
import { tfcCapGbp, tfcTopUpRate, ucCoverageRate } from "../lib/params";
import SectionHeading from "./SectionHeading";
import TabLink from "./TabLink";

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

// What each labour supply assumption is, in the reader's view.
const BOUND_NOTES = {
  central: () => "Central: OBR elasticities as published",
  low: (a) => `Low: OBR elasticities × ${a.elasticity_scale_low?.toFixed(2)}`,
  high: (a) => `High: OBR elasticities × ${a.elasticity_scale_high?.toFixed(2)}`,
};

const LEG_LABELS = {
  free_hours: "15 free hours for all, from 9 months",
  subsidy: "75% subsidy replacing Tax-Free Childcare",
  combined: "Both legs together",
  combined_free_hours: "Free hours",
  combined_subsidy: "Subsidy, added on top of free hours",
};

const CHART_SERIES = [
  { id: "each", label: "Each leg, side by side", bars: ["free_hours", "subsidy"] },
  { id: "free_hours", label: "Free hours only", bars: ["free_hours"] },
  { id: "subsidy", label: "Subsidy only", bars: ["subsidy"] },
  {
    id: "combined",
    label: "Both legs together",
    bars: ["combined_free_hours", "combined_subsidy"],
    stacked: true,
  },
];

const BAR_FILL = { free_hours: 300, subsidy: 500, combined_free_hours: 300, combined_subsidy: 500 };

export default function CostTab({ data, year, bound, intensive, area, onTabChange }) {
  const [seriesId, setSeriesId] = useState("each");
  const series = CHART_SERIES.find((option) => option.id === seriesId);
  const isEngland = area === "england";
  const areaLabel = isEngland ? ", England" : ", UK";
  const result = data.by_year[String(year)];
  const legs = result.legs;
  // The two margins switch on independently. The extensive margin carries the
  // low/central/high elasticity; the intensive margin has one setting and is
  // always read at the central scale.
  const hasExtensive = bound !== "none";
  const hasIntensive = Boolean(intensive);
  const isStatic = !hasExtensive && !hasIntensive;
  const HOURS_BOUND = "central";
  // Each panel below describes one leg's channel, so it must show that leg's
  // own response rather than the response to both legs together.
  const goTo = (tab, text) =>
    onTabChange ? <TabLink onSelect={() => onTabChange(tab)}>{text}</TabLink> : text;
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
  const byCountry = result.subsidy_by_country;
  // One accessor for every figure, so the Area and labour supply controls
  // always select the same view. A country's dynamic cost is its static cost
  // less its own net revenue — the dynamic_cost block's offset is UK-wide and
  // would otherwise be applied to an England denominator.
  const participationBound = hasExtensive ? bound : "central";
  const legResponse = (block, leg) =>
    isEngland
      ? block.legs[leg].labour_supply[participationBound].by_country.england
      : block.legs[leg].labour_supply[participationBound];
  // The intensive margin — parents in work changing their hours — on the same view.
  const legHours = (block, leg) =>
    isEngland
      ? block.legs[leg].hours_response[HOURS_BOUND].by_country.england
      : block.legs[leg].hours_response[HOURS_BOUND];
  const legParticipationOffset = (block, leg) =>
    hasExtensive ? legResponse(block, leg).net_revenue_gbp / 1e9 : 0;
  const legHoursOffset = (block, leg) => (hasIntensive ? legHours(block, leg).net_revenue_gbp / 1e9 : 0);
  const legOffset = (block, leg) => legParticipationOffset(block, leg) + legHoursOffset(block, leg);
  const legCost = (block, leg) => {
    const staticCost = isEngland
      ? block.legs[leg].static_cost_by_country_bn.england
      : block.legs[leg].static_cost_bn;
    return staticCost - legOffset(block, leg);
  };
  const cost = (leg) => legCost(result, leg);
  const takeUpCases = result.free_hours_take_up?.cases;
  const subsidyRange = result.subsidy_range;
  const staticCost = (leg) =>
    isEngland ? legs[leg].static_cost_by_country_bn.england : legs[leg].static_cost_bn;
  const response = hasExtensive
    ? isEngland
      ? result.labour_supply[bound].by_country.england
      : result.labour_supply[bound]
    : null;
  // The combined cost and offset on the selected area, so the share below is
  // computed on its own denominator rather than the UK one.
  const combinedStatic = staticCost("combined");
  const hoursResponse = hasIntensive
    ? isEngland
      ? result.hours_response[HOURS_BOUND].by_country.england
      : result.hours_response[HOURS_BOUND]
    : null;
  const combinedOffset =
    (response ? response.net_revenue_gbp : 0) / 1e9 +
    (hoursResponse ? hoursResponse.net_revenue_gbp : 0) / 1e9;
  // Sign convention on every card: figures are changes in cost, so "+" adds
  // to the cost and "−" lowers it. Net revenue from a labour supply response
  // therefore shows with a minus.
  // One count per margin that is switched on, so a card reads the same
  // whichever combination is chosen.
  // Each margin names its own unit and its own change in cost, so a fall in the
  // number in work is never read as the source of the saving.
  const marginCounts = (r, h) =>
    [
      hasExtensive
        ? `participation ${formatSignedCount(r.net_entrants)} in work (${formatSignedBn(-r.net_revenue_gbp / 1e9)})`
        : null,
      hasIntensive
        ? `hours ${formatSignedCount(h.ftes)} FTEs (${formatSignedBn(-h.net_revenue_gbp / 1e9)})`
        : null,
    ]
      .filter(Boolean)
      .join("; ");
  const legLine = (leg) =>
    `Static ${formatBn(staticCost(leg))}. Labour supply ${formatSignedBn(-legOffset(result, leg))}: ${marginCounts(
      hasExtensive ? legResponse(result, leg) : null,
      hasIntensive ? legHours(result, leg) : null,
    )}.`;
  // "Microcosm UK 2024-25 (national release a6299504, 25 October 2026)" →
  // "Microcosm UK 2024-25 (a6299504)".
  const datasetLabel = (data.dataset ?? "Microcosm UK 2024-25").replace(
    /\(national release (\w+)[^)]*\)/,
    "($1)",
  );
  // Signed, like the card value: the response's change in cost as a share of
  // the static cost.
  const offsetSharePct = combinedStatic ? (-combinedOffset / combinedStatic) * 100 : 0;

  const yearRows = data.years.map((y) => {
    const block = data.by_year[String(y)];
    return {
      year: formatFiscalYear(y),
      free_hours: legCost(block, "free_hours"),
      subsidy: legCost(block, "subsidy"),
      combined: legCost(block, "combined"),
      // Both legs run together cost less than the sum, so the stack splits the
      // combined cost in order: free hours alone, then what the subsidy adds.
      combined_free_hours: legCost(block, "free_hours"),
      combined_subsidy: legCost(block, "combined") - legCost(block, "free_hours"),
    };
  });

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title={`Budget impact, ${formatFiscalYear(data.years[0])} to ${formatFiscalYear(data.years[data.years.length - 1])}`}
          description={
            <>
              Costed against current policy on {datasetLabel}. Free hours are
              England-only; the subsidy is UK-wide.
            </>
          }
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Stat
            label={`Free hours, England, ${formatFiscalYear(year)}`}
            value={formatBn(cost("free_hours"))}
            sub={isStatic ? "Static costing." : legLine("free_hours")}
            footnote={
              takeUpCases ? (
                <>
                  Static range by take-up of the new hours outside work:{" "}
                  {formatBn(takeUpCases.low.static_cost_bn)} (low) to{" "}
                  {formatBn(takeUpCases.high.static_cost_bn)} (high). Central{" "}
                  {formatBn(takeUpCases.central.static_cost_bn)} uses the 2-year-old
                  offer&apos;s take-up flag; see {goTo("methodology", "Methodology")}.
                </>
              ) : null
            }
          />
          <Stat
            label={`75% subsidy${areaLabel}, ${formatFiscalYear(year)}`}
            value={formatBn(cost("subsidy"))}
            sub={
              isEngland
                ? `Rest of UK: ${formatBn(byCountry.scotland)} Scotland, ${formatBn(byCountry.wales)} Wales, ${formatBn(byCountry.northern_ireland)} Northern Ireland.`
                : isStatic
                  ? "Static costing."
                  : legLine("subsidy")
            }
            footnote={
              !isEngland && subsidyRange ? (
                <>
                  Static range: {formatBn(subsidyRange.current_behaviour_bn)} if families keep
                  routing today&apos;s share of spend through the scheme,{" "}
                  {formatBn(subsidyRange.cma_fee_base_bn)} on the CMA fee base,{" "}
                  {formatBn(subsidyRange.as_coded_bn)} as coded (full take-up).
                </>
              ) : null
            }
          />
          {isStatic ? (
            <Stat
              label="Behavioural response"
              value="None"
              sub="Switch on a margin above to add a labour supply response."
            />
          ) : (
            <Stat
              label={`Labour supply, both legs${areaLabel}`}
              value={formatSignedBn(-combinedOffset)}
              sub={`${formatSignedPct(offsetSharePct, 1)} of static cost. ${(() => { const t = marginCounts(response, hoursResponse); return t.charAt(0).toUpperCase() + t.slice(1); })()}.`}
              footnote={
                <>
                  {hasExtensive ? BOUND_NOTES[bound]?.(assumptions) : null}
                  {hasExtensive && hasIntensive ? "; " : null}
                  {hasIntensive ? `${hasExtensive ? "h" : "H"}ours elasticity ${assumptions.hours_price_elasticity}` : null}
                  {". "}
                  {A(src.obr_labour_supply, "OBR elasticities")}
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
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-4">
              <dt className="text-sm font-semibold text-slate-900">
                Leg 1 — free childcare hours (England)
              </dt>
              <dd className="mt-2 space-y-2 text-sm leading-6 text-slate-600">
                <p>
                  <span className="font-medium text-slate-800">Today:</span> every 3-4 year
                  old gets 15 free hours a week. Children from 9 months get 30 hours only if
                  each parent works and earns under £100,000; some disadvantaged 2-year-olds
                  get 15.
                </p>
                <p>
                  <span className="font-medium text-slate-800">Under the reform:</span>{" "}
                  <strong>every child from 9 months to school age gets 15 hours</strong>,
                  with no work or income test. Working parents under £100,000 get a further
                  15, so they keep 30.
                </p>
                <p>
                  <span className="font-medium text-slate-800">Who it reaches:</span>{" "}
                  mainly families where a parent is not in work, or earns over £100,000,
                  with a child under 3.
                </p>
              </dd>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <dt className="text-sm font-semibold text-slate-900">
                Leg 2 — a 75% childcare subsidy (UK)
              </dt>
              <dd className="mt-2 space-y-2 text-sm leading-6 text-slate-600">
                <p>
                  <span className="font-medium text-slate-800">Today:</span> Tax-Free
                  Childcare adds {(tfcTopUpRate(data) * 100).toFixed(0)}% to what a parent
                  pays in, up to £{tfcCapGbp(data).toLocaleString("en-GB")} a child a year,
                  for working parents each earning under £100,000.
                </p>
                <p>
                  <span className="font-medium text-slate-800">Under the reform:</span>{" "}
                  <strong>the government pays 75% of childcare costs</strong>, with no cap,
                  work test or income limit. It replaces Tax-Free Childcare.
                </p>
                <p>
                  <span className="font-medium text-slate-800">Universal Credit:</span>{" "}
                  families on UC keep its childcare element, which covers{" "}
                  {(ucCoverageRate(data) * 100).toFixed(0)}% of costs, instead of the
                  subsidy.
                </p>
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
              Against the current system. &ldquo;Both legs together&rdquo; runs the two legs at
              once, which in the model costs less than their sum because free hours displace
              paid care; {goTo("methodology", "Methodology")} sets out how much.
            </>
          }
        />
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <label className="mb-5 block max-w-xs">
            <span className="mb-1 block text-xs font-medium text-slate-500">Show</span>
            <select
              value={seriesId}
              onChange={(event) => setSeriesId(event.target.value)}
              className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)] focus:ring-2 focus:ring-[color:var(--pe-color-primary-100)]"
            >
              {CHART_SERIES.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={yearRows} margin={{ left: 8, right: 16, top: 8, bottom: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} unit="bn" />
              <Tooltip
                formatter={(value) => formatBn(value)}
                labelFormatter={(label, payload) =>
                  series.stacked && payload?.length
                    ? `${label}: ${formatBn(payload[0].payload.combined)} together`
                    : label
                }
              />
              <Legend />
              {series.bars.map((leg, index) => (
                <Bar
                  key={leg}
                  stackId={series.stacked ? "combined" : undefined}
                  dataKey={leg}
                  name={LEG_LABELS[leg]}
                  fill={colors.primary[BAR_FILL[leg]]}
                  radius={!series.stacked || index === series.bars.length - 1 ? [4, 4, 0, 0] : 0}
                  maxBarSize={120}
                  isAnimationActive={false}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
      {isStatic ? null : (
        <section>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">
              Labour supply response
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Cheaper or free childcare changes whether parents work and how much. The model
              estimates both, then recosts each leg with the new earnings, tax and benefits.
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
              {hasExtensive ? (
                <li>
                  <strong>Whether parents work (extensive margin).</strong> Each parent&apos;s
                  chance of working moves with how much better off work leaves them, using
                  the {A(src.obr_labour_supply, "OBR's participation elasticities")}. The
                  low and high settings scale these up and down.
                </li>
              ) : null}
              {hasIntensive ? (
                <li>
                  <strong>How many hours they work (intensive margin).</strong> Parents
                  already in work and paying for childcare work more hours when it gets
                  cheaper, at an hours elasticity of {assumptions.hours_price_elasticity}{" "}
                  from {A(src.brewer_hours, "Brewer et al.")}
                </li>
              ) : null}
            </ul>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              The two legs push in opposite directions, set out below.{" "}
              {goTo("methodology", "Methodology")} has the detail
              {hasExtensive && hasIntensive ? ", and why the two margins overlap rather than add" : ""}.
            </p>
            <dl className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4">
                <dt className="text-sm font-semibold text-slate-900">
                  Free hours: fewer parents in work
                </dt>
                <dd className="mt-2 space-y-2 text-sm leading-6 text-slate-600">
                  <p>
                    Today a parent on the 30-hour offer loses all of it on leaving work.
                    Under the reform they would keep 15 hours, so working pays a little less
                    and, in the model, some parents leave:{" "}
                    <strong>{formatCount(legResponse(result, "free_hours").entrants)}</strong>{" "}
                    entrants against{" "}
                    <strong>{formatCount(legResponse(result, "free_hours").leavers)}</strong>{" "}
                    leavers{hasExtensive ? "" : " at the central elasticity"}.
                  </p>
                  <p>
                    This need not cost revenue. When a parent leaves, the government collects
                    less tax but stops paying for their extra 15 hours; for a lower earner
                    the saving on the hours can be the larger.
                  </p>
                </dd>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <dt className="text-sm font-semibold text-slate-900">
                  Subsidy: more parents in work
                </dt>
                <dd className="mt-2 space-y-2 text-sm leading-6 text-slate-600">
                  <p>
                    Paying 75% of childcare costs cuts the price of the care that working
                    requires, so in the model work pays more for parents who would buy
                    childcare. Some enter work and those in work add hours, which lowers this
                    leg&apos;s cost below its static figure.
                  </p>
                  {hasExtensive && !isEngland ? null : (
                    <p>
                      {formatSignedCount(legResponse(result, "subsidy").net_entrants)} net
                      entrants from this leg{hasExtensive ? "" : " at the central elasticity"}.
                    </p>
                  )}
                </dd>
              </div>
            </dl>
          </div>
        </section>
      )}

    </div>
  );
}
