"use client";

import { useState } from "react";
import { torontoTime } from "../lib/content";
import type { RungRow } from "../lib/parsers";

type ColumnKey = Exclude<keyof RungRow, "outcomes" | "skipped_missing">;
type Column = { key: ColumnKey; label: string };
const COLUMNS: Column[] = [
  { key: "config", label: "Method" }, { key: "split", label: "Dataset split" },
  { key: "model", label: "Model" }, { key: "ts", label: "Run (America/Toronto)" }, { key: "field", label: "Field" }, { key: "n", label: "n" },
  { key: "accuracy", label: "Accuracy" }, { key: "accuracy_ci95", label: "Accuracy Wilson 95% CI" },
  { key: "precision", label: "Precision" }, { key: "precision_ci95", label: "Precision Wilson 95% CI" },
  { key: "hallucination_rate", label: "Hallucination rate" },
  { key: "macro_f1", label: "Skills macro-F1" }, { key: "cost_usd", label: "Cost (USD)" },
  { key: "cost_per_post", label: "USD / post" }, { key: "model_responses", label: "Model responses" },
  { key: "errors", label: "Errors" },
  { key: "cost_complete", label: "Cost complete" },
  { key: "p50_ms", label: "p50 (ms)" }, { key: "p95_ms", label: "p95 (ms)" },
];
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

function display(row: RungRow, key: ColumnKey): string {
  const value = row[key];
  if (value === null) return "—";
  if (key === "ts") return torontoTime(row.ts);
  if (Array.isArray(value)) return `${percent(value[0])} to ${percent(value[1])}`;
  if (typeof value === "boolean") return value ? "Yes" : "No (incomplete)";
  if (typeof value === "number") {
    if (key === "accuracy" || key === "precision" || key === "hallucination_rate") return percent(value);
    if (key === "macro_f1") return value.toFixed(3);
    if (key === "cost_usd" || key === "cost_per_post") return `${value.toFixed(6)}${row.cost_complete ? "" : " (incomplete)"}`;
    if (key === "p50_ms" || key === "p95_ms") return value.toFixed(1);
  }
  return String(value);
}

export default function RungsTable({ rows }: { rows: RungRow[] }) {
  const [sort, setSort] = useState<{ key: ColumnKey; ascending: boolean }>({ key: "config", ascending: true });
  const columns = COLUMNS.filter(({ key }) =>
    (key !== "p50_ms" && key !== "p95_ms") || rows.some((row) => row[key] !== null));
  const sorted = [...rows].sort((a, b) => {
    const left = a[sort.key], right = b[sort.key];
    if (left === null) return right === null ? 0 : 1;
    if (right === null) return -1;
    const x = Array.isArray(left) ? left[0] : left;
    const y = Array.isArray(right) ? right[0] : right;
    const comparison = typeof x === "string" && typeof y === "string"
      ? x.localeCompare(y) : Number(x) - Number(y);
    return sort.ascending ? comparison : -comparison;
  });
  return (
    <div className="table-scroll" role="region" aria-label="Ladder scores, scroll horizontally for all columns" tabIndex={0}>
      <table>
        <caption>Each row is one method, dataset split and field. Higher scores mean closer agreement with labels. Cost covers the whole method/split and repeats across fields; do not add these rows. Click headings to sort; uncertainty ranges sort by their lower bound. A dash means the metric does not apply or was not recorded. Rules costs, model responses and errors were not recorded. Hallucination rates apply to company, salary and location.</caption>
        <thead><tr>{columns.map(({ key, label }) => (
          <th key={key} scope="col" aria-sort={sort.key === key ? (sort.ascending ? "ascending" : "descending") : "none"}>
            <button type="button" onClick={() => setSort({ key, ascending: sort.key === key ? !sort.ascending : true })}>
              {label}{sort.key === key ? (sort.ascending ? " ↑" : " ↓") : ""}
            </button>
          </th>
        ))}</tr></thead>
        <tbody>{sorted.map((row, index) => (
          <tr key={`${row.config}/${row.split}/${row.field}/${index}`}>
            {columns.map(({ key }) => <td key={key}>{display(row, key)}</td>)}
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}
