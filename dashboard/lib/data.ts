import { readFile } from "node:fs/promises";
import path from "node:path";
import { parseBaselineRuns, parseDisagreements, parseFixtureThread, parseHistory, parsePipelineLabels, parseRungs } from "./parsers.ts";

export const COMMANDS = {
  history: "uv run ingest/rules_history.py --thread 48747976 --history data/rules_history.jsonl",
  rungs: "uv run --env-file .env --extra agent evals/ladder.py --split all",
  disagreements: "uv run --env-file .env --extra agent evals/ladder.py --split all --disagreements",
};

// These readers are called only by force-static server pages during the build.
async function read<T>(file: string, parse: (text: string) => T): Promise<T | null> {
  try {
    return parse(await readFile(path.resolve(process.cwd(), "..", file), "utf8"));
  } catch {
    return null;
  }
}

export const readHistory = () => read("data/rules_history.jsonl", parseHistory);
export const readRungs = () => read("evals/cost-quality.json", parseRungs);
export const readDisagreements = () => read("evals/disagreements.md", parseDisagreements);
export const readPipelineLabels = () => read("evals/labeled.jsonl", parsePipelineLabels);
export const readFixtureThread = () => read("tests/fixtures/sample_thread.json", parseFixtureThread);
export const readBaselineRuns = () => read("evals/runs.jsonl", parseBaselineRuns);
