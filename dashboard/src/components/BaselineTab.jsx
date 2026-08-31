"use client";

import { Fragment, useState } from "react";

import { formatBn, formatFiscalYear } from "../lib/formatters";
import SectionHeading from "./SectionHeading";

// Programmes are compared at the year their published figure covers. The UC
// childcare element is not a programme in that sense and carries its own
// basis, so it sits below the scheme rows.
// The fee base is not listed here: it has its own section below, and the
// entitlement schemes above have no official spending line to compare with.
const EXTRA_MEASURES = ["Universal Credit childcare element"];

const BADGE = {
  "Caseload gap": "bg-amber-50 text-amber-700 border-amber-200",
  "Not comparable": "bg-slate-100 text-slate-600 border-slate-200",
  "Fee base check": "bg-amber-50 text-amber-700 border-amber-200",
};

function money(value) {
  return value === null || value === undefined ? "—" : formatBn(value);
}

// cost_bn carries its own qualifier for some entries ("3.0-3.4 net",
// "4.1 by 2027-28"), so "bn" belongs after the number, not after the string.
function formatCosting(value) {
  const text = String(value);
  const match = text.match(/^([\d.\u2013-]+)(.*)$/);
  if (!match) return `£${text}bn`;
  const [, number, qualifier] = match;
  return `£${number}bn${qualifier}`;
}

function count(value) {
  return value === null || value === undefined
    ? "—"
    : Number(value).toLocaleString("en-GB");
}

export default function BaselineTab({ data, year }) {
  const result = data.by_year[String(year)];
  const programmes = result.baseline_programmes;
  const sensitivity = result.fee_base_sensitivity;
  const costings = data.comparable_costings || [];
  const extras = (result.benchmarks || []).filter((row) =>
    EXTRA_MEASURES.includes(row.measure),
  );
  const [open, setOpen] = useState(null);

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="The modelled baseline against published figures"
          description={
            <>
              What the model pays under current law and how many children it reaches, per
              scheme. Nothing here is an input to the costing — the reform is measured as a
              difference from this baseline, not as a level — but it is what tells you how
              much weight the headline bears. Each comparison is drawn at the year its
              published figure covers, not at {formatFiscalYear(year)}: setting a
                {" "}{formatFiscalYear(year)} figure against a
              January 2025 census would measure the gap between two dates as much as the
              model. Select a row for the source and the reasoning.
            </>
          }
        />

        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          <table className="w-full min-w-[46rem] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-6 py-3 font-semibold">Programme</th>
                <th className="px-4 py-3 text-right font-semibold">Spending, modelled</th>
                <th className="px-4 py-3 text-right font-semibold">Spending, official</th>
                <th className="px-4 py-3 text-right font-semibold">Children, modelled</th>
                <th className="px-6 py-3 text-right font-semibold">Children, official</th>
              </tr>
            </thead>
            <tbody>
              {programmes.map((row) => {
                const isOpen = open === row.programme;
                return (
                  <Fragment key={row.programme}>
                    <tr
                      onClick={() => setOpen(isOpen ? null : row.programme)}
                      className={`cursor-pointer border-b border-slate-100 transition-colors hover:bg-slate-50 ${
                        isOpen ? "bg-slate-50" : ""
                      }`}
                    >
                      <td className="px-6 py-4 align-top">
                        <div className="font-semibold text-slate-900">
                          <span
                            aria-hidden
                            className="mr-2 inline-block text-slate-400"
                            style={{
                              transform: isOpen ? "rotate(90deg)" : "none",
                              transition: "transform 120ms",
                            }}
                          >
                            ▸
                          </span>
                          {row.label}
                        </div>
                        <div className="mt-1 pl-5 text-xs text-slate-500">
                          {row.geography}, {row.period} · compared at {row.comparison_year}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-right tabular-nums text-slate-700">
                        {money(row.model_spending_bn)}
                      </td>
                      <td className="px-4 py-4 text-right tabular-nums text-slate-700">
                        {money(row.official_spending_bn)}
                      </td>
                      <td className="px-4 py-4 text-right tabular-nums text-slate-700">
                        {count(row.model_caseload)}
                      </td>
                      <td className="px-6 py-4 text-right tabular-nums text-slate-700">
                        {count(row.official_caseload)}
                      </td>
                    </tr>
                    {isOpen ? (
                      <tr className="border-b border-slate-100 bg-slate-50">
                        <td
                          colSpan={5}
                          className="px-6 pb-6 pt-0 text-sm leading-6 text-slate-600"
                        >
                          <div>{row.note}</div>
                          <div className="mt-3 border-t border-slate-200 pt-3 text-xs leading-5 text-slate-500">
                            <div>{row.official_caseload_label}</div>
                            <div className="mt-1">{row.official_spending_label}</div>
                            {row.costed_year_spending_bn ? (
                              <div className="mt-2">
                                At {row.costed_year} the model pays{" "}
                                {money(row.costed_year_spending_bn)}
                                {row.costed_year_caseload
                                  ? ` to ${count(row.costed_year_caseload)} children`
                                  : ""}
                                . That is the baseline the reform is measured against.
                              </div>
                            ) : null}
                            <a
                              href={row.url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-2 inline-block text-[color:var(--pe-color-primary-600)] underline"
                            >
                              source
                            </a>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}

              {extras.map((row) => (
                <tr
                  key={row.measure}
                  className="border-b border-slate-100 align-top last:border-0"
                >
                  <td className="px-6 py-4">
                    <div className="font-semibold text-slate-900">{row.measure}</div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span
                        className={`inline-block whitespace-nowrap rounded-full border px-2 py-0.5 font-medium ${
                          BADGE[row.kind] || BADGE["Not comparable"]
                        }`}
                      >
                        {row.kind}
                      </span>
                      <span>
                        {row.geography}, {row.period}
                      </span>
                      <a
                        href={row.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[color:var(--pe-color-primary-600)] underline"
                      >
                        source
                      </a>
                    </div>
                    <div className="mt-2 max-w-3xl space-y-2 text-xs leading-5 text-slate-500">
                      {String(row.note)
                        .split("\n\n")
                        .map((paragraph) => (
                          <p key={paragraph.slice(0, 32)}>{paragraph}</p>
                        ))}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right tabular-nums text-slate-700">
                    {money(row.model_bn)}
                  </td>
                  <td className="px-4 py-4 text-right tabular-nums text-slate-700">
                    {money(row.official_bn)}
                  </td>
                  <td className="px-4 py-4 text-right text-slate-400">—</td>
                  <td className="px-6 py-4 text-right text-slate-400">—</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {sensitivity ? (
        <section>
          <SectionHeading
            title="How much the childcare fee base moves the answer"
            description={
              <>
                The 75% subsidy pays a share of what families spend on childcare, so its
                cost depends on how much the model thinks they spend. For England&apos;s
                under-5s the model has{" "}
                <strong>{formatBn(sensitivity.model_england_under_5_bn)}</strong> of
                childcare fees against a published estimate of{" "}
                <strong>{formatBn(sensitivity.benchmark_england_under_5_bn)}</strong> — about{" "}
                {(
                  sensitivity.model_england_under_5_bn /
                  sensitivity.benchmark_england_under_5_bn
                ).toFixed(2)}
                × as much. If the published figure is the better one, the subsidy is
                being priced on a fee base that is too big, and the cost below falls.
                Scaling the model&apos;s under-5 fees down to that estimate — and leaving
                school-age childcare alone, because nothing is published to scale it
                against — gives the second figure. This is the largest single uncertainty
                in the costing, worth about{" "}
                {formatBn(
                  result.legs.combined.static_cost_bn - sensitivity.combined_cost_bn,
                )}
                .
              </>
            }
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <div className="text-sm text-slate-500">
                Both legs, on the model&apos;s own fee base
              </div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">
                {formatBn(result.legs.combined.static_cost_bn)}
              </div>
              <div className="mt-2 text-sm text-slate-500">
                Of which {formatBn(result.legs.subsidy.static_cost_bn)} is the subsidy.
                This is the headline figure, and the top of the range.
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <div className="text-sm text-slate-500">
                Both legs, on the published fee base
              </div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">
                {formatBn(sensitivity.combined_cost_bn)}
              </div>
              <div className="mt-2 text-sm text-slate-500">
                Of which {formatBn(sensitivity.subsidy_cost_bn)} is the subsidy. The bottom
                of the range: free hours are unaffected, so they set a floor.
              </div>
            </div>
          </div>
        </section>
      ) : null}

      <section>
        <SectionHeading
          title="Comparable published costings"
          description="What other people have put on similar proposals, and how comparable each one is."
        />
        <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-white">
          {costings.map((costing) => (
            <div key={costing.proposal} className="p-6">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-base font-semibold text-slate-900">
                  {costing.proposal}
                </h3>
                <span className="text-lg font-semibold text-[color:var(--pe-color-primary-600)]">
                  {formatCosting(costing.cost_bn)}
                </span>
              </div>
              <div className="mt-1 text-sm text-slate-500">
                <a href={costing.url} target="_blank" rel="noreferrer" className="underline">
                  {costing.source}
                </a>
                , {costing.date} · {costing.geography}
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">{costing.note}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
