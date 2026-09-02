"use client";

import { Fragment, useState } from "react";

import { formatBn, formatFiscalYear } from "../lib/formatters";
import SectionHeading from "./SectionHeading";


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

// Children are shown in millions so the two columns compare at a glance
// rather than by counting digits.
function count(value) {
  if (value === null || value === undefined) return "—";
  return `${(Number(value) / 1e6).toFixed(2)}m`;
}

export default function BaselineTab({ data, year }) {
  const result = data.by_year[String(year)];
  const programmes = result.baseline_programmes;
  const sensitivity = result.fee_base_sensitivity;
  // How much bigger the model's fee base is than the published one. Note this
  // is the reciprocal of sensitivity.ratio, which scales the base down.
  const feeBaseRatio = sensitivity
    ? sensitivity.model_england_under_5_bn / sensitivity.benchmark_england_under_5_bn
    : null;
  const costings = data.comparable_costings || [];
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
                <th className="px-4 py-3 text-right font-semibold">Children, modelled (m)</th>
                <th className="px-6 py-3 text-right font-semibold">Children, official (m)</th>
              </tr>
            </thead>
            <tbody>
              {programmes.map((row) => {
                const isOpen = open === row.programme;
                return (
                  <Fragment key={row.programme}>
                    <tr
                      className={`border-b border-slate-100 transition-colors hover:bg-slate-50 ${
                        isOpen ? "bg-slate-50" : ""
                      }`}
                    >
                      <td className="px-6 py-4 align-top">
                        <button
                          type="button"
                          onClick={() => setOpen(isOpen ? null : row.programme)}
                          aria-expanded={isOpen}
                          className="w-full cursor-pointer text-left font-semibold text-slate-900"
                        >
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
                          <span className="sr-only">
                            {isOpen ? " (collapse details)" : " (expand details)"}
                          </span>
                        </button>
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
                            <div className="mt-2 flex gap-4">
                              <a
                                href={row.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-[color:var(--pe-color-primary-600)] underline"
                              >
                                caseload source
                              </a>
                              {row.spending_url ? (
                                <a
                                  href={row.spending_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-[color:var(--pe-color-primary-600)] underline"
                                >
                                  spending source
                                </a>
                              ) : null}
                            </div>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
        {sensitivity ? (
          <p className="mt-4 text-sm leading-6 text-slate-600">
            <strong>The childcare fee base is the largest uncertainty.</strong> For
            England&apos;s under-5s the model has{" "}
            {formatBn(sensitivity.model_england_under_5_bn)} of childcare fees against a
            published estimate of {formatBn(sensitivity.benchmark_england_under_5_bn)},
            about {feeBaseRatio.toFixed(2)}× as much. Scaling the model&apos;s under-5 fees
            to that estimate would take the subsidy leg from{" "}
            {formatBn(result.legs.subsidy.static_cost_bn)} to{" "}
            {formatBn(sensitivity.subsidy_cost_bn)}; free hours are unaffected. The CMA
            figure is a residual of a sector-income estimate and contains other provider
            income, so this is one accounting scenario, not a bound.
          </p>
        ) : null}
      </section>

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
