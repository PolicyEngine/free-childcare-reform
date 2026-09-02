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

export default function CostTab({ data, year, bound, area }) {
  const isEngland = area === "england";
  const areaLabel = isEngland ? ", England" : ", UK";
  const result = data.by_year[String(year)];
  const legs = result.legs;
  const isStatic = bound === "none";
  const dynamic = isStatic ? null : result.dynamic_cost[bound];
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
  const legResponse = (block, leg) =>
    isEngland ? block.legs[leg].labour_supply[bound].by_country.england : block.legs[leg].labour_supply[bound];
  // The intensive margin — parents in work changing their hours — on the same view.
  const legHours = (block, leg) =>
    isEngland ? block.legs[leg].hours_response[bound].by_country.england : block.legs[leg].hours_response[bound];
  const legOffset = (block, leg) =>
    isStatic ? 0 : (legResponse(block, leg).net_revenue_gbp + legHours(block, leg).net_revenue_gbp) / 1e9;
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
    const block = extendedTakeUp.legs[leg].labour_supply[bound];
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
  const response = isStatic
    ? null
    : isEngland
      ? result.labour_supply[bound].by_country.england
      : result.labour_supply[bound];
  // The combined cost and offset on the selected area, so the share below is
  // computed on its own denominator rather than the UK one.
  const combinedStatic = staticCost("combined");
  const hoursResponse = isStatic
    ? null
    : isEngland
      ? result.hours_response[bound].by_country.england
      : result.hours_response[bound];
  const combinedOffset = isStatic ? 0 : (response.net_revenue_gbp + hoursResponse.net_revenue_gbp) / 1e9;
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
              Each leg costed against the current system, on the PolicyEngine UK Enhanced
              FRS. <strong>The legs cover different countries.</strong> The free
              entitlements are England-only in law and in the model; Tax-Free Childcare and
              the subsidy replacing it are UK-wide. There is no UK figure for free hours
              because early years childcare is devolved: the other nations run their own
              schemes, which this brief does not reform. policyengine-uk models Scottish
              eligibility but not an entitlement amount, and has nothing for Wales or
              Northern Ireland, so there is no devolved entitlement to reform or cost. An
              England spending increase would generate Barnett consequentials, which the
              devolved administrations may spend as they choose; they are not costed here.
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
                : `Static ${formatBn(staticCost('free_hours'))}, plus ${formatSignedBn(-legResponse(result, 'free_hours').net_revenue_gbp / 1e9)} from ${formatCount(legResponse(result, 'free_hours').net_entrants)} net entrants and ${formatSignedBn(-legHours(result, 'free_hours').net_revenue_gbp / 1e9)} from ${formatCount(legHours(result, 'free_hours').ftes)} FTEs of extra hours where displaced paid care cuts the price. Unconditional hours remove a reason to work, so participation lowers; hours rise.`
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
                  : `Static ${formatBn(staticCost('subsidy'))}, plus ${formatSignedBn(-legResponse(result, 'subsidy').net_revenue_gbp / 1e9)} from ${formatCount(legResponse(result, 'subsidy').net_entrants)} net entrants and ${formatSignedBn(-legHours(result, 'subsidy').net_revenue_gbp / 1e9)} from ${formatCount(legHours(result, 'subsidy').ftes)} FTEs of extra hours. Cheaper childcare makes work pay, so this leg costs less.`
            }
          />
          {isStatic ? (
            <Stat
              label="Behavioural response"
              value="None"
              sub="Static costing: nobody changes their hours or whether they work. Choose a response above to add labour supply effects on both margins."
            />
          ) : (
            <Stat
              label={`Labour supply, both legs together${areaLabel}`}
              value={formatSignedBn(-combinedOffset)}
              sub={`${(isEngland ? response.net_entrants : dynamic.net_entrants) >= 0 ? "+" : "−"}${formatCount(
                Math.abs(isEngland ? response.net_entrants : dynamic.net_entrants),
              )} net entrants${isEngland ? " in England" : ` among ${result.labour_supply[bound].responding_adults_m.toFixed(1)}m eligible parents`} (${formatSignedBn(-response.net_revenue_gbp / 1e9)}), plus ${formatCount(hoursResponse.ftes)} FTEs of extra hours from ${formatCount(hoursResponse.workers_with_price_change)} parents in work (${formatSignedBn(-hoursResponse.net_revenue_gbp / 1e9)}). Participation is small: the legs pull against each other. Hours dominate, at ${offsetShare.toFixed(1)}% of the static cost together — but the hours elasticity already contains a participation effect, so the two overlap.`}
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
                (England)
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
                Leg 2 — a 75% subsidy replacing Tax-Free Childcare (UK)
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
                    Not universal, despite the name. The costing keeps Tax-Free
                    Childcare&apos;s take-up rate and its qualifying-child, provider and
                    UK-connection rules. What the reform removes is the work test and the
                    cliff.
                  </li>
                  {extendedTakeUp ? (
                    <li>
                      Take-up is a dataset input, not estimated for this reform. On the
                      extended entitlement&apos;s flag instead of Tax-Free Childcare&apos;s
                      — the argument being that the reform drops TFC&apos;s restrictions —
                      this leg would cost{" "}
                      <strong>{formatBn(extendedStatic("subsidy"))}</strong> static rather
                      than {formatBn(staticCost("subsidy"))}
                      {isStatic
                        ? ""
                        : `, with ${formatCount(extendedResponse("subsidy").net_entrants)} net entrants rather than ${formatCount(legResponse(result, "subsidy").net_entrants)}`}
                      . It is lower because, in this data, the extended flag is the lower
                      of the two ({(extendedTakeUp.take_up_rate_among_qualifying * 100).toFixed(0)}%
                      against {(result.subsidy_take_up.baseline_take_up_rate * 100).toFixed(0)}%).
                    </li>
                  ) : null}
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
              Labour supply response
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Two margins. On the <strong>extensive margin</strong>,{" "}
              {A(src.obr_labour_supply, "the OBR's participation elasticities")} — which
              vary by gender, partner employment, age of youngest child and earnings
              quintile — are applied to the percentage change in each person&apos;s gain to
              work, giving an expected change in their probability of working rather than a
              drawn outcome. On the <strong>intensive margin</strong>, parents already in
              work and paying for childcare change their hours with the price of it: a
              childcare price elasticity of hours of{" "}
              <strong>{assumptions.hours_price_elasticity}</strong>, derived from{" "}
              {A(src.brewer_hours, "Brewer et al.")} (+0.600 hours a week on a mean of
              14.319, against a 100% price fall), applied to each parent&apos;s own change in
              out-of-pocket cost after the subsidy and displaced free hours, at a constant
              wage. The revenue on the extra hours comes from rerunning the model with the
              higher earnings, not from an assumed tax rate. The low and high assumptions
              scale both margins by the same factor.
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Read the hours figure with care. The +0.600 is measured over all mothers,
              with zeros for those not working, so it is a total-hours effect that already
              includes people moving into work; the paper&apos;s own employment effect
              accounts for most of it. Adding it to the participation response below counts
              that channel twice, and the estimated treatment was 12.5 extra free hours a
              week, not a price fall of 100%. On the extensive margin, two forces pull
              against each other, and the reported figure is the net of them, which is why
              it is small.
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
                      the gain to work rises for parents who would be paying for childcare.
                    </li>
                    <li>
                      This is the channel that produces the subsidy leg&apos;s{" "}
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
