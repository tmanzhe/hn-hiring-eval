import { ApiDown, getEvals, type EvalsPayload } from "@/lib/api";

export const dynamic = "force-dynamic";

type Nullable = {
  n: number;
  coverage: number;
  precision: number;
  precision_ci95: [number, number];
  precision_margin: number;
  hallucination_rate: number;
  outcomes: Record<string, number>;
};
type SetField = { n: number; macro_f1: number; macro_precision: number; macro_recall: number };
type EnumField = { n: number; accuracy: number; per_class_recall?: Record<string, number> };
type Run = {
  run_id: string;
  ts: string;
  config: string;
  split: string;
  model: string;
  prompt_sha: string;
  n: number;
  p50_ms: number;
  p95_ms: number;
  scores: Record<string, Nullable | SetField | EnumField>;
  slices?: Record<string, { n: number; skills_f1: number }>;
};

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
const isNullable = (s: object): s is Nullable => "precision_ci95" in s;
const isSet = (s: object): s is SetField => "macro_f1" in s;

function Bar({ lo, hi, point }: { lo: number; hi: number; point: number }) {
  return (
    <span className="relative inline-block h-2 w-28 rounded bg-line align-middle">
      <span
        className="absolute h-2 rounded bg-accent/30"
        style={{ left: `${lo * 100}%`, width: `${Math.max(1, (hi - lo) * 100)}%` }}
      />
      <span className="absolute h-2 w-0.5 bg-accent" style={{ left: `${point * 100}%` }} />
    </span>
  );
}

export default async function EvalsPage() {
  let payload: EvalsPayload | null = null;
  let down: string | null = null;
  try {
    payload = await getEvals();
  } catch (e) {
    down = e instanceof ApiDown ? e.message : "the API failed";
  }

  const runs = (payload?.runs ?? []) as unknown as Run[];
  const latest = runs.length ? runs[runs.length - 1] : null;

  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Evals</h1>
        <p className="max-w-2xl text-muted">
          Every run recorded so far, served from the same file the harness writes. Most projects
          bury this in a README. Putting it in the product means the numbers are as inspectable as
          the thing they measure, including when there are none.
        </p>
      </section>

      {down && (
        <p className="rounded-lg border border-line bg-panel p-4 font-mono text-sm text-accent">
          {down}
        </p>
      )}

      {!down && runs.length === 0 && (
        <section className="space-y-3 rounded-lg border border-line bg-panel p-6">
          <h2 className="font-mono text-sm">no runs yet</h2>
          <p className="max-w-2xl text-muted">
            The harness is built and the sample is drawn, but the 80 posts are not labeled, so
            nothing has been scored. This page stays empty until{" "}
            <code className="font-mono text-xs">evals/runs.jsonl</code> has a row in it. A
            placeholder number here would be worse than an empty page, because it would be the one
            number on the site nobody could check.
          </p>
          <pre className="overflow-x-auto rounded border border-line p-3 font-mono text-xs text-muted">
{`uv run evals/label.py                 # write ground truth, resumable
uv run evals/run.py --config rules    # baseline, appends one row`}
          </pre>
        </section>
      )}

      {latest && (
        <>
          <section className="space-y-3">
            <h2 className="font-mono text-sm text-muted">
              latest · {latest.config} · {latest.split} split · n={latest.n} · {latest.model} ·
              prompt {latest.prompt_sha}
            </h2>
            <div className="overflow-x-auto rounded-lg border border-line">
              <table className="w-full text-sm">
                <thead className="bg-panel text-left font-mono text-xs text-muted">
                  <tr>
                    {["field", "coverage", "precision", "95% interval", "hallucinated"].map((h) => (
                      <th key={h} className="border-b border-line px-3 py-2 font-normal">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(latest.scores).map(([field, s]) => (
                    <tr key={field} className="border-b border-line last:border-0">
                      <td className="px-3 py-2 font-mono text-xs">{field}</td>
                      {isNullable(s) ? (
                        <>
                          <td className="px-3 py-2">{pct(s.coverage)}</td>
                          <td className="px-3 py-2">{pct(s.precision)}</td>
                          <td className="px-3 py-2 whitespace-nowrap">
                            <Bar
                              lo={s.precision_ci95[0]}
                              hi={s.precision_ci95[1]}
                              point={s.precision}
                            />
                            <span className="ml-2 font-mono text-xs text-muted">
                              ±{pct(s.precision_margin)}
                            </span>
                          </td>
                          <td className="px-3 py-2 font-mono text-xs">
                            {s.hallucination_rate > 0 ? (
                              <span className="text-accent">{pct(s.hallucination_rate)}</span>
                            ) : (
                              "0%"
                            )}
                          </td>
                        </>
                      ) : isSet(s) ? (
                        <td className="px-3 py-2 text-muted" colSpan={4}>
                          macro F1 {s.macro_f1.toFixed(3)} · precision {s.macro_precision.toFixed(3)}{" "}
                          · recall {s.macro_recall.toFixed(3)}
                        </td>
                      ) : (
                        <td className="px-3 py-2 text-muted" colSpan={4}>
                          accuracy {pct(s.accuracy)}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="max-w-2xl text-sm text-muted">
              Hallucination is reported on its own line, never folded into an average. A field that
              abstains often and is never wrong is a different thing from one that always answers
              and is sometimes wrong, and one number cannot tell them apart.
            </p>
          </section>

          {latest.slices && Object.keys(latest.slices).length > 0 && (
            <section className="space-y-3">
              <h2 className="font-mono text-sm text-muted">by slice</h2>
              <div className="overflow-x-auto rounded-lg border border-line">
                <table className="w-full text-sm">
                  <thead className="bg-panel text-left font-mono text-xs text-muted">
                    <tr>
                      {["slice", "n", "skills F1"].map((h) => (
                        <th key={h} className="border-b border-line px-3 py-2 font-normal">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(latest.slices).map(([name, s]) => (
                      <tr key={name} className="border-b border-line last:border-0">
                        <td className="px-3 py-2 font-mono text-xs">{name}</td>
                        <td className="px-3 py-2">{s.n}</td>
                        <td className="px-3 py-2">{s.skills_f1.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <section className="space-y-3">
            <h2 className="font-mono text-sm text-muted">all runs · {runs.length}</h2>
            <div className="overflow-x-auto rounded-lg border border-line">
              <table className="w-full text-sm">
                <thead className="bg-panel text-left font-mono text-xs text-muted">
                  <tr>
                    {["run", "config", "split", "n", "p50 ms", "p95 ms"].map((h) => (
                      <th key={h} className="border-b border-line px-3 py-2 font-normal">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[...runs].reverse().map((r) => (
                    <tr key={r.run_id} className="border-b border-line last:border-0">
                      <td className="px-3 py-2 font-mono text-xs">{r.run_id}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.config}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.split}</td>
                      <td className="px-3 py-2">{r.n}</td>
                      <td className="px-3 py-2">{r.p50_ms}</td>
                      <td className="px-3 py-2">{r.p95_ms}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
