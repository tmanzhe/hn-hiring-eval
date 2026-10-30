import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = { title: "HN hiring eval dashboard" };
export const dynamic = "force-static";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav aria-label="Main navigation">
          <Link href="/">Trend</Link>{" | "}
          <Link href="/rungs">Rungs</Link>{" | "}
          <Link href="/disagreements">Disagreements</Link>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
