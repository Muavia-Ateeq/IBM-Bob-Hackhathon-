import { useState } from "react"
import type { Verdict } from "../lib/api"

export interface Override {
  reason: string;
  timestamp: string;
}

interface Props {
  pr: string;
  originalVerdict: Verdict;
  override: Override | null;
  onOverride: (override: Override) => void;
}

const ORIGINAL_LABEL: Record<Verdict, string> = {
  BLOCK: "⊗ BLOCK",
  REVIEW: "⚠ REVIEW",
  PASS: "✓ PASS",
}

const ORIGINAL_COLOR: Record<Verdict, string> = {
  BLOCK: "#DC2626",
  REVIEW: "#B45309",
  PASS: "#15803D",
}

export function ApprovalOverride({ pr, originalVerdict, override, onOverride }: Props) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState("")
  const [touched, setTouched] = useState(false)

  const eligible = originalVerdict === "BLOCK" || originalVerdict === "REVIEW"

  if (!eligible) return null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setTouched(true)
    if (!draft.trim()) return
    onOverride({ reason: draft.trim(), timestamp: new Date().toISOString() })
    setOpen(false)
    setDraft("")
    setTouched(false)
  }

  function handleCancel() {
    setOpen(false)
    setDraft("")
    setTouched(false)
  }

  return (
    <div
      style={{
        border: "1px solid #E2E8F0",
        borderRadius: "8px",
        padding: "16px",
        marginTop: "16px",
        backgroundColor: "#F8FAFC",
      }}
    >
      {override ? (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
            <span
              style={{
                backgroundColor: "#15803D",
                color: "white",
                padding: "4px 12px",
                borderRadius: "999px",
                fontWeight: "bold",
                fontSize: "14px",
              }}
            >
              ✓ PASS (overridden)
            </span>
            <span
              style={{
                color: ORIGINAL_COLOR[originalVerdict],
                fontSize: "13px",
                fontWeight: 500,
              }}
            >
              Original: {ORIGINAL_LABEL[originalVerdict]}
            </span>
          </div>
          <p style={{ margin: "8px 0 4px", fontSize: "14px", color: "#0F172A" }}>
            <strong>Override reason:</strong> {override.reason}
          </p>
          <p style={{ margin: 0, fontSize: "12px", color: "#475569" }}>
            Approved at {new Date(override.timestamp).toUTCString()} · PR {pr}
          </p>
        </div>
      ) : (
        <div>
          {!open && (
            <button
              onClick={() => setOpen(true)}
              style={{
                backgroundColor: "#3b82d4",
                color: "white",
                border: "none",
                borderRadius: "6px",
                padding: "8px 16px",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Override to PASS
            </button>
          )}
          {open && (
            <form onSubmit={handleSubmit} noValidate>
              <label
                htmlFor={`override-reason-${pr}`}
                style={{ display: "block", fontSize: "14px", fontWeight: 600, marginBottom: "8px", color: "#0F172A" }}
              >
                Reason for override (required)
              </label>
              <textarea
                id={`override-reason-${pr}`}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onBlur={() => setTouched(true)}
                rows={3}
                placeholder="Explain why this is safe to merge despite the verdict…"
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  border: touched && !draft.trim() ? "1px solid #DC2626" : "1px solid #E2E8F0",
                  borderRadius: "6px",
                  padding: "8px",
                  fontSize: "14px",
                  resize: "vertical",
                  color: "#0F172A",
                }}
              />
              {touched && !draft.trim() && (
                <p role="alert" style={{ margin: "4px 0 8px", fontSize: "13px", color: "#DC2626" }}>
                  A reason is required before overriding.
                </p>
              )}
              <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
                <button
                  type="submit"
                  style={{
                    backgroundColor: "#15803D",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    padding: "8px 16px",
                    fontSize: "14px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Confirm Override
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  style={{
                    backgroundColor: "transparent",
                    color: "#475569",
                    border: "1px solid #E2E8F0",
                    borderRadius: "6px",
                    padding: "8px 16px",
                    fontSize: "14px",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  )
}
