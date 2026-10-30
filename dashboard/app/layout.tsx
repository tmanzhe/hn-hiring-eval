import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import Navigation from "../components/Navigation";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "HN Hiring Eval · Overview", template: "%s · HN Hiring Eval" },
  description: "Structured extraction of Hacker News hiring posts, with rules-only history and a measured Haiku evaluation ladder for comparing accuracy and cost.",
};
export const dynamic = "force-static";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Navigation />
        <main id="main-content" className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14">{children}</main>
        <footer className="border-t border-slate-200">
          <div className="mx-auto flex max-w-7xl flex-wrap justify-between gap-4 px-5 py-7 text-sm text-slate-500 sm:px-8">
            <p>HN hiring posts. Rules counts. Offline evaluation.</p>
            <div className="flex gap-5"><Link href="/about" className="hover:text-slate-900">About & methodology</Link><a href="https://github.com/tmanzhe/hn-hiring-eval" className="hover:text-slate-900">Source on GitHub ↗</a></div>
          </div>
        </footer>
      </body>
    </html>
  );
}
