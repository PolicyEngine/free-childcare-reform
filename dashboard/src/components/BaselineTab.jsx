"use client";

import { Fragment, useState } from "react";

import { formatBn } from "../lib/formatters";
import SectionHeading from "./SectionHeading";

function count(value) {
  if (value === null || value === undefined) return "—";
  return Number(value).toLocaleString("en-GB");
}

function money(value) {
  if (value === null || value === undefined) return "—";
  return formatBn(value);
}

export default function BaselineTab({ data, year }) {
  const rows = data.by_year[String(year)].baseline_programmes;
  const [openProgramme, setOpenProgramme] = useState(null);

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="The modelled baseline, programme by programme"
          description={
            <>
              What the model pays under current law, and how many children it covers,
              against the published figure for each scheme. Spending and children are shown
              side by side because they answer different questions — whether the model pays
              the right amount, and whether it reaches the right number of families.
              Tax-Free Childcare is why that distinction is here: before the correction
              described in Benchmarks it was close on children while paying nearly double,
              so a headcount-only check would have passed it. Select any row for the source
              and the reason the comparison is drawn where it is.
            </>
          }
        />

        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          <table className="w-full min-w-[46rem] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-6 py-3 font-semibold">Programme</th>
                <th className="px-4 py-3 text-right font-semibold">Modelled spending</th>
                <th className="px-4 py-3 text-right font-semibold">Official spending</th>
                <th className="px-4 py-3 text-right font-semibold">Children, modelled</th>
                <th className="px-6 py-3 text-right font-semibold">Children, official</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const open = openProgramme === row.programme;
                return (
                  <Fragment key={row.programme}>
                    <tr
                      onClick={() => setOpenProgramme(open ? null : row.programme)}
                      className={`cursor-pointer border-b border-slate-100 transition-colors hover:bg-slate-50 ${
                        open ? "bg-slate-50" : ""
                      }`}
                    >
                      <td className="px-6 py-4 align-top">
                        <div className="font-semibold text-slate-900">
                          <span
                            aria-hidden
                            className="mr-2 inline-block text-slate-400"
                            style={{
                              transform: open ? "rotate(90deg)" : "none",
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
                    {open ? (
                      <tr className="border-b border-slate-100 bg-slate-50">
                        <td colSpan={5} className="px-6 pb-6 pt-0">
                          <div className="text-sm leading-6 text-slate-600">{row.note}</div>
                          <div className="mt-3 border-t border-slate-200 pt-3 text-xs leading-5 text-slate-500">
                            <div>{row.official_caseload_label}</div>
                            <div className="mt-1">{row.official_spending_label}</div>
                            {row.costed_year_spending_bn !== null &&
                            row.costed_year_spending_bn !== undefined ? (
                              <div className="mt-2">
                                At the costed year {row.costed_year} the model pays{" "}
                                {money(row.costed_year_spending_bn)}
                                {row.costed_year_caseload
                                  ? ` to ${count(row.costed_year_caseload)} children`
                                  : ""}
                                . That is the baseline the reform is measured against, and it
                                is deliberately not set against the older published figure
                                above.
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
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-sm leading-6 text-slate-600">
          Each comparison is drawn at the year its published figure covers, not at the
          costed year. Setting a 2027 model figure against a January 2025 census would
          measure the gap between two dates as much as the model: on the working-parent
          entitlement that reads 1.61×, and almost all of it is the September 2025 expansion
          to 30 hours for under-threes, which the census predates. On this basis the four
          programme rows reproduce the same comparison{" "}
          <code>policyengine-uk-data</code> checks its own release against, on the same
          published figures.
        </p>
      </section>
    </div>
  );
}
