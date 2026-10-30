import { readFile } from "node:fs/promises";
import path from "node:path";
import { readBaselineRuns, readFixtureThread, readHistory, readPipelineLabels, readRungs } from "./data";
import { FIELD_INFO, formatCount, formatDate, ladderLabel, percent, torontoTime } from "./content";
import { HISTORY_FIELDS, type HistoryRow } from "./parsers";

export type PipelineStep = {
  id: string;
  title: string;
  symbol: string;
  status: string;
  pending: boolean;
  summary: string;
  description: string;
  metrics: { label: string; value: string }[];
  note: string;
  source: string;
  table?: { caption: string; columns: string[]; rows: string[][] };
  example: {
    id: string | null;
    title: string;
    note: string;
    content: string | null;
    source: string;
  };
};

// Rules output for the fixture example, committed as JSON (no Python at build time).
// Regenerate with: uv run python dashboard/scripts/gen_fixture_rules.py
async function rulesForExample(id: string) {
  try {
    const file = path.resolve(process.cwd(), "data/fixture-rules.json");
    const data: unknown = JSON.parse(await readFile(file, "utf8"));
    if (!data || typeof data !== "object") return null;
    const { post_id, extraction } = data as { post_id?: unknown; extraction?: unknown };
    if (post_id !== id || !extraction || typeof extraction !== "object" || Array.isArray(extraction)) return null;
    if (!HISTORY_FIELDS.every((field) => field in extraction)) return null;
    return extraction as Record<string, unknown>;
  } catch {
    return null; // Missing file: never invent a prediction.
  }
}

export async function readPipeline(): Promise<PipelineStep[]> {
  const [history, labels, fixture, baselines, rungs] = await Promise.all([
    readHistory(), readPipelineLabels(), readFixtureThread(), readBaselineRuns(), readRungs(),
  ]);
  // Match the previous overview: reruns of a thread must not inflate totals.
  const threads = new Map<string, HistoryRow>();
  history?.forEach((row) => threads.set(row.thread_id, row));
  const snapshots = [...threads.values()];
  const total = snapshots.reduce((sum, row) => sum + row.total_posts, 0);
  const counts = Object.fromEntries(HISTORY_FIELDS.map((field) =>
    [field, snapshots.reduce((sum, row) => sum + row[field], 0)]));
  const latest = history?.[history.length - 1];
  const post = fixture?.comments[0];
  const rules = post ? await rulesForExample(post.id) : null;
  const example = {
    id: post?.id ?? null,
    title: post ? `Post ${post.id}` : "No committed example available",
    source: "tests/fixtures/sample_thread.json",
  };
  const show = formatCount;
  const missing = "Not generated yet. No readable local report is available.";
  const historyNote = history
    ? `Latest snapshot per thread · ${latest ? formatDate(latest.date) : ""}. Reruns are not added together.`
    : missing;
  const baseline = baselines?.find((run) => run.config === "rules (baseline)" && run.split === "dev");
  const f = rungs?.filter((row) => row.config === "F" && row.split === "dev");
  const fRun = f?.[0];
  const runLabel = ladderLabel(rungs ?? []);
  const outcomes = ["extracted", "abstained", "missed", "hallucinated", "wrong"];
  const precisionText = (row: NonNullable<typeof rungs>[number]) => row.precision === null ? "—"
    : `${percent(row.precision)}${row.precision_ci95 ? ` (${row.precision_ci95.map(percent).join("–")})` : ""}`;
  const fScores = f?.filter((row) => ["company", "location"].includes(row.field));
  const fTable = fScores?.length ? {
    caption: "F · final field quality after rules and fallback · precision with Wilson 95% CI",
    columns: ["Field", "Precision (95% CI)", "Hallucination rate"],
    rows: fScores.map((row) => [row.field, precisionText(row), row.hallucination_rate === null ? "—" : percent(row.hallucination_rate)]),
  } : undefined;
  const scoreTable = rungs ? {
    caption: "Ladder outcomes per rung and nullable field · absent outcome keys shown as —",
    columns: ["Rung / field", ...outcomes],
    rows: rungs.filter((row) => row.outcomes).map((row) => [
      `${row.config} / ${row.field} · n=${row.n}`,
      ...outcomes.map((key) => row.outcomes?.[key] === undefined ? "—" : show(row.outcomes[key])),
    ]),
  } : undefined;
  const comparisonRows = [...(baseline?.rows ?? []), ...(rungs ?? [])];
  const methods = [...new Set(comparisonRows.map((row) => row.config))];
  const comparisonTable = methods.length ? {
    caption: "Per-rung comparison vs rules (baseline) · company, salary, location precision; remote and seniority accuracy; skills macro-F1",
    columns: ["Method / N", "Company P", "Salary P", "Location P", "Skills F1", "Remote acc.", "Seniority acc.", "USD", "p50 / p95 ms"],
    rows: methods.map((config) => {
      const rows = comparisonRows.filter((row) => row.config === config);
      const run = rows[0];
      return [`${config} / ${run.n}`, ...["company", "salary", "location", "skills", "remote", "seniority"].map((field) => {
        const row = rows.find((entry) => entry.field === field);
        return !row ? "—" : field === "skills" ? row.macro_f1?.toFixed(3) ?? "—"
          : percent((row.precision ?? row.accuracy)!);
      }), run.cost_usd === null ? "Not recorded" : `$${run.cost_usd.toFixed(6)}${run.cost_complete ? "" : " (incomplete)"}`,
      `${run.p50_ms?.toFixed(1) ?? "—"} / ${run.p95_ms?.toFixed(1) ?? "—"}`];
    }),
  } : undefined;
  const rulesContent = rules ? JSON.stringify(rules, null, 2) : null;
  const noRules = "Rules output is not available in this build.";
  const fieldTargets = rules ? ["company", "location"].filter((field) => rules[field] === null) : null;
  const label = labels?.find((entry) => entry.comment_id === post?.id);

  return [
    {
      id: "thread", title: "HN thread", symbol: "hn", pending: false,
      status: history ? "Recorded" : "No report",
      summary: history ? `${show(threads.size)} hiring threads` : "Not generated yet",
      description: "Monthly HN “Who is hiring?” threads provide the source job posts.",
      metrics: history ? [{ label: "Distinct threads in history", value: show(threads.size) },
        { label: "Recorded snapshots", value: show(history.length) }] : [],
      note: historyNote, source: "data/rules_history.jsonl",
      example: { ...example, note: fixture
        ? `${fixture.title} · thread ${fixture.thread_id}. This July fixture is separate from the threads in rules history.`
        : "No real thread example is committed in the available fixture.",
        content: post?.html.split(/<p>|\n/)[0] ?? null },
    },
    {
      id: "fetch", title: "Fetch comments", symbol: "↓", pending: false,
      status: history ? "Recorded" : "No report",
      summary: history ? `${show(total)} posts in history` : "Not generated yet",
      description: "The fetcher collects top-level job comments and preserves their source text.",
      metrics: [
        ...(history ? [{ label: "Posts in rules history", value: show(total) }] : []),
        ...(fixture ? [{ label: "Comments in the fixture", value: show(fixture.comments.length) }] : []),
      ],
      note: `${historyNote} Fixture comments are a separate example, not an additional production fetch.`,
      source: "data/rules_history.jsonl · tests/fixtures/sample_thread.json",
      example: { ...example, note: post ? "Original comment HTML, exactly as committed." : "No real comment example is available.",
        content: post?.html ?? null },
    },
    {
      id: "rules", title: "Rules extractor", symbol: "{ }", pending: false,
      status: history ? "Recorded" : "No report",
      summary: history ? `${show(total)} posts analyzed` : "Not generated yet",
      description: "Deterministic rules read familiar post patterns and leave uncertain fields empty.",
      metrics: history ? [{ label: "Posts analyzed", value: show(total) },
        { label: "Salary period returned", value: show(counts.salary_period) }] : [],
      note: `${historyNote} Counts measure returned values, not correctness; empty lists and false also count. Values are before normalization.`,
      source: "data/rules_history.jsonl",
      table: history ? { caption: "Posts with a non-null rules value", columns: ["Field", "Posts"],
        rows: HISTORY_FIELDS.map((field) => [FIELD_INFO[field].label, show(counts[field])]) } : undefined,
      example: { ...example, note: rules
        ? "Output of ingest.rules.parse on this committed fixture (dashboard/data/fixture-rules.json), before normalization; this is not an LLM prediction."
        : `${noRules} ${post ? "Only the committed source is shown." : "No real source example is available."}`,
        content: rulesContent ?? post?.html ?? null },
    },
    {
      id: "llm", title: "LLM fallback", symbol: "F", pending: !fRun,
      status: fRun ? "Measured · Haiku" : "No report",
      summary: fRun ? `F · ${fRun.model_responses ?? "Unrecorded"} model responses` : "Rung F · null fields only",
      description: "Rung F asks an LLM only for null company or location fields and keeps every existing rules value.",
      metrics: fRun ? [
        { label: "Model responses (recorded calls)", value: String(fRun.model_responses ?? "Not recorded") },
        { label: "Total USD", value: fRun.cost_usd?.toFixed(7) ?? "Not recorded" },
        { label: "USD per post", value: fRun.cost_per_post?.toFixed(7) ?? "Not recorded" },
        { label: "p50 latency (ms)", value: fRun.p50_ms?.toFixed(1) ?? "Not recorded" },
        { label: "p95 latency (ms)", value: fRun.p95_ms?.toFixed(1) ?? "Not recorded" },
      ] : [],
      note: `${runLabel} F cost ${fRun?.cost_complete ? "complete" : "not complete"}.`,
      source: "evals/cost-quality.json · evals/cost-quality.md", table: fTable,
      example: { ...example, note: rules
        ? `${fieldTargets?.length ? `Null targets in this rules output: ${fieldTargets.join(", ")}.` : "Both target fields are present in this rules output, so F would skip the model call."} No per-post LLM trace is committed for this fixture.`
        : `${noRules} No per-post LLM trace is available for this fixture.`,
        content: rules ? JSON.stringify({ company: rules.company, location: rules.location }, null, 2) : null },
    },
    {
      id: "span", title: "Span check", symbol: "“ ”", pending: !fRun,
      status: fRun ? "Evaluated within F" : "No report", summary: "Require source evidence",
      description: "The fallback accepts proposed company and location values only when they appear as source spans, allowing case, Unicode and whitespace normalization.",
      metrics: [],
      note: `${runLabel} Span-check acceptance and failure counts are not recorded separately in the JSON. The table shows final F field quality, including retained rules values; it does not isolate span-check performance.`,
      table: fTable, source: "ingest/fallback.py · _grounded · evals/cost-quality.json",
      example: { ...example, note: "No per-post span-check trace is committed for this fixture. Existing rules values do not pass through this check.", content: null },
    },
    {
      id: "score", title: "Score vs labels", symbol: "≟", pending: !rungs,
      status: rungs ? "Ladder scored" : "No report", summary: fRun ? `Dev · N=${fRun.n} posts per rung` : "Labels ready",
      description: "Scorers compare predictions with reference labels, separating extracted, abstained, missed, hallucinated and wrong values.",
      metrics: fRun ? [
        { label: "Scored posts per rung", value: show(fRun.n) },
        { label: "Deleted HN posts skipped", value: show(fRun.skipped_missing.length) },
      ] : [],
      note: `${runLabel} Skipped missing IDs: ${fRun?.skipped_missing.join(", ") ?? "Not recorded"}. Each field is scored independently. Outcome counts are shown only where recorded.`,
      source: "evals/cost-quality.json · evals/labeled.jsonl", table: scoreTable,
      example: { ...example, note: label
        ? "A reference label is committed for this fixture; a per-post scored LLM trace is not available here."
        : "This fixture post has no matching label in evals/labeled.jsonl; no outcome is assigned.",
        content: label ? JSON.stringify(label.fields, null, 2) : null },
    },
    {
      id: "results", title: "Results", symbol: "↗", pending: !rungs,
      status: rungs ? "Comparison available" : "No report",
      summary: rungs ? "Six rungs vs rules (baseline)" : "Rules evidence available",
      description: "Compare each rung with the committed rules baseline. Full field scores, Wilson intervals, hallucination rates and errors are on the evaluation page.",
      metrics: [],
      note: `${runLabel} ${baseline ? `Rules (baseline) is a separate dev evaluation: N=${baseline.n}, run ${torontoTime(baseline.ts)} America/Toronto. The sample sizes differ, so this is not a matched-sample comparison.` : "No committed rules baseline available."} C had 1 API timeout; W had 1 validation error. Their costs are incomplete.`,
      table: comparisonTable,
      source: "evals/cost-quality.json · evals/cost-quality.md · evals/runs.jsonl",
      example: { ...example, note: "The fixture rules output below is separate from the aggregate ladder results. No final per-post LLM trace is committed for this fixture.",
        content: rulesContent },
    },
  ];
}
