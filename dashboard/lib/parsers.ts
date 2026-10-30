// Names and formats mirror ingest/schema.py, ingest/rules_history.py and evals/ladder.py.
export const HISTORY_FIELDS = [
  "company", "role_titles", "location", "remote", "salary_min", "salary_max",
  "salary_currency", "salary_period", "skills", "seniority", "visa_sponsor",
] as const;
export const SCORE_FIELDS = ["company", "salary", "location", "skills", "remote", "seniority"] as const;
type ScoreField = (typeof SCORE_FIELDS)[number];
export type HistoryRow = {
  date: string;
  thread_id: string;
  total_posts: number;
} & Record<(typeof HISTORY_FIELDS)[number], number>;
type Interval = [number, number];
export type RungRow = {
  config: string;
  split: string;
  model: string;
  field: ScoreField;
  n: number;
  accuracy: number | null;
  accuracy_ci95: Interval | null;
  precision: number | null;
  precision_ci95: Interval | null;
  macro_f1: number | null;
  ts: string;
  skipped_missing: string[];
  model_responses: number | null;
  errors: string | null;
  outcomes: Record<string, number> | null;
  hallucination_rate: number | null;
  cost_per_post: number | null;
  cost_usd: number | null;
  cost_complete: boolean | null;
  p50_ms: number | null;
  p95_ms: number | null;
};
export type Disagreement = {
  field: ScoreField;
  config: string;
  split: string;
  comment_id: string;
  label: string;
  model: string;
};

export type PipelineLabel = {
  comment_id: string;
  split: string;
  fields: Record<string, unknown>;
};
export type FixtureThread = {
  thread_id: string;
  title: string;
  comments: { id: string; html: string }[];
};
export type BaselineRun = {
  config: string;
  split: string;
  n: number;
  ts: string;
  location: Record<string, number>;
  rows: RungRow[];
};

export function parsePipelineLabels(text: string): PipelineLabel[] {
  return text.split(/\r?\n/).filter((line) => line.trim()).flatMap((line) => {
    const row = object(JSON.parse(line));
    // Match evals/run.py: only completed labels enter evaluation.
    if (row.done !== true) return [];
    return [{ comment_id: string(row.comment_id), split: string(row.split ?? "dev"),
      fields: Object.fromEntries(HISTORY_FIELDS.filter((field) => field in row)
        .map((field) => [field, row[field]])) }];
  });
}

export function parseFixtureThread(text: string): FixtureThread {
  const row = object(JSON.parse(text));
  if (!Array.isArray(row.comments)) throw new Error("Expected fixture comments");
  return { thread_id: string(row.thread_id), title: string(row.title),
    comments: row.comments.map((value) => {
      const comment = object(value);
      return { id: string(comment.objectID), html: string(comment.comment_text) };
    }) };
}

export function parseBaselineRuns(text: string): BaselineRun[] {
  return text.split(/\r?\n/).filter((line) => line.trim()).flatMap((line) => {
    const row = object(JSON.parse(line));
    if (typeof row.config !== "string" || row.config !== "rules (baseline)") return [];
    // Rules runs have no LLM cost block; validate their own committed schema.
    const n = count(row.n);
    const score = object(object(row.scores).location);
    const location = Object.fromEntries(Object.entries(object(score.outcomes))
      .map(([key, value]) => [key, count(value)]));
    if (count(score.n) !== n || Object.values(location).reduce((sum, value) => sum + value, 0) !== n) {
      throw new Error("Outcome counts do not match n");
    }
    return [{ config: row.config, split: string(row.split), n, ts: string(row.ts), location, rows: parseRungs(JSON.stringify([row])) }];
  }).sort((a, b) => a.ts.localeCompare(b.ts));
}

function object(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Expected an object");
  }
  return value as Record<string, unknown>;
}

function string(value: unknown): string {
  if (typeof value !== "string" || !value) throw new Error("Expected a string");
  return value;
}

function number(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new Error("Expected a finite nonnegative number");
  }
  return value;
}

function count(value: unknown): number {
  const result = number(value);
  if (!Number.isInteger(result)) throw new Error("Expected a count");
  return result;
}

function proportion(value: unknown): number {
  const result = number(value);
  if (result > 1) throw new Error("Expected a proportion");
  return result;
}

function interval(value: unknown): Interval {
  if (!Array.isArray(value) || value.length !== 2) throw new Error("Expected CI pair");
  const pair: Interval = [proportion(value[0]), proportion(value[1])];
  if (pair[0] > pair[1]) throw new Error("Invalid CI bounds");
  return pair;
}

export function parseHistory(text: string): HistoryRow[] {
  const rows = text.split(/\r?\n/).filter((line) => line.trim()).map((line) => {
    const row = object(JSON.parse(line));
    const date = string(row.date);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) ||
        new Date(date).toISOString().slice(0, 10) !== date) throw new Error("Invalid date");
    const thread_id = typeof row.thread_id === "number"
      ? String(count(row.thread_id)) : string(row.thread_id);
    const total_posts = count(row.total_posts);
    const counts = Object.fromEntries(HISTORY_FIELDS.map((field) => {
      const value = count(row[field]);
      if (value > total_posts) throw new Error("Count exceeds total posts");
      return [field, value];
    })) as Pick<HistoryRow, (typeof HISTORY_FIELDS)[number]>;
    return { date, thread_id, total_posts, ...counts };
  });
  if (!rows.length) throw new Error("Empty history");
  // Python sorts (date, str(thread_id)), rather than sorting thread IDs numerically.
  return rows.sort((a, b) => {
    const left = `${a.date}/${a.thread_id}`, right = `${b.date}/${b.thread_id}`;
    return left < right ? -1 : left > right ? 1 : 0;
  });
}

export function wilson(successes: number, n: number): Interval {
  if (n <= 0) return [0, 1];
  const z = 1.959963984540054;
  const p = successes / n;
  const denominator = 1 + z * z / n;
  const center = (p + z * z / (2 * n)) / denominator;
  const half = z / denominator * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n));
  return [Math.max(0, center - half), Math.min(1, center + half)];
}

export function parseRungs(text: string): RungRow[] {
  const runs: unknown = JSON.parse(text);
  if (!Array.isArray(runs) || !runs.length) throw new Error("Expected ladder rows");
  return runs.flatMap((value) => {
    const run = object(value);
    const config = string(run.config), split = string(run.split), model = string(run.model);
    const baseline = config === "rules (baseline)";
    const runN = count(run.n), cost_usd = baseline ? null : number(run.cost_usd);
    if (!baseline && typeof run.cost_complete !== "boolean") throw new Error("Missing cost status");
    const cost_complete = baseline ? null : run.cost_complete as boolean;
    const ts = string(run.ts);
    const skipped_missing = Array.isArray(run.skipped_missing) ? run.skipped_missing.map(string) : [];
    const model_responses = run.model_responses == null ? null : count(run.model_responses);
    const errors = Array.isArray(run.errors) ? run.errors.map((value) => {
      const error = object(value);
      return `Post ${string(error.comment_id)}: ${string(error.error)}`;
    }).join("; ") || "0" : null;
    const p50_ms = run.p50_ms == null ? null : number(run.p50_ms);
    const p95_ms = run.p95_ms == null ? null : number(run.p95_ms);
    const scores = object(run.scores);
    return SCORE_FIELDS.map((field): RungRow => {
      const score = object(scores[field]);
      const n = score.n === undefined ? runN : count(score.n);
      let accuracy: number | null = null, accuracy_ci95: Interval | null = null;
      let precision: number | null = null, precision_ci95: Interval | null = null;
      let macro_f1: number | null = null;
      if (field === "skills") {
        macro_f1 = proportion(score.macro_f1);
      } else if (score.outcomes !== undefined) {
        const outcomes = object(score.outcomes);
        const extracted = count(outcomes.extracted ?? 0);
        const correct = extracted + count(outcomes.abstained ?? 0);
        const attempts = extracted + count(outcomes.wrong ?? 0) + count(outcomes.hallucinated ?? 0);
        const total = Object.values(outcomes).reduce<number>((sum, v) => sum + count(v), 0);
        if (total !== n) throw new Error("Outcome counts do not match n");
        accuracy = score.accuracy === undefined ? (n ? correct / n : 0) : proportion(score.accuracy);
        accuracy_ci95 = score.accuracy_ci95 === undefined
          ? wilson(correct, n) : interval(score.accuracy_ci95);
        precision = proportion(score.precision);
        precision_ci95 = score.precision_ci95 === undefined
          ? wilson(extracted, attempts) : interval(score.precision_ci95);
      } else {
        accuracy = proportion(score.accuracy);
        // The scorer rounds accuracy to 4 decimals; prefer exact confusion counts for the CI.
        let correct = Math.round(accuracy * n);
        if (score.confusion !== undefined) {
          const confusion = object(score.confusion);
          let total = 0;
          correct = 0;
          for (const [pair, value] of Object.entries(confusion)) {
            const hits = count(value), [truth, prediction] = pair.split("->");
            if (prediction === undefined) throw new Error("Invalid confusion key");
            total += hits;
            if (truth === prediction) correct += hits;
          }
          if (total !== n) throw new Error("Confusion counts do not match n");
        }
        accuracy_ci95 = score.accuracy_ci95 === undefined
          ? wilson(correct, n) : interval(score.accuracy_ci95);
      }
      return { config, split, model, field, n, ts, skipped_missing, model_responses, errors,
        outcomes: score.outcomes === undefined ? null : Object.fromEntries(Object.entries(object(score.outcomes)).map(([key, value]) => [key, count(value)])),
        hallucination_rate: score.hallucination_rate == null ? null : proportion(score.hallucination_rate),
        cost_per_post: cost_usd === null || !runN ? null : cost_usd / runN,
        accuracy, accuracy_ci95, precision,
        precision_ci95, macro_f1, cost_usd, cost_complete, p50_ms, p95_ms };
    });
  });
}

function decodeCell(cell: string): unknown {
  const code = /^<code>(.*)<\/code>$/.exec(cell);
  if (!code) throw new Error("Expected a code cell");
  // Decode once: an original literal '&quot;' is emitted as '&amp;quot;'.
  const entities: Record<string, string> = { amp: "&", lt: "<", gt: ">", quot: '"' };
  const json = code[1].replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot);/gi, (_, entity: string) => {
    const key = entity.toLowerCase();
    if (key.startsWith("#x")) return String.fromCodePoint(parseInt(key.slice(2), 16));
    if (key.startsWith("#")) return String.fromCodePoint(parseInt(key.slice(1), 10));
    return entities[key];
  });
  return JSON.parse(json);
}

export function parseDisagreements(text: string): Disagreement[] {
  if (!text.startsWith("# LLM disagreements with Claude-drafted gold labels")) {
    throw new Error("Unrecognized report");
  }
  const entries: Disagreement[] = [];
  const fields = new Set<string>();
  const groups = new Set<string>();
  let field: ScoreField | null = null;
  let config: string | null = null;
  let expected = 0, found = 0, sawEmpty = false, sawTable = false;
  function finishGroup() {
    if (config && (found !== expected || (expected === 0 ? !sawEmpty : !sawTable))) {
      throw new Error("Incomplete disagreement group");
    }
  }
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (line.startsWith("## ")) {
      finishGroup();
      const name = line.slice(3);
      if (!SCORE_FIELDS.includes(name as ScoreField) || fields.has(name)) {
        throw new Error("Invalid field heading");
      }
      field = name as ScoreField;
      fields.add(field);
      config = null;
    } else if (line.startsWith("### ")) {
      finishGroup();
      const heading = /^### Config ([BCDEWF]) \((\d+)\)$/.exec(line);
      if (!field || !heading) throw new Error("Invalid config heading");
      config = heading[1];
      const key = `${field}/${config}`;
      if (groups.has(key)) throw new Error("Duplicate group");
      groups.add(key);
      expected = Number(heading[2]);
      found = 0;
      sawEmpty = false;
      sawTable = false;
    } else if (field && line.startsWith("|")) {
      if (!config) throw new Error("Table outside config");
      if (line === "| Split | Post / label ID | Label value | Model value |") {
        sawTable = true;
        continue;
      }
      if (/^\|[\s|:-]+\|$/.test(line)) continue;
      const cells = line.slice(1, -1).split("|").map((cell) => cell.trim());
      if (!line.endsWith("|") || cells.length !== 4 || !["dev", "held-out"].includes(cells[0])) {
        throw new Error("Invalid disagreement row");
      }
      const id = decodeCell(cells[1]);
      if (typeof id !== "string" && typeof id !== "number") throw new Error("Invalid post ID");
      entries.push({ field, config, split: cells[0], comment_id: String(id),
        label: JSON.stringify(decodeCell(cells[2])), model: JSON.stringify(decodeCell(cells[3])) });
      found++;
    } else if (field && line) {
      if (config && line === "No disagreements.") sawEmpty = true;
      else throw new Error("Unexpected report content");
    }
  }
  finishGroup();
  if (fields.size !== SCORE_FIELDS.length) throw new Error("Missing fields");
  // --config may select any subset, but every field must have the same selected configs.
  const configs = [...groups].filter((key) => key.startsWith("company/"))
    .map((key) => key.split("/")[1]);
  if (!configs.length || SCORE_FIELDS.some((name) =>
    configs.some((rung) => !groups.has(`${name}/${rung}`))) ||
    groups.size !== configs.length * SCORE_FIELDS.length) throw new Error("Missing config groups");
  return entries;
}
