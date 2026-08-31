import "./globals.css";

export const metadata = {
  title: "Childcare reform costing | PolicyEngine",
  description:
    "Costing of two childcare reforms for the UK, 2027 to 2029: 15 free hours for every child from 9 months with a further 15 for working parents under £100,000, and a 75% subsidy of childcare costs replacing Tax-Free Childcare. Static and with an extensive-margin labour supply response.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
