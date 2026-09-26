import { useEffect, useState } from "react"
import { fetchRuns, fetchPrVerdict, type PrVerdictResponse } from "./lib/api"

function verdictColor(verdict: string) {
  if (verdict === "PASS") return "#15803D"
  if (verdict === "REVIEW") return "#B45309"
  if (verdict === "BLOCK") return "#DC2626"
  return "#475569"
}

function explainVerdict(v: PrVerdictResponse): string {
  if (v.verdict === "PASS") {
    return "No issues were found. This code is safe to merge."
  }
  const highCount = v.findings.filter(
    (f) => f.severity === "critical" || f.severity === "high"
  ).length

  if (v.verdict === "BLOCK") {
    return `Blocked because ${highCount} high-severity issue${highCount !== 1 ? "s" : ""} ${highCount !== 1 ? "were" : "was"} found.`
  }

  if (v.degraded) {
    return `Flagged for review: some checkers (${v.degraded_checkers.join(", ")}) did not complete, so this cannot be marked safe.`
  }

  return `Flagged for review: ${v.findings.length} issue${v.findings.length !== 1 ? "s" : ""} found that may need a human look.`
}

function App() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [prVerdicts, setPrVerdicts] = useState<PrVerdictResponse[]>([])
  const [selected, setSelected] = useState<PrVerdictResponse | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const runsData = await fetchRuns()

        // Get the unique list of PR identifiers from all run records
        const uniquePrs = Array.from(
          new Set(runsData.runs.map((r) => r.pr))
        )

        // Fetch the real verdict for each PR
        const verdicts: PrVerdictResponse[] = []
        for (const pr of uniquePrs) {
          try {
            const v = await fetchPrVerdict(pr)
            verdicts.push(v)
          } catch {
            // skip PRs whose verdict can't be fetched
          }
        }

        setPrVerdicts(verdicts)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data")
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  return (
    <div style={{ padding: "40px", fontFamily: "sans-serif" }}>
      <h1>TrustGate Dashboard</h1>

      {loading && <p>Loading pull requests…</p>}

      {error && (
        <p style={{ color: "#DC2626" }}>
          Something went wrong: {error}
        </p>
      )}

      {!loading && !error && prVerdicts.length === 0 && (
        <p>No pull requests scanned yet.</p>
      )}

      {!loading &&
        prVerdicts.map((v) => (
          <div
            key={v.pr}
            onClick={() => setSelected(v)}
            style={{
              border: "1px solid #ccc",
              borderRadius: "8px",
              padding: "16px",
              marginBottom: "12px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              cursor: "pointer",
              backgroundColor: selected?.pr === v.pr ? "#f0f0f0" : "white",
            }}
          >
            <span>{v.pr}</span>
            <span
              style={{
                backgroundColor: verdictColor(v.verdict),
                color: "white",
                padding: "4px 12px",
                borderRadius: "999px",
                fontWeight: "bold",
                fontSize: "14px",
              }}
            >
              {v.verdict}
            </span>
          </div>
        ))}

      {selected && (
        <div style={{ marginTop: "30px", borderTop: "2px solid #333", paddingTop: "20px" }}>
          <h2>Details: {selected.pr}</h2>

          <div
            style={{
              backgroundColor: "#eef4ff",
              border: "1px solid #b3d1ff",
              borderRadius: "8px",
              padding: "16px",
              marginBottom: "16px",
              fontSize: "16px",
            }}
          >
            {explainVerdict(selected)}
          </div>

          {selected.findings.length === 0 ? (
            <p>No issues found. ✅</p>
          ) : (
            selected.findings.map((f, i) => (
              <div
                key={i}
                style={{
                  border: "1px solid #eee",
                  borderRadius: "6px",
                  padding: "12px",
                  marginBottom: "10px",
                  backgroundColor: "#fafafa",
                }}
              >
                <p><strong>Checker:</strong> {f.checker}</p>
                <p><strong>File:</strong> {f.file} (line {f.line})</p>
                <p><strong>Severity:</strong> {f.severity}</p>
                <p><strong>Evidence:</strong> {f.evidence}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default App