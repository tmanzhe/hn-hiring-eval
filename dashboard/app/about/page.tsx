import type { Metadata } from "next";
import Link from "next/link";
import { FIELD_INFO } from "../../lib/content";
import { HISTORY_FIELDS } from "../../lib/parsers";

export const metadata: Metadata = { title: "About & methodology" };

const outcomes = [
  ["Extracted correctly", "A value is returned and matches the reference label."],
  ["Correctly left empty (abstained)", "The label is empty and the extractor returns no value too."],
  ["Missed", "The label has a value, but the extractor leaves it empty."],
  ["Wrong", "The label has a value, but the extractor returns a different, incorrect value."],
  ["Invented (hallucinated)", "The label has no value, but the extractor returns one."],
];

export default function AboutPage() {
  return (
    <div className="space-y-12">
      <section>
        <p className="eyebrow text-orange-700">About & methodology</p>
        <h1 className="page-title">Make extraction measurable.</h1>
        <p className="page-intro">This project turns HN “Who is hiring” posts into structured rows, then evaluates the extraction against labeled examples. The goal is to compare simpler rules with more involved language-model methods using the same fields and scoring rules.</p>
        <a className="text-link mt-5 inline-block text-sm" href="https://github.com/tmanzhe/hn-hiring-eval">Explore the repository on GitHub ↗</a>
      </section>

      <section className="grid gap-5 md:grid-cols-2" aria-label="Scope and current status">
        <article className="card p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-slate-950">What the overview measures</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">The history script counts non-null rules outputs once per post and field. Each history entry is a Toronto run date and thread ID; another run on that date/thread replaces that entry. The overview totals use the latest entry per thread.</p>
          <p className="mt-3 text-sm leading-7 text-slate-600">Different runs can cover different threads and numbers of posts. The chart shows extraction counts, not a measure of the hiring market or of extraction accuracy. The salary card specifically counts returned salary periods.</p>
        </article>
        <article className="card p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-slate-950">What is implemented</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">The repository includes rules extraction, normalization, field scorers and the B, C, D, E, W and F evaluation rungs. The committed ladder results cover all six rungs using Haiku (claude-haiku-5-5), dev split, N=51 posts. The rules (baseline) dev evaluation is separate: N=53, run 2026-09-22.</p>
          <p className="mt-3 text-sm leading-7 text-slate-600">These dashboard pages read local reports at build time. They do not start an extraction or model run. Missing or unreadable reports show an empty state; new reports appear after a rebuild.</p>
        </article>
      </section>

      <section id="scoring" className="scroll-mt-8" aria-labelledby="scoring-title">
        <p className="eyebrow">Correctness is separate from coverage</p>
        <h2 id="scoring-title" className="section-title mt-2">How evaluation works</h2>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">Predictions are compared with labeled posts, with development and held-out results kept separate. Company, salary and location can be missing, so their scorer distinguishes these outcomes:</p>
        <dl className="mt-5 grid gap-3 sm:grid-cols-2">
          {outcomes.map(([term, description]) => <div key={term} className="card p-5"><dt className="text-sm font-semibold text-slate-900">{term}</dt><dd className="mt-2 text-sm leading-6 text-slate-600">{description}</dd></div>)}
        </dl>
        <div className="mt-5 space-y-3 text-sm leading-7 text-slate-600">
          <p>Coverage asks how often a value is returned. Precision asks how often a returned value is correct. The hallucination rate counts invented values separately, because an empty answer and an unsupported answer need different fixes.</p>
          <p>A Wilson 95% confidence interval is an uncertainty range around a measured proportion: small samples give wider ranges, so small apparent differences may be noise. Skills use an average F1 score, which balances correct skills with missed skills, without a Wilson interval. Work arrangement and seniority use exact category agreement.</p>
          <p>The labeled set oversamples prose posts. Ladder scores are unweighted over the selected labels, so they describe those examples rather than the full population. Labels were drafted by Claude and checked by the author; <Link className="text-link" href="/disagreements">label review</Link> is intended to check possible shared-model bias.</p>
          <p>Costs use provider-reported input, output and cache tokens with supplied USD prices; they exclude charges outside token usage. Failed calls or missing usage mark cost incomplete. Timings measure wall time per post, including orchestration.</p>
        </div>
      </section>

      <section id="glossary" className="scroll-mt-8" aria-labelledby="glossary-title">
        <p className="eyebrow">Field glossary</p>
        <h2 id="glossary-title" className="section-title mt-2">What is a returned value?</h2>
        <div className="mt-5 rounded-xl border border-teal-200 bg-teal-50 p-5 text-sm leading-7 text-teal-950">
          <strong>Non-null means the field is not empty in the specific sense of null.</strong> It does not mean the answer is correct. Empty lists (<code>[]</code>) and a “no” value (<code>false</code>) count as non-null. Role titles and skills default to empty lists, so even 100% non-null does not mean every post has an identified title or skill.
        </div>
        <div className="table-scroll mt-5"><table>
          <caption>The extraction schema defines these fields for each post. History counts them before normalization; salary amounts need both currency and pay period to be interpreted.</caption>
          <thead><tr><th scope="col">Field</th><th scope="col">Meaning</th></tr></thead>
          <tbody>{HISTORY_FIELDS.map((field) => <tr key={field} id={`field-${field}`} className="scroll-mt-8"><th scope="row" className="align-top"><span className="block whitespace-nowrap">{FIELD_INFO[field].label}</span><code className="mt-1 block font-normal text-slate-500">{field}</code></th><td className="leading-7">{FIELD_INFO[field].description}</td></tr>)}</tbody>
        </table></div>
        <div className="card mt-5 p-6">
          <h3 className="font-semibold text-slate-900">The stored posting adds provenance</h3>
          <p className="mt-2 text-sm leading-7 text-slate-600">The pipeline adds three fields that are not counted in extraction history: <code>comment_id</code> identifies the HN post, <code>thread_date</code> records the thread’s date, and <code>extracted_by</code> records rules or LLM as the extraction source. The model is not asked to guess this metadata.</p>
        </div>
      </section>
    </div>
  );
}
