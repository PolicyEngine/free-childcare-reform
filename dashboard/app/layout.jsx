import results from "../public/data/free_childcare_reform_results.json";
import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import PolicyEngineHeader from "../src/components/PolicyEngineHeader";

import "./globals.css";

export const metadata = {
  title:
    "15 free childcare hours for all, plus a 75% subsidy: a UK costing for 2027-2029 | PolicyEngine",
  description:
    "Costing of two childcare reforms for the UK, 2027 to 2029: 15 free hours for every child from 9 months with a further 15 for working parents under £100,000, and a 75% subsidy of childcare costs replacing Tax-Free Childcare. Static and with an extensive-margin labour supply response.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <PolicyEngineHeader />
        {children}
        <PolicyEngineFooter data={results} />
      </body>
    </html>
  );
}
