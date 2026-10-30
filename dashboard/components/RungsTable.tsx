"use client";

import { useState } from "react";
import type { RungRow } from "../lib/parsers";

type Column = { key: keyof RungRow; label: string };
const COLUMNS: Column[] = [
  { key: "config", label: "Config" }, { key: "split", label: "Split" },
  { key: "model", label: "Model" }, { key: "field", label: "Field" }, { key: "n", label: "n" },
  { key: "accuracy", label: "Accuracy" }, { key: "accuracy_ci95", label: "Accuracy Wilson 95% CI" },
  { key: "precision", label: "Precision" }, { key: "precision_ci95", label: "Precision Wilson 95% CI" },
  { key: "macro_f1", label: "Skills macro-F1" }, { key: "cost_usd", label: "Cost (USD)" },
  { key: "cost_complete", label: "Cost complete" },
  { key: "p50_ms", label: "p50 (ms)" }, { key: "p95_ms", label: "p95 (ms)" },
];
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

function display(row: RungRow, key: keyof RungRow): string {
  const value = row[key];
  if (value === null) return "—";
  if (Array.isArray(value)) return `${percent(value[0])} to ${percent(value[1])}`;
  if (typeof value === "boolean") return value ? "Yes" : "No (incomplete)";
  if (typeof value === "number") {
    if (key === "accuracy" || key === "precision") return percent(value);
    if (key === "macro_f1") return value.toFixed(3);
    if (key === "cost_usd") return `${value.toFixed(6)}${row.cost_complete ? "" : " (incomplete)"}`;
    if (key === "p50_ms" || key === "p95_ms") return value.toFixed(1);
  }
  return String(value);
}

export default function RungsTable({ rows }: { rows: RungRow[] }) {
  const [sort, setSort] = useState<{ key: keyof RungRow; ascending: boolean }>({ key: "config", ascending: true });
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
    <div style={{ overflowX: "auto" }}>
      <table>
        <caption>Field scores and run costs; CI columns sort by their lower bound.</caption>
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
