"""Render a TrustGate verdict as a pull-request comment and post it.

Read this before wiring this into `.github/workflows/trustgate.yml`. It is not wired in, and
it must not be, without solving a problem that has not been solved here.

Under `pull_request` — the only trigger this repository uses — `GITHUB_TOKEN` is read-only and
a fork receives no token at all; `trustgate.yml` declares `pull-requests: read` and nothing
wider. Posting a comment from inside the gate therefore needs either `pull_request_target`,
which `trustgate.yml` documents as remote code execution with `GROQ_API_KEY` in reach, or a
GitHub App with its own installation token. Neither exists. So this runs from a developer's
machine, or from `workflow_dispatch`, and `trustgate.yml` is not modified.

There is no numeric score anywhere in this file. The verdict comes from `adjudicate()` via
`compute_verdict`, which is a pure function; see `SYSTEM_LEDGER.md` for why the 5/2/1 score
these comments were originally specified with was declined.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.runlog import DEFAULT_RUNS_DIR, compute_verdict
from app.schemas import Severity, Verdict, VerdictRecord

# Every level in `Severity` gets a glyph. Colour is never the only carrier: each cell also
# carries the uppercase label, because red/amber/green is unreadable for roughly 1 in 12 men
# with red-green colour vision deficiency.
SEVERITY_EMOJI = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🟢",
    Severity.INFO: "⚪",
}

VERDICT_EMOJI = {
    Verdict.BLOCK: "🔴",
    Verdict.REVIEW: "🟡",
    Verdict.PASS: "🟢",
}

MAX_EVIDENCE = 120
_BACKTICK_RUN = re.compile(r"`+")


def _code(text: str) -> str:
    """Render text as a markdown code span, safe inside a table cell.

    Newlines and pipes are removed rather than escaped because both silently destroy a table
    row: a raw newline splits the row and an unescaped pipe adds a column. The backtick fence
    is sized to the longest run in the content, so evidence that itself contains backticks
    still renders instead of ending the span early and dumping raw markup into the comment.
    """
    flat = " ".join(text.split()).replace("|", "\\|")
    if len(flat) > MAX_EVIDENCE:
        flat = flat[:MAX_EVIDENCE].rstrip() + "…"
    longest = max((len(run) for run in _BACKTICK_RUN.findall(flat)), default=0)
    fence = "`" * (longest + 1)
    pad = " " if flat.startswith("`") or flat.endswith("`") else ""
    return f"{fence}{pad}{flat}{pad}{fence}"


def _explain(record: VerdictRecord) -> str:
    if record.verdict is Verdict.BLOCK:
        return (
            "A finding at `critical` or `high` severity was reported. The pull request should "
            "not merge until it is resolved or a human overrides it with a reason."
        )
    if record.verdict is Verdict.REVIEW:
        return (
            "A finding at `medium`, `low`, or `info` was reported, or at least one checker "
            "did not complete. **A degraded run is never a pass** — some of this diff was not "
            "reviewed."
        )
    return "Every checker completed and reported nothing. This is the only state that is a pass."


def render_comment(record: VerdictRecord) -> str:
    """Format a verdict as markdown. Pure: no I/O, no clock, no network."""
    checker_count = len(record.results)
    emoji = VERDICT_EMOJI[record.verdict]

    lines = [
        f"{emoji} **TrustGate Verdict: {record.verdict.value}**",
        "",
        f"{checker_count} automated checker{'' if checker_count == 1 else 's'} ran in parallel "
        "on this pull request.",
        "",
    ]

    if record.findings:
        lines += [
            "### Findings",
            "",
            "| Checker | File | Line | Severity | Evidence |",
            "|---|---|---|---|---|",
        ]
        for finding in record.findings:
            glyph = SEVERITY_EMOJI[finding.severity]
            lines.append(
                f"| `{finding.checker}` | `{finding.file}` | {finding.line} "
                f"| {glyph} {finding.severity.value.upper()} | {_code(finding.evidence)} |"
            )
        lines.append("")
    else:
        lines += ["### Findings", "", "None reported.", ""]

    lines += [
        f"**Why {record.verdict.value}?** {record.reason}. {_explain(record)}",
        "",
    ]

    if record.degraded:
        names = ", ".join(f"`{name}`" for name in record.degraded_checkers) or "the run itself"
        lines += [
            f"> **Degraded:** {names} did not complete. The verdict above accounts for the "
            "findings that were produced, not for the review that did not happen.",
            "",
        ]

    lines.append(
        "<sub>TrustGate renders a verdict; it never merges your code. A human decides.</sub>"
    )
    return "\n".join(lines)


def post_comment(repo: str, pr: str, body: str, token: str) -> str:
    """POST the comment and return its html_url. Raises on any API failure."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
    request = urllib.request.Request(
        url,
        data=body.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "TrustGate",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read()).get("html_url", url)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="app.comment", description="Post a TrustGate verdict to a pull request"
    )
    parser.add_argument("--pr", required=True, help="pull request number")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--repo", help="owner/name; defaults to $GITHUB_REPOSITORY")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the comment and exit without posting"
    )
    args = parser.parse_args(argv)

    try:
        record = compute_verdict(args.pr, args.runs_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    body = render_comment(record)
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY")

    print(f"--- comment for {repo or '<no repo>'}#{args.pr} ---")
    print(body)
    print("--- end ---")

    if args.dry_run:
        print("\nDRY RUN — nothing was posted.")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    if not token or not token.strip():
        print(
            "GITHUB_TOKEN is not set. Export it, or pass --dry-run to print the comment only.",
            file=sys.stderr,
        )
        return 2
    if not repo or repo.count("/") != 1:
        print(
            "GITHUB_REPOSITORY is not set to owner/name. Set it, or pass --repo owner/name.",
            file=sys.stderr,
        )
        return 2

    try:
        posted = post_comment(repo, args.pr, body, token.strip())
    except urllib.error.HTTPError as exc:
        print(f"GitHub returned {exc.code} {exc.reason}: {exc.read().decode('utf-8', 'replace')}",
              file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"could not reach api.github.com: {exc.reason}", file=sys.stderr)
        return 1

    print(f"\nPosted: {posted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
