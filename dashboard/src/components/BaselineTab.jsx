"use client";

import { formatBn } from "../lib/formatters";
import SectionHeading from "./SectionHeading";

// A ratio's colour is about how far it sits from 1, not which side of it. Both
// directions are a problem; only the size of the gap matters.
function ratioTone(ratio) {
  if (ratio === null || ratio === undefined) return "text-slate-400";
  const gap = Math.abs(ratio - 1);
  if (gap <= 0.1) return "text-emerald-700";
  if (gap <= 0.25) return "text-amber-700";
  return "text-rose-700";
}

function Ratio({ value }) {
  if (value === null || value === undefined) {
    return <span className="text-slate-400">—</span>;
  }
  return (
    <span className={`font-semibold tabular-nums ${ratioTone(value)}`}>
      {value.toFixed(2)}×
    </span>
  );
}

function count(value) {
  return Number(value).toLocaleString("en-GB");
}

export default function BaselineTab({ data, year }) {
  const rows = data.by_year[String(year)].baseline_programmes;

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="The modelled baseline, programme by programme"
          description={
            <>
              What the model pays under current law, and how many children it covers,
              against the published figure for each scheme. Spending and caseload are shown
              side by side because they answer different questions — whether the model pays
              the right amount, and whether it covers the right children. Tax-Free Childcare
              is why that distinction is here: before the correction described below it was
              close on caseload while paying nearly double, so a caseload-only check would
              have passed it.
            </>
          }
        />

        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          <table className="w-full min-w-[52rem] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-6 py-3 font-semibold">Programme</th>
                <th className="px-3 py-3 text-right font-semibold">Model</th>
                <th className="px-3 py-3 text-right font-semibold">Official</th>
                <th className="px-3 py-3 text-right font-semibold">Ratio</th>
                <th className="px-3 py-3 text-right font-semibold">Model</th>
                <th className="px-3 py-3 text-right font-semibold">Official</th>
                <th className="px-6 py-3 text-right font-semibold">Ratio</th>
              </tr>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-400">
                <th className="px-6 pb-3 font-normal">compared at the published figure&apos;s year</th>
                <th className="px-3 pb-3 text-right font-normal" colSpan={3}>
                  Spending
                </th>
                <th className="px-3 pb-3 text-right font-normal" colSpan={3}>
                  Children
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.programme} className="border-b border-slate-100 last:border-0">
                  <td className="px-6 py-4 align-top">
                    <div className="font-semibold text-slate-900">{row.label}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {row.geography}, {row.period} · read at {row.comparison_year}
                    </div>
                  </td>
                  <td className="px-3 py-4 text-right tabular-nums text-slate-700">
                    {formatBn(row.model_spending_bn)}
                  </td>
                  <td className="px-3 py-4 text-right tabular-nums text-slate-700">
                    {row.official_spending_bn ? (
                      formatBn(row.official_spending_bn)
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-3 py-4 text-right">
                    <Ratio value={row.spending_ratio} />
                  </td>
                  <td className="px-3 py-4 text-right tabular-nums text-slate-700">
                    {count(row.model_caseload)}
                  </td>
                  <td className="px-3 py-4 text-right tabular-nums text-slate-700">
                    {count(row.official_caseload)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Ratio value={row.caseload_ratio} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-sm leading-6 text-slate-600">
          These are the same four ratios <code>policyengine-uk-data</code> checks its own
          release against, on the same published figures, so this table and the data build
          agree by construction rather than by coincidence. Two rows have no published
          spending figure: DfE reports the universal and working-parent entitlements as one
          £8.7bn total for England rather than separately.
        </p>
      </section>

      <section>
        <SectionHeading
          title="Why each comparison is drawn where it is"
          description="Every published figure predates the years this reform is costed for, and the periods differ by programme. Each ratio above is taken at the year its published figure covers — not at the costed year — because a model figure divided by an older statistic measures the gap between the two dates as much as anything else."
        />
        <div className="space-y-4">
          {rows.map((row) => (
            <div
              key={row.programme}
              className="rounded-2xl border border-slate-200 bg-white p-6"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div className="font-semibold text-slate-900">{row.label}</div>
                <a
                  href={row.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-[color:var(--pe-color-primary-600)] underline"
                >
                  source
                </a>
              </div>
              <div className="mt-2 text-sm leading-6 text-slate-600">{row.note}</div>
              <div className="mt-3 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">
                {row.official_caseload_label}
                {row.official_spending_bn ? ` · ${row.official_spending_label}` : null}
                <br />
                At the costed year {row.costed_year} the model pays{" "}
                {formatBn(row.costed_year_spending_bn)} to{" "}
                {count(row.costed_year_caseload)} children. That is the baseline the reform
                is measured against, and it is deliberately not divided by the older
                published figure above.
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
