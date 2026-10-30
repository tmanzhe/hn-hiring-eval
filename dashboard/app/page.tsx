import Link from "next/link";
import PipelineGraph from "../components/PipelineGraph";
import { readPipeline } from "../lib/pipeline";

export default async function OverviewPage() {
  const steps = await readPipeline();

  return (
    <div className="space-y-7">
      <section className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="eyebrow text-orange-700">From source to evidence</p>
          <h1 className="page-title">Follow the extraction.</h1>
          <p className="mt-3 text-base leading-7 text-slate-600">Select a step to inspect its numbers and follow one real post.</p>
        </div>
        <Link href="/rungs" className="text-link text-sm">Evaluation ladder <span aria-hidden="true">↗</span></Link>
      </section>
      <PipelineGraph steps={steps} />
      <p className="text-xs leading-6 text-slate-500">Built from committed local data. Rules counts describe coverage; the committed Haiku ladder results describe correctness, cost and latency on 51 dev posts. <Link href="/about" className="text-link">Methodology ↗</Link></p>
    </div>
  );
}
