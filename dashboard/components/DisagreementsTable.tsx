"use client";

import { useState } from "react";
import { SCORE_FIELDS, type Disagreement } from "../lib/parsers";

export default function DisagreementsTable({ entries }: { entries: Disagreement[] }) {
  const [field, setField] = useState("");
  const [search, setSearch] = useState("");
  const query = search.trim().toLowerCase();
  const filtered = entries.filter((entry) => (!field || entry.field === field) &&
    Object.values(entry).some((value) => value.toLowerCase().includes(query)));
  return (
    <>
      <div className="card flex flex-wrap items-end gap-5 p-5">
      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">Field
        <select value={field} onChange={(event) => setField(event.target.value)}>
          <option value="">All fields</option>
          {SCORE_FIELDS.map((name) => <option key={name} value={name}>{name}</option>)}
        </select>
      </label>
      <label className="flex min-w-0 flex-1 flex-col gap-2 text-sm font-medium text-slate-700">Search posts or values
        <input type="search" placeholder="Post ID, method or answer…" value={search} onChange={(event) => setSearch(event.target.value)} />
      </label>
      <p aria-live="polite" className="pb-2 text-sm text-slate-500">{filtered.length} of {entries.length} disagreements</p>
      </div>
      {!filtered.length ? <p className="card p-8 text-center text-sm leading-7 text-slate-600">{entries.length ? "No answers match these filters. Try another field or clear your search." : "This report contains no disagreements for the selected methods and posts. That means agreement with the labels, not proof that every answer is correct."}</p> : (
        <div className="table-scroll" role="region" aria-label="Label disagreements, scroll horizontally for all columns" tabIndex={0}>
        <table>
          <caption>Each row is a field where a method’s answer differs from the reference label. Read the two values side by side, then open the HN post to check the source. Model salary amounts are annualized; label amounts keep their recorded period.</caption>
          <thead><tr>{["Field", "Method", "Dataset split", "Post / label ID", "Reference label", "Model answer"].map((label) => (
            <th key={label} scope="col">{label}</th>
          ))}</tr></thead>
          <tbody>{filtered.map((entry, index) => (
            <tr key={`${entry.field}/${entry.config}/${entry.split}/${entry.comment_id}/${index}`}>
              <td>{entry.field}</td><td>{entry.config}</td><td>{entry.split}</td><td><a className="text-link" href={`https://news.ycombinator.com/item?id=${encodeURIComponent(entry.comment_id)}`}>{entry.comment_id} ↗</a></td>
              <td><code>{entry.label}</code></td><td><code>{entry.model}</code></td>
            </tr>
          ))}</tbody>
        </table>
        </div>
      )}
    </>
  );
}
