import DisagreementsTable from "../../components/DisagreementsTable";
import { COMMANDS, readDisagreements } from "../../lib/data";

export default async function DisagreementsPage() {
  const entries = await readDisagreements();
  return (
    <>
      <h1>Disagreements</h1>
      {entries ? <>
        <p>Gold-label disagreements by field and config. Label salaries retain their original period; model salary bounds are annualized.</p>
        <DisagreementsTable entries={entries} />
      </> : <p>Not generated yet — run {COMMANDS.disagreements}</p>}
    </>
  );
}
