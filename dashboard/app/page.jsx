"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { formatFiscalYear } from "../src/lib/formatters";
import BaselineTab from "../src/components/BaselineTab";
import CostTab from "../src/components/CostTab";
import DistributionTab from "../src/components/DistributionTab";
import MethodologyTab from "../src/components/MethodologyTab";

const TAB_OPTIONS = [
  { id: "reform", label: "Reform" },
  { id: "baseline", label: "Baseline" },
  { id: "methodology", label: "Methodology" },
];

function getInitialTab(tabParam) {
  return TAB_OPTIONS.some((tab) => tab.id === tabParam) ? tabParam : "reform";
}

const SELECT_CLASS =
  "h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)] focus:ring-2 focus:ring-[color:var(--pe-color-primary-100)]";

const FIELD_LABEL_CLASS = "mb-1 block text-xs font-medium text-slate-500";

// A labelled switch. Tinted when on, so the state reads at a glance, unlike
// two pills that both look "selected".
function Toggle({ on, onChange, label, hint }) {
  return (
    <label className="flex cursor-pointer items-center gap-2 whitespace-nowrap" title={hint}>
      <button
        type="button"
        role="switch"
        aria-checked={on}
        onClick={() => onChange(!on)}
        className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${
          on ? "bg-[color:var(--pe-color-primary-600)]" : "bg-slate-300"
        }`}
      >
        <span
          className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${
            on ? "translate-x-4" : "translate-x-0.5"
          }`}
        />
      </button>
      <span className={on ? "font-medium text-slate-800" : "text-slate-500"}>{label}</span>
    </label>
  );
}

function Dashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState(() => getInitialTab(searchParams.get("tab")));
  const [data, setData] = useState(null);
  const [year, setYear] = useState(null);
  // Sub-tabs within "The reform": what it costs, and who gains.
  const [reformView, setReformView] = useState("budget");
  // Shared by both reform views, so the controls sit above the switcher.
  const [bound, setBound] = useState("central");
  // The two labour supply margins switch on independently. `bound` is "none"
  // when the extensive margin is off; the intensive margin has one setting.
  const [extensive, setExtensive] = useState(true);
  const [intensive, setIntensive] = useState(true);
  const effectiveBound = extensive ? bound : "none";
  const [area, setArea] = useState("uk");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setActiveTab(getInitialTab(searchParams.get("tab")));
  }, [searchParams]);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/data/free_childcare_reform_results.json`,
        );
        if (!res.ok) {
          throw new Error(
            "free_childcare_reform_results.json not found; run the pipeline first",
          );
        }
        const payload = await res.json();
        setData(payload);
        setYear(payload.years[0]);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  function handleTabChange(tab) {
    setActiveTab(tab);
    router.replace(tab === "reform" ? "/" : `/?tab=${tab}`, { scroll: false });
  }

  return (
    <div className="app-shell min-h-screen">
      <header className="title-row">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4 md:px-8">
          <h1>A two-part childcare reform: free hours and a 75% subsidy</h1>
        </div>
      </header>

      <main className="relative z-[1] mx-auto max-w-[1400px] px-6 py-10 md:px-8 md:py-12">
        <p className="mb-3 text-[1.05rem] leading-relaxed text-slate-600">
          This dashboard uses{" "}
          <a href="https://policyengine.org" target="_blank" rel="noreferrer" className="underline">
            PolicyEngine
          </a>{" "}
          UK to cost a two-part childcare reform for <strong>2027-28 to 2029-30</strong>.
          The first leg gives <strong>15 free hours to every child</strong> from 9 months,
          plus 15 more for working parents under £100,000; the second replaces Tax-Free
          Childcare with a <strong>75% subsidy of childcare costs</strong>.
        </p>

        <div className="mb-8 mt-8 flex w-fit flex-wrap border-b-2 border-slate-200">
          {TAB_OPTIONS.map((tab) => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => handleTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <p className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
            Error: {error}
          </p>
        )}
        {loading && !error && (
          <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
            Loading data...
          </p>
        )}

        {!loading && !error && data && year && (
          <>
            {activeTab === "reform" && (
              <div>
                <div className="mb-6">
                  {/* One row: the view switch first, then the filters; wraps on phones. */}
                  <div className="flex flex-wrap items-end gap-x-5 gap-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="w-full sm:w-auto">
                      <span className={FIELD_LABEL_CLASS}>View</span>
                      <div
                        role="tablist"
                        aria-label="Reform view"
                        className="grid h-10 w-full grid-cols-2 gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1 sm:inline-grid sm:w-auto"
                      >
                        {[
                          { id: "budget", label: "Budget impact" },
                          { id: "households", label: "Household effects" },
                        ].map((view) => (
                          <button
                            key={view.id}
                            type="button"
                            role="tab"
                            aria-selected={reformView === view.id}
                            onClick={() => setReformView(view.id)}
                            className={`h-full whitespace-nowrap rounded-md px-3 text-sm font-semibold transition-colors sm:px-4 ${
                              reformView === view.id
                                ? "bg-white text-[color:var(--pe-color-primary-700)] shadow-sm ring-1 ring-slate-200"
                                : "text-slate-500 hover:text-slate-700"
                            }`}
                          >
                            {view.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    <span className="hidden h-10 w-px self-end bg-slate-200 sm:block" aria-hidden />
                    <label className="w-28 shrink-0">
                      <span className={FIELD_LABEL_CLASS}>Year</span>
                      <select
                        value={year}
                        onChange={(event) => setYear(Number(event.target.value))}
                        className={SELECT_CLASS}
                      >
                        {data.years.map((y) => (
                          <option key={y} value={y}>
                            {formatFiscalYear(y)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="w-28 shrink-0">
                      <span className={FIELD_LABEL_CLASS}>Area</span>
                      <select
                        value={area}
                        onChange={(event) => setArea(event.target.value)}
                        className={SELECT_CLASS}
                      >
                        <option value="uk">UK</option>
                        <option value="england">England</option>
                      </select>
                    </label>
                    <div className="min-w-0 max-w-full">
                      <span className={FIELD_LABEL_CLASS}>Labour supply response</span>
                      <div className="flex min-h-10 flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm sm:py-0">
                        <Toggle
                          on={extensive}
                          onChange={setExtensive}
                          label="Participation"
                          hint="Extensive margin: whether parents work, using OBR elasticities on the gain to work"
                        />
                        {extensive ? (
                          <select
                            value={bound}
                            onChange={(event) => setBound(event.target.value)}
                            className="h-7 rounded-md border-0 bg-slate-100 px-2 text-xs font-medium text-slate-700 outline-none focus:border-[color:var(--pe-color-primary-500)]"
                            aria-label="Participation elasticity"
                            title="Participation (extensive margin) elasticity"
                          >
                            <option value="central">
                              Central (OBR as published)
                            </option>
                            <option value="low">
                              Low ({Number((data.assumptions || {}).elasticity_scale_low ?? 0.33).toFixed(2)}×)
                            </option>
                            <option value="high">
                              High ({Number((data.assumptions || {}).elasticity_scale_high ?? 2)}×)
                            </option>
                          </select>
                        ) : null}
                        <span className="hidden h-5 w-px bg-slate-200 sm:block" aria-hidden />
                        <Toggle
                          on={intensive}
                          onChange={setIntensive}
                          label="Hours"
                          hint={`Intensive margin: hours worked by parents already in work, elasticity ${(data.assumptions || {}).hours_price_elasticity}`}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {reformView === "budget" ? (
                  <CostTab
                    data={data}
                    year={year}
                    bound={effectiveBound}
                    intensive={intensive}
                    area={area}
                    onTabChange={handleTabChange}
                  />
                ) : (
                  <DistributionTab
                    data={data}
                    year={year}
                    bound={effectiveBound}
                    intensive={intensive}
                    area={area}
                    onTabChange={handleTabChange}
                  />
                )}
              </div>
            )}
            {activeTab === "baseline" && <BaselineTab data={data} year={year} />}
            {activeTab === "methodology" && <MethodologyTab data={data} year={year} onTabChange={handleTabChange} />}
          </>
        )}

        <footer className="mt-12 border-t border-slate-200 pt-8 text-center text-sm text-slate-500">
          <p>
            Replication code:{" "}
            <a
              href="https://github.com/PolicyEngine/free-childcare-reform"
              target="_blank"
              rel="noreferrer"
            >
              PolicyEngine/free-childcare-reform
            </a>
            . Built with{" "}
            <a href="https://pypi.org/project/policyengine/" target="_blank" rel="noreferrer">
              policyengine.py
            </a>{" "}
            v{data?.policyengine_version}
          </p>
        </footer>
      </main>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<p className="p-12 text-center text-slate-500">Loading...</p>}>
      <Dashboard />
    </Suspense>
  );
}
