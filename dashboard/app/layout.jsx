import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import PolicyEngineHeader from "../src/components/PolicyEngineHeader";

import Script from "next/script";

import "./globals.css";

export const metadata = {
  title: "Two childcare reforms: free hours and a 75% subsidy | PolicyEngine",
  description:
    "Costing of two childcare reforms for the UK, 2027 to 2029: 15 free hours for every child from 9 months with a further 15 for working parents under £100,000, and a 75% subsidy of childcare costs replacing Tax-Free Childcare. Static and with a labour supply response on both margins.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <PolicyEngineHeader />
        {children}
        <PolicyEngineFooter />
        {/* Google Analytics: policyengine.org's GA4 property; this app is served at policyengine.org/uk/free-childcare-reform through a rewrite, where the main site's GA does not reach. */}
        {process.env.NODE_ENV === "production" && (
          <>
            <Script
              src="https://www.googletagmanager.com/gtag/js?id=G-2YHG89FY0N"
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-2YHG89FY0N');`}
            </Script>
          </>
        )}
      </body>
    </html>
  );
}
