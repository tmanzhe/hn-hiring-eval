import Link from "next/link";
import TrendChart from "../components/TrendChart";
import EmptyState from "../components/EmptyState";
import { COMMANDS, readHistory } from "../lib/data";
import { FIELD_INFO, formatCount, formatDate, formatPercent } from "../lib/content";
import { HISTORY_FIELDS, type HistoryRow } from "../lib/parsers";

const steps = [
  ["Collect posts", "Read top-level job posts from monthly HN “Who is hiring” threads."],
  ["Extract fields", "Use rules to identify company, location, salary and other details. LLM methods are also implemented."],
  ["Normalize values", "Standardize skills and annualize salary amounts for the stored dataset."],
  ["Evaluate separately", "Compare predictions with labeled posts, keeping correctness, omissions and invented values visible."],
];

export default async function OverviewPage() {
  const rows = await readHistory();
  // Sum only the latest snapshot of each thread so repeated runs are not double-counted.
  const threads = new Map<string, HistoryRow>();
  rows?.forEach((row) => threads.set(row.thread_id, row));
  const snapshots = [...threads.values()];
  const posts = snapshots.reduce((sum, row) => sum + row.total_posts, 0);
  const salary = snapshots.reduce((sum, row) => sum + row.salary_period, 0);
  const latest = rows?.[rows.length - 1];
  const stats = [
    { label: "Posts analyzed", value: rows ? formatCount(posts) : "—", note: "Rules pass · latest run per thread" },
    { label: "Hiring threads", value: rows ? formatCount(threads.size) : "—", note: "Distinct HN threads in the history" },
    { label: "Fields tracked", value: formatCount(HISTORY_FIELDS.length), note: "Company, salary, skills and more" },
    { label: "Salary period found", value: rows ? formatPercent(salary, posts) : "—", note: rows ? `${formatCount(salary)} of ${formatCount(posts)} posts returned a pay period` : "Share of posts with a returned pay period" },
  ];

  return (
    <div className="space-y-12 sm:space-y-16">
      <section className="grid items-center gap-8 lg:grid-cols-[1.55fr_1fr] lg:gap-16">
        <div>
          <p className="eyebrow text-orange-700">Hacker News · Hiring extraction & evaluation</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-[1.12] tracking-tight text-slate-950 sm:text-6xl">From hiring posts<br className="hidden sm:block" /> to structured facts.</h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">Structured extraction of HN “Who is hiring” posts, with an evaluation ladder from rules to language models (LLMs) built to compare accuracy and cost.</p>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">A job post can mix salary, funding figures and several roles in one paragraph. This project asks how much extra model complexity helps extract the right details, and what it costs.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/rungs" className="rounded-lg bg-slate-900 px-5 py-3 text-sm font-medium text-white hover:bg-slate-700">Explore the evaluation ladder <span aria-hidden="true">→</span></Link>
            <Link href="/about" className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-100">Read the methodology</Link>
          </div>
        </div>
        <aside className="rounded-2xl bg-slate-900 p-7 text-white sm:p-8">
          <p className="eyebrow text-orange-300">The question behind the project</p>
          <h2 className="mt-4 text-2xl font-medium leading-snug sm:text-3xl">When does an LLM earn its added cost?</h2>
          <div className="mt-7 space-y-4 border-t border-slate-700 pt-6 text-sm">
            <p className="flex items-start gap-3"><span aria-hidden="true" className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-teal-300" /><span><strong className="font-medium text-white">Rules history</strong><br /><span className="text-slate-300">{rows ? "Local extraction counts available" : "Waiting for local extraction counts"}</span></span></p>
            <p className="flex items-start gap-3"><span aria-hidden="true" className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-orange-300" /><span><strong className="font-medium text-white">LLM ladder: implemented</strong><br /><span className="text-slate-300">Not run on real data. No accuracy or cost results yet.</span></span></p>
          </div>
        </aside>
      </section>

      <section aria-label="Rules history at a glance">
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {stats.map((stat) => <div key={stat.label} className="card p-4 sm:p-6">
            <p className="text-sm font-medium text-slate-600">{stat.label}</p>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 tabular-nums sm:text-4xl">{stat.value}</p>
            <p className="mt-3 text-xs leading-5 text-slate-500">{stat.note}</p>
          </div>)}
        </div>
        <p className="mt-3 text-xs leading-6 text-slate-500">{rows ? "Counts use the latest recorded run for each thread in data/rules_history.jsonl; reruns are not added together. Salary period is a coverage indicator, not a check of salary correctness." : "History statistics will appear when a local rules report is available. The schema field count comes from the extraction schema."}</p>
      </section>

      <section aria-labelledby="pipeline-title">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><p className="eyebrow">From source to evaluation</p><h2 id="pipeline-title" className="section-title mt-2">How it works</h2></div><Link href="/about" className="text-link text-sm">See the method <span aria-hidden="true">↗</span></Link></div>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map(([title, description], i) => <li key={title} className="card p-5">
            <span className="font-mono text-sm text-orange-700">0{i + 1}</span>
            <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
          </li>)}
        </ol>
        <p className="mt-3 text-xs leading-6 text-slate-500">The history below records the rules pass before normalization. Evaluation against labels is a separate offline step.</p>
      </section>

      <section aria-labelledby="history-title">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><p className="eyebrow">Rules only</p><h2 id="history-title" className="section-title mt-2">Extraction history</h2></div><Link href="/about#glossary" className="text-link text-sm">What do these fields mean?</Link></div>
        {rows ? <div className="card p-4 sm:p-7"><TrendChart rows={rows} /></div> : <EmptyState title="Your extraction history will appear here" command={COMMANDS.history}>Once a rules report is available, this chart will show how many posts returned each field in each recorded run.</EmptyState>}
      </section>

      <section aria-labelledby="latest-title">
        <div className="mb-5"><p className="eyebrow">One recorded run</p><h2 id="latest-title" className="section-title mt-2">Latest counts</h2>
          {latest && <p className="mt-3 text-sm leading-6 text-slate-600">{formatDate(latest.date)} (Toronto run date) · <a className="text-link" href={`https://news.ycombinator.com/item?id=${encodeURIComponent(latest.thread_id)}`}>Thread {latest.thread_id} ↗</a> · {formatCount(latest.total_posts)} posts</p>}
        </div>
        {latest ? <div className="table-scroll"><table>
          <caption>Posts where rules returned a value (non-null) in the latest date/thread entry. The share divides each count by {formatCount(latest.total_posts)} posts. Empty lists and false count too; a returned value may be wrong.</caption>
          <thead><tr><th scope="col">Extracted field</th><th scope="col" className="text-right">Posts with a value</th><th scope="col" className="text-right">Share of posts</th></tr></thead>
          <tbody>{HISTORY_FIELDS.map((field) => <tr key={field}>
            <th scope="row"><a href={`/about#field-${field}`} className="hover:text-orange-700">{FIELD_INFO[field].label}</a><code className="mt-1 block font-normal text-slate-500">{field}</code></th>
            <td className="text-right tabular-nums">{formatCount(latest[field])}</td>
            <td><div className="flex items-center justify-end gap-4"><div aria-hidden="true" className="hidden h-1.5 w-24 overflow-hidden rounded-full bg-slate-100 sm:block"><div className="h-full rounded-full bg-teal-600" style={{ width: latest.total_posts ? `${latest[field] / latest.total_posts * 100}%` : "0%" }} /></div><span className="min-w-14 text-right tabular-nums">{formatPercent(latest[field], latest.total_posts)}</span></div></td>
          </tr>)}</tbody>
        </table></div> : <EmptyState title="Field counts will appear here" command={COMMANDS.history}>The latest run will list each field, its returned-value count and its share of the analyzed posts.</EmptyState>}
      </section>
    </div>
  );
}
