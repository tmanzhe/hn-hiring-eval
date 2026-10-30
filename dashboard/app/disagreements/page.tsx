import type { Metadata } from "next";
import Link from "next/link";
import RunLabel from "../../components/RunLabel";
import DisagreementsTable from "../../components/DisagreementsTable";
import EmptyState from "../../components/EmptyState";
import { COMMANDS, readDisagreements, readRungs } from "../../lib/data";

export const metadata: Metadata = { title: "Label review" };

export default async function DisagreementsPage() {
  const [entries, rows] = await Promise.all([readDisagreements(), readRungs()]);
  return (
    <div className="space-y-8">
      <section>
        <p className="eyebrow text-orange-700">Check the reference answers</p>
        <h1 className="page-title">Where do answers disagree?</h1>
        <p className="page-intro">A disagreement means the model’s answer differs from a reference label. Review the original post to decide whether the extraction, the label or both need attention.</p>
        <RunLabel rows={rows ?? []} />
      </section>
      <aside className="card p-6 text-sm leading-7 text-slate-600">
        <h2 className="font-semibold text-slate-900">Why review the labels?</h2>
        <p className="mt-2">Claude drafted the labels from raw posts without seeing the parser’s answers, and the author checked each label. The LLM methods also use Claude, so shared model preferences could affect the comparison. This report is designed to help audit that risk.</p>
        <p className="mt-3">The committed report compares all six Haiku rungs with the reference labels. <Link href="/rungs" className="text-link">See the methods →</Link></p>
      </aside>
      {entries ? <>
        <p className="text-sm leading-7 text-slate-600">Compare label and model values side by side. Salary labels keep their recorded pay period; model salary bounds are annualized for scoring. Only company, salary, location, skills, work arrangement and seniority are checked.</p>
        <DisagreementsTable entries={entries} />
      </> : <EmptyState title="There are no review results to show yet" command={COMMANDS.disagreements}
        prerequisite="Requires labeled posts and their source posts in data/raw/, plus ANTHROPIC_API_KEY, a pinned STRONG_MODEL, all four LLM_*_USD_PER_MTOK rates and LLM_PRICE_SOURCE in .env. This command makes paid model calls.">
        After a ladder run with disagreement reporting, this page will list answers that differ from the reference labels. You’ll be able to filter by field and search for a post or value.
      </EmptyState>}
    </div>
  );
}
