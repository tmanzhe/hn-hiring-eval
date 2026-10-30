import { ladderLabel } from "../lib/content";
import type { RungRow } from "../lib/parsers";

export default function RunLabel({ rows }: { rows: RungRow[] }) {
  const skipped = [...new Set(rows.flatMap((row) => row.skipped_missing))];
  return <div className="mt-5 rounded-xl border border-orange-200 bg-orange-50 px-5 py-4 text-sm leading-7 text-orange-950">
    <p className="font-semibold">{ladderLabel(rows)}</p>
    {rows.length > 0 && <p>Every rung used Haiku; the repository’s pinned Opus was not used. {skipped.length} of {rows[0].n + skipped.length} dev labels were skipped because their posts were deleted from HN: {skipped.join(", ")}.</p>}
    {rows.filter((row) => row.field === "company" && row.errors && row.errors !== "0").map((row) => <p key={row.config}>{row.config}: {row.errors?.includes("APITimeoutError") ? "1 API timeout" : row.errors?.includes("ValidationError") ? "1 validation error" : row.errors}. Cost {row.cost_complete ? "complete" : "incomplete"}.</p>)}
  </div>;
}
