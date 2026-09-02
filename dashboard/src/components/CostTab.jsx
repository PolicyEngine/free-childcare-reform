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

// What each labour supply assumption is, in the reader's view.
const BOUND_NOTES = {
  central: (a) =>
    `Central: OBR elasticities as published (price elasticity ${a.price_elasticity_central}).`,
  low: (a) =>
    `Low: OBR elasticities × ${a.elasticity_scale_low?.toFixed(2)} (price elasticity ${a.price_elasticity_low}).`,
  high: (a) =>
    `High: OBR elasticities × ${a.elasticity_scale_high?.toFixed(2)} (price elasticity ${a.price_elasticity_high}).`,
};

const LEG_LABELS = {
  free_hours: "15 free hours for all, from 9 months",
  subsidy: "75% subsidy replacing Tax-Free Childcare",
};

export default function CostTab({ data, year, bound, intensive, area }) {
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
  const dynamic = hasExtensive ? result.dynamic_cost[bound] : null;
  // Each panel below describes one leg's channel, so it must show that leg's
  // own response rather than the response to both legs together.
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
  // The same leg with the subsidy's take-up read from the extended
  // entitlement's flag, so the size of that choice shows on the same view.
  const extendedTakeUp = result.subsidy_take_up?.extended_entitlement_flag;
  const extendedResponse = (leg) => {
    const block = extendedTakeUp.legs[leg].labour_supply[participationBound];
    return isEngland ? block.by_country.england : block;
  };
  // Static only: the extended-flag scenario carries the participation margin
  // but not the hours margin, so its dynamic cost would not be comparable.
  const extendedStatic = (leg) => {
    const block = extendedTakeUp.legs[leg];
    return isEngland ? block.static_cost_by_country_bn.england : block.static_cost_bn;
  };
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
  // One sentence per margin that is switched on, so a card reads the same
  // whichever combination is chosen.
  const legParts = (leg) => {
    const parts = [];
    if (hasExtensive) {
      const r = legResponse(result, leg);
      parts.push(
        `${formatSignedBn(-r.net_revenue_gbp / 1e9)} from ${formatCount(r.net_entrants)} net entrants`,
      );
    }
    if (hasIntensive) {
      const h = legHours(result, leg);
      parts.push(`${formatSignedBn(-h.net_revenue_gbp / 1e9)} from ${formatCount(h.ftes)} FTEs of extra hours`);
    }
    return parts.join(" and ");
  };
  const offsetShare = combinedStatic ? Math.abs(combinedOffset / combinedStatic) * 100 : 0;

  const yearRows = data.years.map((y) => {
    const block = data.by_year[String(y)];
    return {
      year: formatFiscalYear(y),
      free_hours: legCost(block, "free_hours"),
      subsidy: legCost(block, "subsidy"),
    };
  });

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title={`Budget impact, ${formatFiscalYear(data.years[0])} to ${formatFiscalYear(data.years[data.years.length - 1])}`}
          description={
            <>
              Each leg is costed against the current system on the PolicyEngine UK Enhanced
              FRS. <strong>The legs cover different countries:</strong> the free
              entitlements are England-only, in law and in the model; Tax-Free Childcare
              and the subsidy replacing it are UK-wide. There is no UK free-hours figure
              because early years is devolved and the model carries no devolved entitlement
              amounts, and the Barnett consequentials of England spending are not costed.
            </>
          }
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Stat
            label={`Free hours, England, ${formatFiscalYear(year)}`}
            value={formatBn(cost("free_hours"))}
            sub={
              isStatic
                ? "15 hours for every child from 9 months, plus 15 more where parents work and earn under £100,000."
                : `Static ${formatBn(staticCost('free_hours'))}, plus ${legParts('free_hours')}.${hasExtensive ? " Unconditional hours remove a reason to work, so participation falls." : ""}${hasIntensive ? " Displaced paid care cuts the price for working parents, so hours rise." : ""}`
            }
          />
          <Stat
            label={`75% subsidy${areaLabel}, ${formatFiscalYear(year)}`}
            value={formatBn(cost("subsidy"))}
            sub={
              isEngland
                ? `Tax-Free Childcare is UK-wide, so this leg splits: the rest is ${formatBn(byCountry.scotland)} Scotland, ${formatBn(byCountry.wales)} Wales and ${formatBn(byCountry.northern_ireland)} Northern Ireland.`
                : isStatic
                  ? `Replacing Tax-Free Childcare. On the published fee base this is ${formatBn(feeBase.subsidy_cost_bn)} — see Baseline.`
                  : `Static ${formatBn(staticCost('subsidy'))}, plus ${legParts('subsidy')}. Cheaper childcare makes work pay, so this leg costs less.`
            }
          />
          {isStatic ? (
            <Stat
              label="Behavioural response"
              value="None"
              sub="Static costing: nobody changes their hours or whether they work. Switch on a margin above to add a labour supply response."
            />
          ) : (
            <Stat
              label={`Labour supply, both legs together${areaLabel}`}
              value={formatSignedBn(-combinedOffset)}
              sub={[
                hasExtensive
                  ? `${response.net_entrants >= 0 ? "+" : "−"}${formatCount(Math.abs(response.net_entrants))} net entrants${isEngland ? " in England" : ` among ${result.labour_supply[bound].responding_adults_m.toFixed(1)}m eligible parents`} (${formatSignedBn(-response.net_revenue_gbp / 1e9)}), the net of the two legs pulling in opposite directions.`
                  : null,
                hasIntensive
                  ? `${formatCount(hoursResponse.ftes)} FTEs of extra hours from ${formatCount(hoursResponse.workers_with_price_change)} parents in work (${formatSignedBn(-hoursResponse.net_revenue_gbp / 1e9)}).`
                  : null,
                `${offsetShare.toFixed(1)}% of the static cost.`,
                hasExtensive && hasIntensive
                  ? "The two margins overlap rather than add."
                  : null,
              ]
                .filter(Boolean)
                .join(" ")}
              footnote={
                <>
                  {hasExtensive ? BOUND_NOTES[bound]?.(assumptions) : null}{" "}
                  {hasIntensive ? `Hours elasticity ${assumptions.hours_price_elasticity}, one setting.` : null}{" "}
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
                (England)
              </dt>
              <dd className="mt-2 text-sm leading-6 text-slate-600">
                <ul className="list-disc space-y-1 pl-5">
                  <li>Today: 15 hours for 3-4 year olds; 30 where parents work and earn under £100,000.</li>
                  <li>
                    After: <strong>15 hours for every child</strong> from 9 months to school
                    age, with no work or income test.
                  </li>
                  <li>
                    Plus <strong>a further 15 hours</strong> where parents work and earn
                    under £100,000.
                  </li>
                  <li>A non-working family gains 15 hours; a working family under £100,000 keeps its 30.</li>
                </ul>
              </dd>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <dt className="text-sm font-semibold text-slate-900">
                Leg 2 — a 75% subsidy replacing Tax-Free Childcare (UK)
              </dt>
              <dd className="mt-2 text-sm leading-6 text-slate-600">
                <ul className="list-disc space-y-1 pl-5">
                  <li>
                    Today: Tax-Free Childcare tops up 25% of what a parent pays in, capped at
                    £2,000 a child, with a work test and a £100,000 cliff.
                  </li>
                  <li>
                    After: <strong>75% of childcare costs</strong>, with no cap, work test
                    or cliff.
                  </li>
                  <li>
                    Not universal: the costing keeps Tax-Free Childcare&apos;s take-up rate
                    and its qualifying-child, provider and UK-connection rules.
                  </li>
                  {extendedTakeUp ? (
                    <li>
                      Take-up is a dataset input. Read from the extended entitlement&apos;s
                      flag instead, this leg would cost{" "}
                      <strong>{formatBn(extendedStatic("subsidy"))}</strong> static rather
                      than {formatBn(staticCost("subsidy"))}
                      {hasExtensive
                        ? `, with ${formatCount(extendedResponse("subsidy").net_entrants)} net entrants rather than ${formatCount(legResponse(result, "subsidy").net_entrants)}`
                        : ""}
                      , because that flag has the lower take-up rate in this data (
                      {(extendedTakeUp.take_up_rate_among_qualifying * 100).toFixed(0)}%
                      against {(result.subsidy_take_up.baseline_take_up_rate * 100).toFixed(0)}%).
                    </li>
                  ) : null}
                  <li>
                    Families on Universal Credit keep the <strong>85% childcare element</strong>{" "}
                    unchanged rather than stacking the two.
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
              Each leg on its own, against the current system. They are not added
              together: free hours displace paid care, so running both at once costs less
              than the sum of the two. The assumption is that{" "}
              {A(src.ifs_free_childcare, "90% of a new free offer")} replaces care a family
              was already buying, but displacement is capped at what they spend,
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
              Labour supply response
            </h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
              {hasExtensive ? (
                <li>
                  <strong>Extensive margin.</strong>{" "}
                  {A(src.obr_labour_supply, "The OBR's participation elasticities")} — by
                  gender, partner employment, age of youngest child and earnings quintile —
                  applied to each person&apos;s percentage change in the gain to work, as an
                  expected change in their probability of working. Two forces pull against
                  each other and the figure is their net, which is why it is small. Low and
                  high scale the elasticities by a fixed factor.
                </li>
              ) : null}
              {hasIntensive ? (
                <li>
                  <strong>Intensive margin.</strong> Parents in work and paying for childcare
                  change their hours with its price: a hours elasticity of{" "}
                  <strong>{assumptions.hours_price_elasticity}</strong> from{" "}
                  {A(src.brewer_hours, "Brewer et al.")} (+0.600 hours a week on a mean of
                  14.319, against a 100% price fall), applied to each parent&apos;s change in
                  out-of-pocket cost after the subsidy, displaced free hours and the UC
                  childcare support realised, at a constant wage. Revenue comes from
                  rerunning the model with the higher earnings. One setting; it does not move
                  with the extensive-margin elasticity.
                </li>
              ) : null}
              {hasIntensive ? (
                <li>
                  <strong>The hours figure overlaps the participation figure.</strong> The +0.600 is measured over
                  all mothers, zeros included, so it already contains people moving into work
                  — the paper&apos;s own employment effect accounts for most of it. Adding it to
                  the participation response counts that channel twice, and the treatment
                  was a move from part-time (12.5-15 hours a week) to full-time school hours
                  (30-35), not a 100% price fall.
                </li>
              ) : null}
            </ul>
            <dl className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4">
                <dt className="text-sm font-semibold text-slate-900">
                  Downward — the reform removes work conditions
                </dt>
                <dd className="mt-2 text-sm leading-6 text-slate-600">
                  <ul className="list-disc space-y-1 pl-5">
                    <li>
                      Today, working parents each earning under £100,000 get 30 hours from 9
                      months; a non-working family gets nothing until the child is 3 (15
                      hours at 3-4), except 2-year-olds in families on out-of-work benefits
                      or UC under £15,400, who get 15 hours.
                    </li>
                    <li>
                      Under the reform a non-working family gets 15 hours in or out of work,
                      so its gain to work is unchanged. The gain to work falls for working
                      parents on the 30-hour offer, who would now keep 15 hours if they
                      stopped working: these are the leavers.
                    </li>
                    <li>
                      The in-work entitlement of parents each earning under £100,000 is
                      unchanged under this leg.
                    </li>
                    <li>
                      Free-hours leg alone:{" "}
                      <strong>{formatCount(legResponse(result, 'free_hours').entrants)}</strong> entrants
                      against <strong>{formatCount(legResponse(result, 'free_hours').leavers)}</strong>{" "}
                      leavers, a net revenue effect of{" "}
                      <strong>
                        {formatSignedBn(legResponse(result, 'free_hours').net_revenue_gbp / 1e9)}
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
                      the gain to work rises for parents who would pay for childcare.
                    </li>
                    <li>
                      This channel produces the subsidy leg&apos;s{" "}
                      <strong>
                        {formatCount(legResponse(result, 'subsidy').net_entrants)}
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
