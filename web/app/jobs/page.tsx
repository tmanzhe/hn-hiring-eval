import Link from "next/link";
import { ApiDown, getJobs, type Job } from "@/lib/api";

export const dynamic = "force-dynamic";

const REMOTE = ["", "remote", "hybrid", "onsite"];

function salary(j: Job) {
  if (j.salary_min == null && j.salary_max == null) return <span className="text-muted">not stated</span>;
  const fmt = (n: number) => `$${Math.round(n / 1000)}k`;
  const range =
    j.salary_min != null && j.salary_max != null && j.salary_min !== j.salary_max
      ? `${fmt(j.salary_min)} to ${fmt(j.salary_max)}`
      : fmt((j.salary_max ?? j.salary_min)!);
  return (
    <span>
      {range}
      {j.salary_period && j.salary_period !== "year" && (
        <span className="text-muted"> (from {j.salary_period})</span>
      )}
    </span>
  );
}

export default async function JobsPage({
  searchParams,
}: {
  searchParams: Promise<{ skill?: string; remote?: string; min_salary?: string }>;
}) {
  const sp = await searchParams;
  const qs = new URLSearchParams();
  if (sp.skill) qs.set("skill", sp.skill);
  if (sp.remote) qs.set("remote", sp.remote);
  if (sp.min_salary) qs.set("min_salary", sp.min_salary);
  qs.set("limit", "200");

  let jobs: Job[] = [];
  let down: string | null = null;
  try {
    jobs = await getJobs(qs.toString());
  } catch (e) {
    down = e instanceof ApiDown ? e.message : "the API failed";
  }

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Currently hiring</h1>
        <p className="max-w-2xl text-muted">
          The latest thread only. Spanning every thread would list roles that were filled months
          ago, so the cutoff is a correctness property rather than a filter.
        </p>
      </section>

      <form className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 font-mono text-xs text-muted">
          skill
          <input
            name="skill"
            defaultValue={sp.skill ?? ""}
            placeholder="Python"
            className="rounded border border-line bg-panel px-2 py-1 font-mono text-sm text-ink"
          />
        </label>
        <label className="flex flex-col gap-1 font-mono text-xs text-muted">
          remote
          <select
            name="remote"
            defaultValue={sp.remote ?? ""}
            className="rounded border border-line bg-panel px-2 py-1 font-mono text-sm text-ink"
          >
            {REMOTE.map((r) => (
              <option key={r} value={r}>
                {r || "any"}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 font-mono text-xs text-muted">
          min salary
          <input
            name="min_salary"
            type="number"
            min={0}
            step={10000}
            defaultValue={sp.min_salary ?? ""}
            className="rounded border border-line bg-panel px-2 py-1 font-mono text-sm text-ink"
          />
        </label>
        <button className="rounded border border-line bg-panel px-3 py-1.5 font-mono text-sm hover:border-accent">
          filter
        </button>
        <Link href="/jobs" className="font-mono text-sm text-muted hover:text-accent">
          clear
        </Link>
      </form>

      {down ? (
        <p className="rounded-lg border border-line bg-panel p-4 font-mono text-sm text-accent">
          {down}
        </p>
      ) : jobs.length === 0 ? (
        <p className="text-muted">
          Nothing matched. A salary filter drops every posting that did not state one, which is
          most of them.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-line">
          <table className="w-full text-sm">
            <thead className="bg-panel text-left font-mono text-xs text-muted">
              <tr>
                {["company", "location", "remote", "salary", "seniority", "skills", ""].map((h) => (
                  <th key={h} className="border-b border-line px-3 py-2 font-normal">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.comment_id} className="border-b border-line last:border-0">
                  <td className="px-3 py-2">{j.company ?? <span className="text-muted">not stated</span>}</td>
                  <td className="px-3 py-2">{j.location ?? <span className="text-muted">—</span>}</td>
                  <td className="px-3 py-2 font-mono text-xs">{j.remote ?? "—"}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{salary(j)}</td>
                  <td className="px-3 py-2 font-mono text-xs">{j.seniority ?? "—"}</td>
                  <td className="px-3 py-2 text-xs">{j.skills.join(", ")}</td>
                  <td className="px-3 py-2">
                    <a
                      href={`https://news.ycombinator.com/item?id=${j.comment_id}`}
                      className="font-mono text-xs text-muted hover:text-accent"
                    >
                      post
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!down && jobs.length > 0 && (
        <p className="font-mono text-xs text-muted">
          {jobs.length} postings. Null means the post did not say, not that the value is unknown to
          the parser.
        </p>
      )}
    </div>
  );
}
