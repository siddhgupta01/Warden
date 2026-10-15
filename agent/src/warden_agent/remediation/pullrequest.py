"""Turn findings into a remediation pull request.

The agent never changes infrastructure or merges anything. It builds a plan (a
branch name, the fix files, and a PR description), and either writes that plan
locally for review (dry run) or opens a real pull request via the GitHub API for
a human to review and merge. Human-in-the-loop is the whole point.

The GitHub API path is only exercised when a token is supplied, so the pure
plan-building and local-write paths are fully unit-tested without network.
"""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass

from ..models import Finding
from . import terraform

try:  # requests is only needed to actually open a PR; tests inject a session.
    import requests
except ImportError:  # pragma: no cover
    requests = None


@dataclass(frozen=True)
class RemediationPlan:
    branch: str
    pr_title: str
    pr_body: str
    files: tuple[tuple[str, str], ...]  # (repo-relative path, content)


class GitHubError(RuntimeError):
    pass


def render_pr_body(findings: list[Finding]) -> str:
    lines = [
        "## Warden remediation",
        "",
        "Automated fix proposal. Review before merging. Each change is minimal and",
        "reversible; nothing here was applied to infrastructure.",
        "",
        f"Addresses {len(findings)} finding(s):",
        "",
    ]
    for f in findings:
        frameworks = ", ".join([*f.cis, *f.mitre]) or "-"
        lines.append(f"- **{f.severity.value.upper()}** {f.title} on `{f.resource_id}` ({frameworks})")
    lines.append("")
    return "\n".join(lines)


def build_plan(findings: list[Finding], branch_prefix: str = "warden/remediation") -> RemediationPlan | None:
    proposals = [p for p in (terraform.generate_fix(f) for f in findings) if p is not None]
    if not proposals:
        return None
    files = tuple((p.path, p.content) for p in proposals)
    branch = f"{branch_prefix}-{int(time.time())}"
    title = f"Warden: remediate {len(proposals)} finding(s)"
    return RemediationPlan(branch=branch, pr_title=title, pr_body=render_pr_body(findings), files=files)


def write_plan_locally(plan: RemediationPlan, out_dir: str) -> list[str]:
    """Write the plan's files under out_dir for review. Returns written paths."""
    written = []
    for path, content in plan.files:
        dest = os.path.join(out_dir, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(content)
        written.append(dest)
    body_path = os.path.join(out_dir, "PULL_REQUEST.md")
    with open(body_path, "w", encoding="utf-8") as fh:
        fh.write(plan.pr_body)
    written.append(body_path)
    return written


def open_pull_request(
    plan: RemediationPlan,
    repo: str,
    token: str,
    base: str = "main",
    session=None,
    api: str = "https://api.github.com",
) -> str:
    """Create a branch, commit the fix files, and open a PR. Returns the PR URL.

    `repo` is "owner/name". `session` is a requests-like session (injected in
    tests); when omitted a real requests.Session is used.
    """
    if session is None:
        if requests is None:  # pragma: no cover
            raise GitHubError("requests is not installed; cannot open a pull request")
        session = requests.Session()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # 1. Resolve the base branch head.
    r = session.get(f"{api}/repos/{repo}/git/ref/heads/{base}", headers=headers)
    _check(r, "resolve base branch")
    base_sha = r.json()["object"]["sha"]

    # 2. Create the remediation branch.
    r = session.post(
        f"{api}/repos/{repo}/git/refs",
        headers=headers,
        json={"ref": f"refs/heads/{plan.branch}", "sha": base_sha},
    )
    _check(r, "create branch")

    # 3. Add each fix file on the new branch.
    for path, content in plan.files:
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        r = session.put(
            f"{api}/repos/{repo}/contents/{path}",
            headers=headers,
            json={
                "message": f"Warden remediation: {path}",
                "content": encoded,
                "branch": plan.branch,
            },
        )
        _check(r, f"add {path}")

    # 4. Open the pull request.
    r = session.post(
        f"{api}/repos/{repo}/pulls",
        headers=headers,
        json={"title": plan.pr_title, "head": plan.branch, "base": base, "body": plan.pr_body},
    )
    _check(r, "open pull request")
    return r.json().get("html_url", "")


def _check(response, what: str) -> None:
    if response.status_code // 100 != 2:
        body = getattr(response, "text", "")
        raise GitHubError(f"GitHub API failed to {what}: HTTP {response.status_code} {body}")
