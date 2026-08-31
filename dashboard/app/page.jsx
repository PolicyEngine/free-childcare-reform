"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import BaselineTab from "../src/components/BaselineTab";
import CostTab from "../src/components/CostTab";
import DistributionTab from "../src/components/DistributionTab";
import MethodologyTab from "../src/components/MethodologyTab";

const TAB_OPTIONS = [
  { id: "reform", label: "The reform" },
  { id: "baseline", label: "Baseline" },
  { id: "methodology", label: "Methodology" },
];

function getInitialTab(tabParam) {
  return TAB_OPTIONS.some((tab) => tab.id === tabParam) ? tabParam : "reform";
}

function TabLink({ onSelect, children }) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className="font-semibold text-[color:var(--pe-color-primary-600)] underline decoration-1 underline-offset-2 transition-opacity hover:opacity-80"
    >
      {children}
    </button>
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
          <h1>Costing a two-part childcare reform</h1>
        </div>
      </header>

      <main className="relative z-[1] mx-auto max-w-[1400px] px-6 py-10 md:px-8 md:py-12">
        <p className="mb-3 text-[1.05rem] leading-relaxed text-slate-600">
          This dashboard uses{" "}
          <a href="https://policyengine.org" target="_blank" rel="noreferrer" className="underline">
            PolicyEngine
          </a>{" "}
          UK&apos;s microsimulation to cost a two-part childcare reform for{" "}
          <strong>2027-28 to 2029-30</strong>. The first replaces today&apos;s split — 30
          free hours for working parents earning under £100,000, 15 hours for 3-4 year
          olds — with <strong>15 hours free for every child</strong> from 9 months to
          school age, plus a further 15 hours where parents work and earn under £100,000.
          The second replaces Tax-Free Childcare with a{" "}
          <strong>75% subsidy of childcare costs for all</strong>, keeping the Universal
          Credit childcare element. The{" "}
          <TabLink onSelect={() => handleTabChange("reform")}>reform</TabLink> tab reports
          what each leg costs and who gains;{" "}
          <TabLink onSelect={() => handleTabChange("baseline")}>Baseline</TabLink> sets the
          modelled baseline against published figures, and is the place to judge how much
          weight the headline bears;{" "}
          <TabLink onSelect={() => handleTabChange("methodology")}>Methodology</TabLink>{" "}
          explains how each result is computed, with a source for every assumption.
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
                <div className="mb-8 flex w-fit gap-1 rounded-xl bg-slate-100 p-1">
                  {[
                    { id: "budget", label: "Budget impact" },
                    { id: "households", label: "Household effects" },
                  ].map((view) => (
                    <button
                      key={view.id}
                      type="button"
                      onClick={() => setReformView(view.id)}
                      className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
                        reformView === view.id
                          ? "bg-white text-slate-900 shadow-sm"
                          : "text-slate-500 hover:text-slate-700"
                      }`}
                    >
                      {view.label}
                    </button>
                  ))}
                </div>
                {reformView === "budget" ? (
                  <CostTab data={data} year={year} onYearChange={setYear} />
                ) : (
                  <DistributionTab data={data} year={year} onYearChange={setYear} />
                )}
              </div>
            )}
            {activeTab === "baseline" && <BaselineTab data={data} year={year} />}
            {activeTab === "methodology" && <MethodologyTab data={data} year={year} />}
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
            v{data?.policyengine_version} on the Enhanced FRS 2024-25.
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
