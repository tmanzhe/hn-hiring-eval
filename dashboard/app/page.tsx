import TrendChart from "../components/TrendChart";
import { COMMANDS, readHistory } from "../lib/data";
import { HISTORY_FIELDS } from "../lib/parsers";

export default async function TrendPage() {
  const rows = await readHistory();
  if (!rows) return <><h1>Trend</h1><p>Not generated yet — run {COMMANDS.history}</p></>;
  const latest = rows[rows.length - 1];
  return (
    <>
      <h1>Trend</h1>
      <p>Non-null counts by run, ordered by Toronto date and thread ID. False and empty lists count as non-null.</p>
      <TrendChart rows={rows} />
      <h2>Latest counts</h2>
      <p>{latest.date} · Thread {latest.thread_id} · {latest.total_posts} total posts</p>
      <table>
        <thead><tr><th scope="col">Field</th><th scope="col">Non-null posts</th></tr></thead>
        <tbody>{HISTORY_FIELDS.map((field) => (
          <tr key={field}><th scope="row">{field}</th><td>{latest[field]}</td></tr>
        ))}</tbody>
      </table>
    </>
  );
}
