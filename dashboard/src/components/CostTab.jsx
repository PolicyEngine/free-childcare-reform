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
      )}
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
