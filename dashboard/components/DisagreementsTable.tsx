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
      <label>Field{" "}
        <select value={field} onChange={(event) => setField(event.target.value)}>
          <option value="">All fields</option>
          {SCORE_FIELDS.map((name) => <option key={name} value={name}>{name}</option>)}
        </select>
      </label>
      <label>Search{" "}
        <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} />
      </label>
      <p aria-live="polite">{filtered.length} of {entries.length} disagreements</p>
      {!filtered.length ? <p>{entries.length ? "No matching disagreements." : "No disagreements."}</p> : (
        <table>
          <thead><tr>{["Field", "Config", "Split", "Post / label ID", "Label value", "Model value"].map((label) => (
            <th key={label} scope="col">{label}</th>
          ))}</tr></thead>
          <tbody>{filtered.map((entry, index) => (
            <tr key={`${entry.field}/${entry.config}/${entry.split}/${entry.comment_id}/${index}`}>
              <td>{entry.field}</td><td>{entry.config}</td><td>{entry.split}</td><td>{entry.comment_id}</td>
              <td><code>{entry.label}</code></td><td><code>{entry.model}</code></td>
            </tr>
          ))}</tbody>
        </table>
      )}
    </>
  );
}
