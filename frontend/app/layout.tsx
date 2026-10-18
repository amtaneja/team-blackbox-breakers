import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Auditly | Invoice and PO Review",
    template: "%s | Auditly",
  },
  description: "Auditly extracts invoice and purchase order details from labeled emails and creates comparison summaries for review.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
