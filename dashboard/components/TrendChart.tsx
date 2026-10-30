"use client";

import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { FIELD_INFO, formatCount } from "../lib/content";
import { HISTORY_FIELDS, type HistoryRow } from "../lib/parsers";

type Field = (typeof HISTORY_FIELDS)[number];
const COLORS = ["#0369a1", "#a16207", "#0f766e", "#9f1239", "#7c3aed", "#c2410c",
  "#4d7c0f", "#b45309", "#4338ca", "#475569", "#a21caf"];

export default function TrendChart({ rows }: { rows: HistoryRow[] }) {
  const [selected, setSelected] = useState<Field[]>(["company", "location", "remote", "salary_period"]);
  const data = rows.map((row) => ({ ...row, run: `${row.date} / ${row.thread_id}` }));
  return (
    <figure aria-labelledby="trend-caption">
      <figcaption id="trend-caption" className="mb-5 max-w-3xl text-sm leading-7 text-slate-600">
        Each point is one date/thread run; higher means more posts returned that field. Runs follow Toronto date, then thread ID. Counts reflect thread size and extraction coverage, not correctness or hiring growth. Choose fields below; hover or use the arrow keys on the chart for values.
      </figcaption>
      <fieldset className="mb-5">
        <legend className="mb-3 text-xs font-medium text-slate-500">Fields to show</legend>
        <div className="flex flex-wrap gap-2">
          {HISTORY_FIELDS.map((field, index) => <label key={field} className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs ${selected.includes(field) ? "border-slate-300 bg-slate-50 text-slate-900" : "border-slate-200 text-slate-500"}`}>
            <input type="checkbox" className="h-3.5 w-3.5 accent-slate-800" checked={selected.includes(field)} onChange={() => setSelected((current) => current.includes(field) ? current.filter((item) => item !== field) : [...current, field])} />
            <span aria-hidden="true" className="h-2 w-2 rounded-full" style={{ background: COLORS[index] }} />{FIELD_INFO[field].label}
          </label>)}
        </div>
      </fieldset>
      {selected.length ? <div className="h-80 w-full min-w-0 sm:h-96">
        <ResponsiveContainer width="100%" height="100%" initialDimension={{ width: 800, height: 384 }}>
          <LineChart accessibilityLayer data={data} margin={{ top: 15, right: 15, bottom: 15, left: 0 }}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="run" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} minTickGap={28} height={60}
              tickFormatter={(value: string) => `Run ${data.findIndex((row) => row.run === value) + 1}`} />
            <YAxis allowDecimals={false} domain={[0, "auto"]} tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} width={45} />
            <Tooltip contentStyle={{ border: "1px solid #e2e8f0", borderRadius: 12, fontSize: 12, lineHeight: "24px" }} />
            {HISTORY_FIELDS.filter((field) => selected.includes(field)).map((field) => (
              <Line key={field} name={FIELD_INFO[field].label} dataKey={field} stroke={COLORS[HISTORY_FIELDS.indexOf(field)]} strokeWidth={2.5} dot={{ r: 4, strokeWidth: 2, fill: "#fff" }} activeDot={{ r: 6 }} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div> : <p role="status" className="flex h-80 items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-600">Choose a field above to see its recorded counts.</p>}
      <p className="mt-2 text-xs leading-6 text-slate-500">Vertical axis: posts with a non-null value · Horizontal axis: recorded runs. Full dates and thread IDs are in the tooltip and table. False and empty lists count as non-null.</p>
      <details className="mt-5 border-t border-slate-100 pt-4 text-sm">
        <summary>View counts for every recorded run</summary>
        <div className="mt-4 overflow-x-auto"><table>
          <caption>Exact counts behind the chart, including fields you have hidden. Each row is one recorded run; counts are not added across runs.</caption>
          <thead><tr><th scope="col">Toronto run date</th><th scope="col">Thread ID</th><th scope="col">Total posts</th>{HISTORY_FIELDS.map((field) => <th scope="col" key={field}>{FIELD_INFO[field].label}</th>)}</tr></thead>
          <tbody>{rows.map((row, i) => <tr key={`${row.date}/${row.thread_id}/${i}`}><th scope="row" className="whitespace-nowrap">{row.date}</th><td>{row.thread_id}</td><td>{formatCount(row.total_posts)}</td>{HISTORY_FIELDS.map((field) => <td key={field} className="tabular-nums">{formatCount(row[field])}</td>)}</tr>)}</tbody>
        </table></div>
      </details>
    </figure>
  );
}
