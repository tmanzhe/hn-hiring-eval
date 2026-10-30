import { readFile } from "node:fs/promises";
import path from "node:path";
import { readBaselineRuns, readFixtureThread, readHistory, readPipelineLabels, readRungs } from "./data";
import { FIELD_INFO, formatCount, formatDate } from "./content";
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
  const notRun = "The LLM ladder has not been run on real data.";
  const historyNote = history
    ? `Latest snapshot per thread · ${latest ? formatDate(latest.date) : ""}. Reruns are not added together.`
    : missing;
  const latestBaselines = new Map<string, NonNullable<typeof baselines>[number]>();
  baselines?.forEach((run) => latestBaselines.set(run.split, run));
  const outcomes = ["extracted", "abstained", "missed", "hallucinated", "wrong"];
  const baselineTable = latestBaselines.size ? {
    caption: "Existing rules evaluations · location only · latest record per split (not LLM results)",
    columns: ["Split / rules config", ...outcomes],
    rows: [...latestBaselines.values()].map((run) => [
      `${run.split} · ${run.config} · n=${run.n}`,
      ...outcomes.map((outcome) => show(run.location[outcome] ?? 0)),
    ]),
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
      id: "llm", title: "LLM fallback", symbol: "F", pending: true,
      status: "Not run", summary: "Rung F · null fields only",
      description: "Rung F asks an LLM only for null company or location fields and keeps every existing rules value.",
      metrics: [], note: `${notRun} Model-call counts, cost and latency are not generated yet.`,
      source: "ingest/fallback.py · evals/cost-quality.json (not generated yet)",
      example: { ...example, note: rules
        ? `${fieldTargets?.length ? `Null targets in this rules output: ${fieldTargets.join(", ")}.` : "Both target fields are already present in this rules output, so rung F would skip the model call."} This is a rules-only inspection; no LLM output exists for this post.`
        : `${noRules} No real LLM example exists because the ladder has not been run.`,
        content: rules ? JSON.stringify({ company: rules.company, location: rules.location }, null, 2) : null },
    },
    {
      id: "span", title: "Span check", symbol: "“ ”", pending: true,
      status: "Not run", summary: "Require source evidence",
      description: "The fallback accepts proposed company and location values only when they appear as source spans, allowing case, Unicode and whitespace normalization.",
      metrics: [], note: `${notRun} Span-check acceptance and failure counts are not generated yet.`,
      source: "ingest/fallback.py · _grounded",
      example: { ...example, note: "No real span-check trace exists for this post: there is no LLM proposal to check, and existing rules values do not pass through this check.", content: null },
    },
    {
      id: "score", title: "Score vs labels", symbol: "≟", pending: true,
      status: "LLM not run", summary: labels ? `${show(labels.length)} completed labels ready` : "Labels not available",
      description: "Scorers compare predictions with reference labels, separating extracted, abstained, missed, hallucinated and wrong values.",
      metrics: labels ? [{ label: "Completed labels", value: show(labels.length) },
        { label: "Dev labels", value: show(labels.filter((entry) => entry.split === "dev").length) },
        { label: "Held-out labels", value: show(labels.filter((entry) => entry.split === "held-out").length) }] : [],
      note: `${notRun} LLM scores are not generated yet. ${baselines?.length ? "The committed rules evaluations below are separate; each field is scored independently." : "No committed rules evaluation is available."}`,
      source: "evals/labeled.jsonl · evals/runs.jsonl", table: baselineTable,
      example: { ...example, note: label
        ? "A reference label is committed for this post; no LLM prediction or scored LLM trace exists."
        : "This fixture post has no matching label in evals/labeled.jsonl, so no real scored example exists for it; no outcome is assigned.",
        content: label ? JSON.stringify(label.fields, null, 2) : null },
    },
    {
      id: "results", title: "Results", symbol: "↗", pending: !rungs,
      status: rungs ? "Report available" : "Awaiting ladder",
      summary: rungs ? "Local ladder report" : history || baselines?.length ? "Rules evidence available" : "Not generated yet",
      description: "Results keep rules coverage separate from evaluation quality, model cost and per-post timing.",
      metrics: [
        ...(history ? [{ label: "Rules history snapshots", value: show(history.length) }] : []),
        ...(baselines ? [{ label: "Committed rules evaluation records", value: show(baselines.length) }] : []),
      ],
      note: rungs ? "A local ladder report is available on the evaluation page."
        : `${notRun} The comparison will appear after a ladder run; accuracy, cost and speed results for the LLM are not generated yet.`,
      source: "data/rules_history.jsonl · evals/runs.jsonl · evals/cost-quality.json",
      example: { ...example, note: rules
        ? "No final evaluated LLM result exists for this post. Its rules-only extraction is the last available step in this build."
        : "No final evaluated LLM result exists, and no rules output is available for this example in this build.",
        content: rulesContent },
    },
  ];
}
