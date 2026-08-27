"use client";

import { formatBn } from "../lib/formatters";
import SectionHeading from "./SectionHeading";

const KIND_STYLES = {
  "Independent check": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Caseload and award gap": "bg-amber-50 text-amber-700 border-amber-200",
  "Fee base check": "bg-amber-50 text-amber-700 border-amber-200",
  Unbenchmarked: "bg-slate-100 text-slate-600 border-slate-200",
  "Not comparable": "bg-slate-100 text-slate-600 border-slate-200",
};

function Badge({ kind }) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium ${
        KIND_STYLES[kind] || KIND_STYLES["Not comparable"]
      }`}
    >
      {kind}
    </span>
  );
}

export default function BenchmarkTab({ data, year }) {
  const result = data.by_year[String(year)];
  const benchmarks = result.benchmarks || [];
  const sensitivity = result.fee_base_sensitivity;
  const costings = data.comparable_costings || [];
  const cliff = data.income_cliff_context;

  return (
    <div className="space-y-10">
      <section>
        <SectionHeading
          title="The model against published outturns"
          description={
            <>
              None of these figures is an input to the estimate. They are here because two
              of the gaps change how the results should be read, and both are flagged
              below rather than quietly corrected away. Model figures are UK-wide unless
              the variable is England-only by construction; several benchmarks are
              England-only, so a model figure modestly above a published England number is
              expected.
            </>
          }
        />
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="px-6 py-3 font-medium">Measure</th>
                  <th className="px-6 py-3 font-medium">Model</th>
                  <th className="px-6 py-3 font-medium">Published</th>
                  <th className="px-6 py-3 font-medium">Ratio</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {benchmarks.map((row) => (
                  <tr key={row.measure} className="align-top">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{row.measure}</div>
                      <div className="mt-1 text-xs text-slate-400">
                        {row.model_variables}
                      </div>
                      {row.note ? (
                        <div className="mt-2 max-w-xl text-xs leading-5 text-slate-500">
                          {row.note}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      {formatBn(row.model_bn)}
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      <a
                        href={row.url}
                        target="_blank"
                        rel="noreferrer"
                        className="underline"
                      >
                        {row.official_label}
                      </a>
                      <div className="mt-1 text-xs text-slate-400">
                        {row.geography}, {row.period}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      {row.ratio_model_to_official
                        ? `${row.ratio_model_to_official}×`
                        : "—"}
                    </td>
                    <td className="px-6 py-4">
                      <Badge kind={row.kind} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {sensitivity ? (
        <section>
          <SectionHeading
            title="What the fee-base gap does to the subsidy leg"
            description={
              <>
                The 75% subsidy is a flat share of childcare spending, so its cost is
                linear in the spending base. Only the under-5 slice has a published
                benchmark, so only it is rebased — the school-age third of the base is left
                as modelled. This is a scaling of the headline result, not a re-run.
              </>
            }
          />
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <div className="text-sm text-slate-500">Subsidy leg, as modelled</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">
                {formatBn(result.legs.subsidy.static_cost_bn)}
              </div>
              <div className="mt-2 text-sm text-slate-500">
                On the model&apos;s own {formatBn(sensitivity.model_childcare_expenses_bn)}{" "}
                of childcare spending, of which{" "}
                {formatBn(sensitivity.model_under_5_bn)} is under-5s. Treat as an upper
                bound.
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <div className="text-sm text-slate-500">
                Subsidy leg, on the benchmark fee base
              </div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">
                {formatBn(sensitivity.subsidy_cost_bn)}
              </div>
              <div className="mt-2 text-sm text-slate-500">
                Rebasing the under-5 slice by{" "}
                {sensitivity.under_5_slice_ratio}× — England under-5s in the model are{" "}
                {formatBn(sensitivity.model_england_under_5_bn)} against a benchmark of{" "}
                {formatBn(sensitivity.benchmark_england_under_5_bn)}. Treat as a lower
                bound.
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <div className="text-sm text-slate-500">Both legs, on that base</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">
                {formatBn(sensitivity.combined_cost_bn)}
              </div>
              <div className="mt-2 text-sm text-slate-500">
                Against {formatBn(result.legs.combined.static_cost_bn)} as modelled.
              </div>
            </div>
          </div>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600">{sensitivity.note}</p>
        </section>
      ) : null}

      <section>
        <SectionHeading
          title="Comparable published costings"
          description="What other people have put on similar proposals, and how comparable each one actually is."
        />
        <div className="space-y-3">
          {costings.map((costing) => (
            <div
              key={costing.proposal}
              className="rounded-2xl border border-slate-200 bg-white p-6"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-base font-semibold text-slate-900">
                  {costing.proposal}
                </h3>
                <span className="text-lg font-semibold text-[color:var(--pe-color-primary-600)]">
                  £{costing.cost_bn}bn
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
