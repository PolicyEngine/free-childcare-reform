const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

// Brand bar only. The policyengine.org site nav (Research, Model, API, About,
// Donate) is deliberately not rendered here: this page is a single analysis,
// and a nav that leads away from it is not what a reader of the costing
// needs. The logo still links home.
export default function PolicyEngineHeader() {
  return (
    <nav
      className="relative z-[1] w-full"
      style={{
        background:
          "linear-gradient(to right, var(--pe-color-primary-800, #234E52), var(--pe-color-primary-600, #2C7A7B))",
      }}
    >
      <div className="mx-auto flex h-[58px] max-w-[1400px] items-center px-6 md:px-8">
        <a
          href="https://policyengine.org/uk"
          aria-label="PolicyEngine UK home"
          className="flex flex-shrink-0 items-center"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`${BASE_PATH}/assets/logos/policyengine-white.svg`}
            alt="PolicyEngine"
            className="h-6 w-auto"
          />
        </a>
      </div>
    </nav>
  );
}
