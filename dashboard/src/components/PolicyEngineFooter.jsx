const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const REPO = "https://github.com/PolicyEngine/free-childcare-reform";

// The footer states what produced the numbers, not where else to go on the
// site. Versions come from the results file rather than being written here,
// so a rebuild on a different release cannot leave a stale claim behind.
export default function PolicyEngineFooter({ data }) {
  const policyengine = data?.policyengine_version;
  const dataset = data?.dataset_release ?? "Enhanced FRS 2024-25";

  return (
    <footer
      className="relative z-[1] w-full"
      style={{
        background:
          "linear-gradient(to right, var(--pe-color-primary-800, #234E52), var(--pe-color-primary-600, #2C7A7B))",
      }}
    >
      <div className="mx-auto flex max-w-[1400px] flex-col gap-3 px-6 py-8 md:px-8">
        <a
          href="https://policyengine.org/uk"
          aria-label="PolicyEngine UK home"
          className="w-fit"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`${BASE_PATH}/assets/logos/policyengine-white.svg`}
            alt="PolicyEngine"
            className="h-6 w-auto"
          />
        </a>
        <p className="m-0 text-[14px] leading-6 text-white">
          Replication code:{" "}
          <a href={REPO} className="font-medium text-white underline">
            PolicyEngine/free-childcare-reform
          </a>
          . Built with policyengine.py
          {policyengine ? ` v${policyengine}` : ""} on the {dataset}.
        </p>
        <p className="m-0 text-[13px] text-white/70">
          &copy; {new Date().getFullYear()} PolicyEngine
        </p>
      </div>
    </footer>
  );
}
