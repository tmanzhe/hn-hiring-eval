import RungsTable from "../../components/RungsTable";
import { COMMANDS, readRungs } from "../../lib/data";

export default async function RungsPage() {
  const rows = await readRungs();
  return (
    <>
      <h1>Rungs</h1>
      {rows ? <>
        <p>One row per config, split and field. Click column headings to sort.</p>
        <p>Nullable-field accuracy = (extracted + abstained) / n. Precision = extracted / attempts.
          Skills use macro-F1 and have no Wilson interval. Intervals are 95% Wilson; supplied JSON intervals take precedence.</p>
        <p>Cost is total USD per config/split, repeated across its fields. Latency is per post in milliseconds.</p>
        <RungsTable rows={rows} />
      </> : <p>Not generated yet — run {COMMANDS.rungs}</p>}
    </>
  );
}
