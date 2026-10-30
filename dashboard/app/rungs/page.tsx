import type { Metadata } from "next";
import Link from "next/link";
import RungsTable from "../../components/RungsTable";
import EmptyState from "../../components/EmptyState";
import { COMMANDS, readRungs } from "../../lib/data";
import { RUNGS } from "../../lib/content";

export const metadata: Metadata = { title: "Evaluation ladder" };

export default async function RungsPage() {
  const rows = await readRungs();
  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow text-orange-700">The experiment</p>
        <h1 className="page-title">Does added complexity help?</h1>
        <p className="page-intro">The ladder compares extraction methods on the same labeled posts. It is built to measure what changes when an LLM gets tools, guidance, a rules first pass or a fixed sequence of steps.</p>
        <p className="mt-5 rounded-xl border border-orange-200 bg-orange-50 px-5 py-4 text-sm leading-7 text-orange-950"><strong>Implemented, not yet measured on real data.</strong> B, C, D, E, W and F are implemented. The ladder has not been run on real data, so no real-data accuracy, cost or speed comparison is available.</p>
      </section>

      <section aria-labelledby="methods-title">
        <h2 id="methods-title" className="section-title">Meet the methods</h2>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">Rules use code to read familiar post patterns. An LLM is a language model that reads the post; in B–E, it also decides when to call its tools. W and F use steps chosen by code.</p>
        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {RUNGS.map((rung) => <article key={rung.id} className="card p-6">
            <div className="flex items-center gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 font-mono font-semibold text-slate-800">{rung.id}</span><h3 className="font-semibold text-slate-900">{rung.title}</h3></div>
            <p className="mt-4 text-sm leading-7 text-slate-600">{rung.description}</p>
          </article>)}
        </div>
      </section>

      <section aria-labelledby="results-title">
        <h2 id="results-title" className="section-title">Accuracy & cost report</h2>
        <p className="mb-5 mt-3 text-sm leading-7 text-slate-600">This area reads the local ladder report when one is available. Scores compare predictions with reference labels; they do not come from the rules history counts.</p>
        {rows ? <RungsTable rows={rows} /> : <EmptyState title="The comparison will appear after a ladder run" command={COMMANDS.rungs}
          prerequisite="Requires labeled posts and their source posts in data/raw/, plus ANTHROPIC_API_KEY, a pinned STRONG_MODEL, all four LLM_*_USD_PER_MTOK rates and LLM_PRICE_SOURCE in .env. This command makes paid model calls.">
          There is no readable ladder report here yet. A run will produce field scores, uncertainty ranges, token-based USD costs and per-post timings for each method and dataset split.
        </EmptyState>}
      </section>

      <section className="card p-6 sm:p-8" aria-labelledby="scores-title">
        <h2 id="scores-title" className="text-xl font-semibold text-slate-950">How to read the scores</h2>
        <dl className="mt-5 grid gap-6 text-sm leading-7 md:grid-cols-2">
          <div><dt className="font-semibold text-slate-900">Accuracy & precision</dt><dd className="mt-1 text-slate-600">For company, salary and location, accuracy includes correct answers and correctly empty answers. Precision asks: when it returned a value, how often was it right?</dd></div>
          <div><dt className="font-semibold text-slate-900">Wilson 95% confidence interval (CI)</dt><dd className="mt-1 text-slate-600">An uncertainty range for a measured proportion; wider ranges mean less certainty from the available sample. Small differences within these ranges are not convincing evidence of improvement.</dd></div>
          <div><dt className="font-semibold text-slate-900">Skills F1 & category accuracy</dt><dd className="mt-1 text-slate-600">Skills F1 balances correct skills returned with skills missed, averaged across posts from 0 to 1; higher is better. It has no Wilson interval. Work arrangement and seniority use exact category accuracy.</dd></div>
          <div><dt className="font-semibold text-slate-900">Dataset split & sample size</dt><dd className="mt-1 text-slate-600">“Dev” is for tuning; “held-out” is a separate check. The n column counts labeled posts. Scores are unweighted over selected labels, not estimates for all HN posts.</dd></div>
          <div><dt className="font-semibold text-slate-900">Cost & incomplete usage</dt><dd className="mt-1 text-slate-600">Cost uses reported tokens and supplied USD prices for a whole method/split, repeated across its field rows. Do not add those rows. Failed calls or missing usage make cost incomplete.</dd></div>
          <div><dt className="font-semibold text-slate-900">Time per post</dt><dd className="mt-1 text-slate-600">p50 is the median processing time. p95 is the time at or below which 95% of posts finished. Both include orchestration and are shown in milliseconds.</dd></div>
        </dl>
        <p className="mt-6 border-t border-slate-100 pt-5 text-sm text-slate-600">Missing information and invented answers have different consequences. <Link className="text-link" href="/about#scoring">Read the scoring method →</Link></p>
      </section>
    </div>
  );
}
