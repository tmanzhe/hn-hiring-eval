"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [["/", "Overview"], ["/rungs", "Evaluation ladder"], ["/disagreements", "Label review"], ["/about", "Methodology"]];

export default function Navigation() {
  const pathname = usePathname();
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-6 gap-y-4 px-5 py-5 sm:px-8">
        <Link href="/" className="flex items-center gap-3 font-semibold tracking-tight text-slate-950">
          <span aria-hidden="true" className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-700 text-sm font-bold text-white">hn</span>
          <span>Hiring<span className="font-normal text-slate-500"> / eval</span></span>
        </Link>
        <nav aria-label="Main navigation" className="order-3 flex w-full flex-wrap gap-1 text-sm sm:order-none sm:w-auto">
          {links.map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}
            className={`rounded-lg px-3 py-2 transition-colors ${pathname === href ? "bg-slate-100 font-semibold text-slate-950" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"}`}>
            {label}
          </Link>)}
        </nav>
        <a className="text-sm font-medium text-slate-600 hover:text-orange-700" href="https://github.com/tmanzhe/hn-hiring-eval">GitHub <span aria-hidden="true">↗</span></a>
      </div>
    </header>
  );
}
