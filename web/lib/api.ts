// Every fetch here runs on the server, so the API URL never reaches the browser and the
// container can talk to the API over its internal address.
//
// No caching. The jobs table and the evals page are the two things a reader is most likely to
// doubt, and a stale number is worse than a slow one.

const BASE = process.env.API_URL ?? "http://127.0.0.1:8000";

export type Job = {
  comment_id: number;
  company: string | null;
  location: string | null;
  remote: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_period: string | null;
  seniority: string | null;
  skills: string[];
  thread_month: string;
};

export type TrendPoint = {
  thread_month: string;
  skill: string;
  postings: number;
  share: number;
};

export type EvalsPayload = {
  runs: Record<string, unknown>[];
  n?: number;
  note?: string;
};

export class ApiDown extends Error {}

async function get<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  } catch {
    throw new ApiDown(`cannot reach the API at ${BASE}`);
  }
  if (!res.ok) throw new ApiDown(`${path} returned ${res.status}`);
  return res.json() as Promise<T>;
}

export const getJobs = (qs: string) => get<Job[]>(`/api/jobs${qs ? `?${qs}` : ""}`);
export const getTrends = (qs: string) => get<TrendPoint[]>(`/api/trends${qs ? `?${qs}` : ""}`);
export const getEvals = () => get<EvalsPayload>("/api/evals");
export const apiBase = () => BASE;
