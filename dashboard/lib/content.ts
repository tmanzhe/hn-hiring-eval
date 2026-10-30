import type { HISTORY_FIELDS } from "./parsers";

export const FIELD_INFO: Record<(typeof HISTORY_FIELDS)[number], { label: string; description: string }> = {
  company: { label: "Company", description: "The hiring employer named in the post." },
  role_titles: { label: "Role titles", description: "A list of advertised job titles. An empty list still counts as non-null." },
  location: { label: "Location", description: "Where the role can be performed, separate from its work arrangement." },
  remote: { label: "Work arrangement", description: "Remote, hybrid or onsite. A returned value does not necessarily mean a remote job." },
  salary_min: { label: "Salary minimum", description: "The lower pay amount, read together with currency and period." },
  salary_max: { label: "Salary maximum", description: "The upper pay amount, read together with currency and period." },
  salary_currency: { label: "Salary currency", description: "The currency associated with the pay amount." },
  salary_period: { label: "Salary period", description: "Whether pay is per year, month or hour. History counts come before annualization." },
  skills: { label: "Skills", description: "A list of detected skills. An empty list still counts as non-null." },
  seniority: { label: "Seniority", description: "Junior, mid, senior or staff+. This can be null if no level is identified." },
  visa_sponsor: { label: "Visa sponsorship", description: "True for sponsorship, false for no sponsorship, or null if unknown. False still counts as non-null." },
};

export const RUNGS = [
  { id: "B", title: "Verify claims", description: "An LLM agent can check whether a proposed value appears in the post." },
  { id: "C", title: "Add extraction tools", description: "Adds tools to split roles, find salary candidates and standardize skill names alongside claim verification." },
  { id: "D", title: "Add written guidance", description: "Uses C’s tools plus instructions about post formats and common extraction mistakes." },
  { id: "E", title: "Add a rules first pass", description: "Uses D’s setup with rules output as a fallible hint for the model to check." },
  { id: "W", title: "Follow a fixed workflow", description: "Code fixes the sequence: extract, verify company, location and salary, then revise at most once if checks fail." },
  { id: "F", title: "Fill only missing fields", description: "Runs rules first, then calls an LLM only for missing company or location; accepts source text spans and keeps existing rules values." },
] as const;

export const formatCount = (value: number) => value.toLocaleString("en-US");
export const formatPercent = (value: number, total: number) =>
  total ? `${((value / total) * 100).toFixed(1)}%` : "—";
export const formatDate = (date: string) => new Date(`${date}T12:00:00Z`).toLocaleDateString("en-US", {
  month: "short", day: "numeric", year: "numeric", timeZone: "UTC",
});

export const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
export const torontoTime = (ts: string) => new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/Toronto", year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
}).format(new Date(ts));

export function ladderLabel(rows: { model: string; n: number; ts: string }[]): string {
  if (!rows.length) return "No readable ladder report available.";
  const times = [...new Set(rows.map((row) => row.ts))].sort();
  const model = rows[0].model;
  return `${model === "claude-haiku-5-5" ? "Haiku" : model} (${model}), N=${rows[0].n} posts, run ${torontoTime(times[0])}–${torontoTime(times[times.length - 1])} America/Toronto · dev split`;
}
