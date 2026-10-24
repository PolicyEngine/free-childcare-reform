import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import PolicyEngineHeader from "../src/components/PolicyEngineHeader";

import "./globals.css";

export const metadata = {
  title: "A two-part childcare reform: free hours and a 75% subsidy | PolicyEngine",
  description:
    "Costing of a two-part childcare reform for the UK, 2027-28 to 2029-30: 15 free hours for every child from 9 months with a further 15 for working parents under £100,000, and a 75% subsidy of childcare costs replacing Tax-Free Childcare. Static and with a labour supply response on both margins.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <PolicyEngineHeader />
        {children}
        <PolicyEngineFooter />
      </body>
    </html>
  );
}
