"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { HISTORY_FIELDS, type HistoryRow } from "../lib/parsers";

const COLORS = ["#0072b2", "#d55e00", "#009e73", "#cc79a7", "#a6761d", "#6a3d9a",
  "#1b9e77", "#e7298a", "#7570b3", "#666666", "#e6ab02"];

export default function TrendChart({ rows }: { rows: HistoryRow[] }) {
  const data = rows.map((row) => ({ ...row, run: `${row.date} / ${row.thread_id}` }));
  return (
    <div role="img" aria-label="Per-field non-null counts over recorded runs" style={{ width: "100%", height: 450 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="run" />
          <YAxis allowDecimals={false} domain={[0, "auto"]} />
          <Tooltip />
          <Legend />
          {HISTORY_FIELDS.map((field, index) => (
            <Line key={field} dataKey={field} stroke={COLORS[index]} isAnimationActive={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
