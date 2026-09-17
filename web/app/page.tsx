"use client";

import { useState } from "react";

type Match = {
  comment_id: number;
  company: string | null;
  score: number;
  matched_skills: string[];
  gap_skills: string[];
  salary_min: number | null;
  salary_max: number | null;
};

type MatchResponse = {
  matched_skills_in_resume: string[];
  matches: Match[];
  note: string;
  detail?: string;
};

export default function MatchPage() {
  const [resume, setResume] = useState("");
  const [data, setData] = useState<MatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch("/api/match", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ resume, limit: 10 }),
      });
      const body = await res.json();
      if (!res.ok) setError(body.detail ?? `request failed with ${res.status}`);
      else setData(body);
    } catch {
      setError("request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">Match a resume against the thread</h1>
        <p className="max-w-2xl text-muted">
          Paste plain text. The ranking is IDF-weighted set overlap, computed in SQL and Python, so
          a rare skill counts for more than a common one. No model chooses or orders these results.
        </p>
      </section>

      <form onSubmit={submit} className="space-y-3">
        <textarea
          value={resume}
          onChange={(e) => setResume(e.target.value)}
          rows={10}
          minLength={20}
          required
          placeholder="Paste a resume or a skills summary. At least 20 characters."
          className="w-full rounded-lg border border-line bg-panel p-4 font-mono text-sm outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={busy || resume.trim().length < 20}
          className="rounded-lg border border-line bg-panel px-4 py-2 font-mono text-sm hover:border-accent disabled:opacity-40"
        >
          {busy ? "ranking..." : "rank"}
        </button>
      </form>

      {error && (
        <p className="rounded-lg border border-line bg-panel p-4 font-mono text-sm text-accent">
          {error}
        </p>
      )}

      {data && (
        <section className="space-y-5">
          <div>
            <h2 className="font-mono text-sm text-muted">skills found in the resume</h2>
            <p className="mt-2 flex flex-wrap gap-2">
              {data.matched_skills_in_resume.length === 0 ? (
                <span className="text-muted">
                  None of the canonical skills appeared. The ranking below will be weak.
                </span>
              ) : (
                data.matched_skills_in_resume.map((s) => (
                  <span key={s} className="rounded border border-line px-2 py-0.5 font-mono text-xs">
                    {s}
                  </span>
                ))
              )}
            </p>
          </div>

          {data.matches.length === 0 ? (
            <p className="text-muted">No postings overlapped. Try a longer resume.</p>
          ) : (
            <ol className="space-y-3">
              {data.matches.map((m) => (
                <li key={m.comment_id} className="rounded-lg border border-line bg-panel p-4">
                  <div className="flex flex-wrap items-baseline gap-x-3">
                    <span className="font-semibold">{m.company ?? "company not stated"}</span>
                    <span className="font-mono text-xs text-muted">score {m.score.toFixed(3)}</span>
                    <a
                      href={`https://news.ycombinator.com/item?id=${m.comment_id}`}
                      className="ml-auto font-mono text-xs text-muted hover:text-accent"
                    >
                      original post
                    </a>
                  </div>
                  <p className="mt-2 text-sm">
                    <span className="text-muted">overlap: </span>
                    {m.matched_skills.join(", ") || "none"}
                  </p>
                  {m.gap_skills?.length > 0 && (
                    <p className="text-sm">
                      <span className="text-muted">gaps: </span>
                      {m.gap_skills.join(", ")}
                    </p>
                  )}
                </li>
              ))}
            </ol>
          )}
          <p className="text-sm text-muted">{data.note}</p>
        </section>
      )}
    </div>
  );
}
