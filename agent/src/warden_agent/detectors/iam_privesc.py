"""Detect IAM users whose policies allow privilege escalation to admin.

Mirrors terraform/environment/target_iam_privesc.tf. The detector looks for a set
of IAM actions that let a principal grant itself more access (attach any policy,
rewrite a managed policy's default version, and similar), allowed on a wildcard
resource.

MITRE ATT&CK T1098 (Account Manipulation), T1548 (Abuse Elevation Control
Mechanism); over-privilege per CSA "Overprivileged by Design".
"""

from __future__ import annotations

from ..models import Finding, Severity
from ..scanner import Facts

# Actions that, allowed broadly, create a path to administrator. Lowercased for
# case-insensitive matching (IAM treats action names case-insensitively).
DANGEROUS_ACTIONS = {
    "iam:attachuserpolicy",
    "iam:attachrolepolicy",
    "iam:attachgrouppolicy",
    "iam:putuserpolicy",
    "iam:putrolepolicy",
    "iam:putgrouppolicy",
    "iam:createpolicyversion",
    "iam:setdefaultpolicyversion",
    "iam:createaccesskey",
    "iam:updateassumerolepolicy",
    "iam:addusertogroup",
}


def _statements(doc: dict) -> list[dict]:
    stmts = doc.get("Statement", [])
    return stmts if isinstance(stmts, list) else [stmts]


def _actions(statement: dict) -> list[str]:
    actions = statement.get("Action", [])
    if isinstance(actions, str):
        actions = [actions]
    return [a.lower() for a in actions]


def _matched_dangerous(doc: dict) -> set[str]:
    hits: set[str] = set()
    for st in _statements(doc):
        if st.get("Effect") != "Allow":
            continue
        for action in _actions(st):
            if action in ("*", "iam:*"):
                hits.add(action)
            elif action in DANGEROUS_ACTIONS:
                hits.add(action)
            elif action.endswith("*") and action.startswith("iam:"):
                prefix = action[:-1]
                hits.update(d for d in DANGEROUS_ACTIONS if d.startswith(prefix))
    return hits


def detect(facts: Facts) -> list[Finding]:
    findings: list[Finding] = []
    for user in facts.iam_users:
        hits: set[str] = set()
        evidence_policies = []
        for policy in user["policies"]:
            matched = _matched_dangerous(policy["document"])
            if matched:
                hits |= matched
                evidence_policies.append(
                    {"policy": policy["name"], "actions": sorted(matched)}
                )
        if not hits:
            continue
        findings.append(
            Finding(
                id=f"iam-privesc:{user['user']}",
                title="IAM user can escalate privileges toward administrator",
                severity=Severity.CRITICAL,
                resource_type="AWS::IAM::User",
                resource_id=user["user"],
                region="global",
                description=(
                    "The user holds policy permissions that allow self-escalation "
                    "(for example attaching an arbitrary managed policy or rewriting "
                    "a policy's default version), which is a path to administrator."
                ),
                cis=(),
                mitre=("T1098", "T1548"),
                evidence={"dangerous_actions": sorted(hits), "policies": evidence_policies},
                remediation_summary=(
                    "Remove the privilege-escalation IAM actions or scope them to "
                    "specific, non-IAM-altering resources."
                ),
            )
        )
    return findings
