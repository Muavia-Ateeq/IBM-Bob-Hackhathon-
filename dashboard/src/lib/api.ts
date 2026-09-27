const BASE_URL = import.meta.env.VITE_API_URL || "https://trustgate-api-ehib.onrender.com";

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Verdict = "PASS" | "REVIEW" | "BLOCK";
export type CheckerStatus = "ok" | "error" | "timeout";
export type CheckerTier = "deterministic" | "semantic";

export interface Finding {
  checker: string;
  severity: Severity;
  title: string;
  detail: string;
  file: string;
  line: number;
  evidence: string;
  cwe: string | null;
  remediation: string | null;
}

export interface CheckerResult {
  checker: string;
  tier: CheckerTier;
  status: CheckerStatus;
  findings: Finding[];
  duration_ms: number;
  error: string | null;
}

export interface RunRecord {
  run_id: string;
  pr: string;
  written_at: string;
  result: CheckerResult;
}

export interface VerdictRecord {
  verdict: Verdict;
  reason: string;
  degraded: boolean;
  degraded_checkers: string[];
  findings: Finding[];
  results: CheckerResult[];
  input_hash: string;
  duration_ms: number;
  cost_usd: number | null;
}

export interface HealthResponse {
  ok: boolean;
}

export interface RunsResponse {
  count: number;
  unreadable: number;
  runs: RunRecord[];
}

export interface PrVerdictResponse extends VerdictRecord {
  pr: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`health check failed: ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export async function fetchRuns(): Promise<RunsResponse> {
  const response = await fetch(`${BASE_URL}/api/runs`);
  if (!response.ok) {
    throw new Error(`runs fetch failed: ${response.status}`);
  }
  return response.json() as Promise<RunsResponse>;
}

export async function fetchPrVerdict(pr: string): Promise<PrVerdictResponse> {
  const response = await fetch(`${BASE_URL}/api/pr/${encodeURIComponent(pr)}/verdict`);
  if (response.status === 404) {
    throw new Error(`no verdict found for PR: ${pr}`);
  }
  if (!response.ok) {
    throw new Error(`verdict fetch failed: ${response.status}`);
  }
  return response.json() as Promise<PrVerdictResponse>;
}
