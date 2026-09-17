import { ApiDown, getTrends, type TrendPoint } from "@/lib/api";

export const dynamic = "force-dynamic";

const DEFAULT = "Python,TypeScript,Kubernetes,Terraform";
const LINE = ["#9a3412", "#0f766e", "#4338ca", "#a16207", "#be123c", "#15803d"];

export default async function TrendsPage({
  searchParams,
}: {
  searchParams: Promise<{ skills?: string }>;
}) {
  const sp = await searchParams;
  const skills = sp.skills || DEFAULT;

  let points: TrendPoint[] = [];
  let down: string | null = null;
  try {
    points = await getTrends(new URLSearchParams({ skills }).toString());
  } catch (e) {
    down = e instanceof ApiDown ? e.message : "the API failed";
  }

  const months = [...new Set(points.map((p) => p.thread_month))].sort();
  const names = [...new Set(points.map((p) => p.skill))].sort();
  const max = Math.max(0.01, ...points.map((p) => p.share));

  // Plain SVG. A charting library would be four hundred kilobytes to draw six polylines.
  const W = 720;
  const H = 260;
  const PAD = { l: 44, r: 12, t: 12, b: 28 };
  const x = (i: number) =>
    PAD.l + (months.length < 2 ? 0 : (i * (W - PAD.l - PAD.r)) / (months.length - 1));
  const y = (share: number) => PAD.t + (1 - share / max) * (H - PAD.t - PAD.b);

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Skill demand over time</h1>
        <p className="max-w-2xl text-muted">
          Share of that month&apos;s postings, not raw counts. Counts would track how big the thread
          was, so a busy month would look like rising demand for everything at once.
        </p>
      </section>

      <form className="flex flex-wrap items-end gap-3">
        <label className="flex flex-1 flex-col gap-1 font-mono text-xs text-muted">
          skills, comma separated
          <input
            name="skills"
            defaultValue={skills}
            className="rounded border border-line bg-panel px-2 py-1 font-mono text-sm text-ink"
          />
        </label>
        <button className="rounded border border-line bg-panel px-3 py-1.5 font-mono text-sm hover:border-accent">
          plot
        </button>
      </form>

      {down ? (
        <p className="rounded-lg border border-line bg-panel p-4 font-mono text-sm text-accent">
          {down}
        </p>
      ) : months.length === 0 ? (
        <p className="text-muted">No postings mentioned those skills in any thread on disk.</p>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-line bg-panel p-4">
            <svg viewBox={`0 0 ${W} ${H}`} className="min-w-[640px]" role="img">
              {[0, 0.5, 1].map((f) => (
                <g key={f}>
                  <line
                    x1={PAD.l}
                    x2={W - PAD.r}
                    y1={y(max * f)}
                    y2={y(max * f)}
                    stroke="currentColor"
                    className="text-line"
                  />
                  <text x={4} y={y(max * f) + 4} className="fill-current text-muted" fontSize="11">
                    {(max * f * 100).toFixed(0)}%
                  </text>
                </g>
              ))}
              {names.map((name, si) => {
                const series = months.map((m, i) => {
                  const hit = points.find((p) => p.thread_month === m && p.skill === name);
                  return `${x(i)},${y(hit?.share ?? 0)}`;
                });
                return (
                  <polyline
                    key={name}
                    points={series.join(" ")}
                    fill="none"
                    stroke={LINE[si % LINE.length]}
                    strokeWidth="2"
                  />
                );
              })}
              {months.map((m, i) => (
                <text
                  key={m}
                  x={x(i)}
                  y={H - 8}
                  textAnchor="middle"
                  className="fill-current text-muted"
                  fontSize="11"
                >
                  {m}
                </text>
              ))}
            </svg>
          </div>
          <ul className="flex flex-wrap gap-4 font-mono text-xs">
            {names.map((n, i) => (
              <li key={n} className="flex items-center gap-2">
                <span
                  className="inline-block h-2 w-4 rounded"
                  style={{ background: LINE[i % LINE.length] }}
                />
                {n}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
