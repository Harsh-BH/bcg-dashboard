import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";

const dmSans = DM_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-dm-sans",
});

export const metadata: Metadata = {
  title: "Headcount Dashboard",
  description: "BCG HR Headcount Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`h-full antialiased ${dmSans.variable}`}>
      <body className="min-h-full font-[family-name:var(--font-dm-sans)]">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
