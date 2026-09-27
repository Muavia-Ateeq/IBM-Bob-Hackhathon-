"""TrustGate integration check — one command, four questions, run during a demo.

    python app/main.py --serve            # in another shell
    python integration_test.py --pr 42

The four checks:

1. Is the API up, and how fast is it?
2. Do the run records on disk validate against the real contract?
3. Does the verdict endpoint answer, and with what verdict?
4. Is the gate still carrying the properties that make it a gate?

Checks 2 and 3 must read the same data or they can never agree: check 2 is a local
filesystem read, check 3 is HTTP. Both resolve to `trustgate/backend/runs` — this file
computes it from `REPO_ROOT`, and the engine's `DEFAULT_RUNS_DIR` is anchored to the
package rather than the working directory — so `python app/main.py --serve` finds the same
records from any directory.

The `--base-url` default is that local server for exactly this reason. Do not point it at
the deployed instance: that service is read-only over an empty directory by design, not a
broken deployment (see SYSTEM_LEDGER.md), and it will 404 for any pull request.

`runs/` is gitignored run output. It used to default to a CWD-relative `Path("runs")`, which
silently pointed at nothing whenever the caller was not standing in `trustgate/backend`.

Check 2 validates against `app.schemas.RunRecord`, which is the actual contract. The field
list these checks were originally specified with — `run_id, agent, member, pr, findings,
status` — is a schema this project never built; checking against an invented second schema
would only prove the invention was self-consistent.

Check 4 reads `trustgate.yml` as parsed YAML rather than grepping its text, because the file
documents `pull_request_target` in its own header comment. A substring check for "no
pull_request_target" fails on that comment and would report a working gate as broken.

With no GROQ_API_KEY and no gitleaks binary — the state of K12 and K14 — check 3 answers
`REVIEW` and check 2 reports degraded records. That is the correct output, not a failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The status marks below are not ASCII, and a Windows console still defaults stdout to cp1252,
# which raises UnicodeEncodeError on the first check rather than printing it. Same guard as
# app/main.py.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from pydantic import ValidationError

from app.schemas import RunRecord, Verdict

# The repo root, not trustgate/: this file is trustgate/backend/integration_test.py, and the one
# thing REPO_ROOT is used for is locating .github/workflows/trustgate.yml, which stays at the
# repo root because that is the only place GitHub reads workflows from.
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "trustgate" / "backend" / "runs"
SHA_PIN = re.compile(r"^[0-9a-f]{40}$")

# Built once at import. `urlopen` constructs a fresh opener per call, and on Windows that
# construction calls `getproxies()`, which reads the registry: measured at 644 ms on the
# first request and ~5 ms on every one after. Reusing the opener pays that cost once, ever.
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _get(url: str, timeout: float = 5.0) -> tuple[int, object]:
    with _OPENER.open(url, timeout=timeout) as response:
        return response.status, json.loads(response.read())


def check_health(base_url: str) -> tuple[bool, str]:
    try:
        started = time.perf_counter()
        status, body = _get(f"{base_url}/api/health")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code} {exc.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, f"unreachable — {exc}. Is `python app/main.py --serve` running?"

    if status != 200:
        return False, f"HTTP {status}"
    if not isinstance(body, dict) or body.get("ok") is not True:
        return False, f"expected {{\"ok\": true}}, got {body!r}"
    return True, f"{elapsed_ms}ms"


def check_runs(runs_dir: Path) -> tuple[bool, str]:
    if not runs_dir.is_dir():
        return False, f"no such runs directory: {runs_dir}"
    paths = sorted(runs_dir.glob("*.json"))
    if not paths:
        return False, f"{runs_dir} holds no .json run records — run the engine first"

    invalid: list[str] = []
    for path in paths:
        try:
            RunRecord.model_validate_json(path.read_bytes())
        except (ValidationError, ValueError):
            invalid.append(path.name)

    summary = f"{len(paths) - len(invalid)} valid file(s), {len(invalid)} invalid"
    if invalid:
        return False, f"{summary} — {', '.join(invalid[:3])}"
    return True, summary


def check_verdict(base_url: str, pr: str) -> tuple[bool, str]:
    try:
        _, body = _get(f"{base_url}/api/pr/{pr}/verdict")
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code} {exc.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, f"unreachable — {exc}"

    if not isinstance(body, dict):
        return False, f"expected an object, got {type(body).__name__}"
    for key in ("pr", "verdict", "findings"):
        if key not in body:
            return False, f"response is missing {key!r}"

    verdict = body["verdict"]
    if verdict not in {member.value for member in Verdict}:
        return False, f"verdict {verdict!r} is not one of PASS/REVIEW/BLOCK"

    degraded = body.get("degraded")
    note = "  (degraded run)" if degraded else ""
    return True, f"{verdict} — {len(body['findings'])} finding(s){note}"


def check_gate(workflow: Path) -> tuple[bool, str]:
    import yaml

    if not workflow.is_file():
        return False, f"missing {workflow}"
    document = yaml.safe_load(workflow.read_text(encoding="utf-8"))

    # Bare `on:` is parsed as the boolean True under YAML 1.1, so both keys must be tried.
    triggers = document.get("on", document.get(True)) or {}
    # Every job's steps, not just `gate`. Reading one named job meant a second job's actions
    # were never pin-checked, so a floating tag added anywhere else in this workflow would
    # have passed. Collect across jobs so the next one added is covered without an edit here.
    steps = [step for job in (document.get("jobs") or {}).values() for step in (job.get("steps") or [])]

    pins = [str(step["uses"]) for step in steps if "uses" in step]
    unpinned = [pin for pin in pins if not SHA_PIN.match(pin.split("@", 1)[-1])]

    upload = next((step for step in steps if "upload-sarif" in str(step.get("uses", ""))), None)
    permissions = document.get("permissions") or {}

    invariants = [
        ("pull_request trigger", "pull_request" in triggers),
        ("no pull_request_target", "pull_request_target" not in triggers),
        ("SARIF upload present", upload is not None),
        ("SARIF upload has if: always()", bool(upload) and upload.get("if") == "always()"),
        ("security-events: write", permissions.get("security-events") == "write"),
        (f"{len(pins)} action(s) SHA-pinned", not unpinned),
    ]
    failed = [label for label, ok in invariants if not ok]
    if failed:
        return False, "; ".join(failed)
    return True, f"{len(invariants)} invariants hold, {len(pins)} action(s) pinned"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="integration_test", description="End-to-end smoke check for TrustGate"
    )
    # 127.0.0.1, not `localhost`: a `localhost` request measured 2054–2292 ms against
    # 22–60 ms for the literal address, because `localhost` resolves to ::1 first and the
    # server binds IPv4 only, so every request pays a refused connection before the
    # fallback. Both spellings work; the default is the one that reports honestly.
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--pr", default="42")
    parser.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    parser.add_argument("--workflow", type=Path, default=REPO_ROOT / ".github/workflows/trustgate.yml")
    args = parser.parse_args(argv)

    checks = (
        ("API Health", lambda: check_health(args.base_url)),
        ("Runs Directory", lambda: check_runs(args.runs_dir)),
        ("Verdict Endpoint", lambda: check_verdict(args.base_url, args.pr)),
        ("GitHub Action", lambda: check_gate(args.workflow)),
    )

    print("TrustGate Integration Check\n")
    results = []
    for label, run in checks:
        try:
            ok, detail = run()
        except Exception as exc:  # a check that explodes is a failed check, not a crash
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        results.append(ok)
        print(f"{label + ':':<18} {'✅' if ok else '❌'} {detail}")

    passed = all(results)
    print(f"\nStatus: {'ALL CHECKS PASSED' if passed else 'CHECKS FAILED'}")
    if not passed:
        print(
            "A failed check is a finding, not a bug in this script. "
            f"Checked PR was {args.pr!r} — the run records carry whatever `--pr` was written with."
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
