"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import BaselineTab from "../src/components/BaselineTab";
import BenchmarkTab from "../src/components/BenchmarkTab";
import CostTab from "../src/components/CostTab";
import DistributionTab from "../src/components/DistributionTab";
import MethodologyTab from "../src/components/MethodologyTab";

const TAB_OPTIONS = [
  { id: "cost", label: "Budget impact" },
  { id: "baseline", label: "Baseline" },
  { id: "distribution", label: "Household effects" },
  { id: "methodology", label: "Methodology" },
];

function getInitialTab(tabParam) {
  return TAB_OPTIONS.some((tab) => tab.id === tabParam) ? tabParam : "cost";
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
    router.replace(tab === "cost" ? "/" : `/?tab=${tab}`, { scroll: false });
  }

  return (
    <div className="app-shell min-h-screen">
      <header className="title-row">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4 md:px-8">
          <h1>
            15 free childcare hours for all, plus a 75% subsidy
          </h1>
        </div>
      </header>

      <main className="relative z-[1] mx-auto max-w-[1400px] px-6 py-10 md:px-8 md:py-12">
        <p className="mb-3 text-[1.05rem] leading-relaxed text-slate-600">
          This dashboard uses{" "}
          <a href="https://policyengine.org" target="_blank" rel="noreferrer" className="underline">
            PolicyEngine
          </a>{" "}
          UK&apos;s microsimulation to cost a two-part childcare reform for{" "}
          <strong>2027, 2028 and 2029</strong>. The first part replaces today&apos;s split —
          30 free hours for working parents earning under £100,000, 15 hours for 3-4 year
          olds — with <strong>15 hours free for every child from 9 months to school age</strong>,
          plus a further 15 hours where parents work and earn under £100,000. The second
          replaces Tax-Free Childcare with a <strong>75% subsidy of childcare costs for
          all</strong>, keeping the Universal Credit childcare element. The{" "}
          <TabLink onSelect={() => handleTabChange("cost")}>Budget impact</TabLink> tab
          reports the cost both statically and with an extensive-margin labour supply
          response. The{" "}
          <TabLink onSelect={() => handleTabChange("distribution")}>Household effects</TabLink>{" "}
          tab shows who gains, by income quintile. The{" "}
          <TabLink onSelect={() => handleTabChange("baseline")}>Baseline</TabLink> tab sets
          the modelled baseline for each childcare programme against its published figure,
          on spending and on children covered, and checks the rest against published
          outturns and comparable costings. It is the place to start if you want to know how
          much weight the headline numbers bear. The{" "}
          <TabLink onSelect={() => handleTabChange("methodology")}>Methodology</TabLink> tab
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
            {activeTab === "cost" && (
              <CostTab data={data} year={year} onYearChange={setYear} />
            )}
            {activeTab === "distribution" && (
              <DistributionTab data={data} year={year} onYearChange={setYear} />
            )}
            {activeTab === "baseline" && (
              <div className="space-y-10">
                <BaselineTab data={data} year={year} />
                <BenchmarkTab data={data} year={year} />
              </div>
            )}
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
            <a href="https://pypi.org/project/policyengine-uk/" target="_blank" rel="noreferrer">
              policyengine-uk
            </a>{" "}
            v{data?.policyengine_uk_version} on the Enhanced FRS 2024-25.
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
