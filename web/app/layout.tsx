import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "hn-hiring-eval",
  description:
    "Structured job data from HN 'Who is hiring' threads, published alongside the eval harness that measures it.",
};

const NAV = [
  { href: "/", label: "match" },
  { href: "/jobs", label: "jobs" },
  { href: "/trends", label: "trends" },
  { href: "/evals", label: "evals" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <header className="border-b border-line">
          <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-6 gap-y-2 px-6 py-5">
            <Link href="/" className="font-mono text-sm font-semibold tracking-tight">
              hn-hiring-eval
            </Link>
            <nav className="flex gap-5 font-mono text-sm text-muted">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href} className="hover:text-accent">
                  {n.label}
                </Link>
              ))}
            </nav>
            <a
              href="https://github.com/tmanzhe/hn-hiring-eval"
              className="ml-auto font-mono text-sm text-muted hover:text-accent"
            >
              source
            </a>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
        <footer className="mx-auto max-w-5xl px-6 pb-12 pt-4 text-sm text-muted">
          Counting, ranking and filtering are SQL. The model reads a resume and writes one
          summary. It is never asked for a number.
        </footer>
      </body>
    </html>
  );
}
