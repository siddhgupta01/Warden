"""Detect security groups that allow SSH (22/tcp) from the whole internet.

Mirrors terraform/environment/target_sg_ssh_open.tf.

CIS AWS 5.2, AWS FSBP EC2.13, MITRE ATT&CK T1021.004 (Remote Services: SSH),
reachable via T1190.
"""

from __future__ import annotations

from ..models import Finding, Severity
from ..scanner import Facts

_OPEN_V4 = "0.0.0.0/0"
_OPEN_V6 = "::/0"
_SSH_PORT = 22


def _rule_opens_ssh(rule: dict) -> bool:
    proto = rule.get("ip_protocol")
    # "-1" means all protocols and all ports.
    all_ports = proto == "-1"
    if proto not in ("tcp", "-1"):
        return False
    if not all_ports:
        fp, tp = rule.get("from_port"), rule.get("to_port")
        if fp is None or tp is None or not (fp <= _SSH_PORT <= tp):
            return False
    open_to_world = _OPEN_V4 in (rule.get("cidr_ipv4") or []) or _OPEN_V6 in (
        rule.get("cidr_ipv6") or []
    )
    return open_to_world


def detect(facts: Facts) -> list[Finding]:
    findings: list[Finding] = []
    for sg in facts.security_groups:
        offending = [r for r in sg["ingress"] if _rule_opens_ssh(r)]
        if not offending:
            continue
        findings.append(
            Finding(
                id=f"sg-ssh-open:{sg['id']}",
                title="Security group allows SSH from the entire internet",
                severity=Severity.HIGH,
                resource_type="AWS::EC2::SecurityGroup",
                resource_id=sg["id"],
                region=facts.region,
                description=(
                    "An ingress rule exposes TCP port 22 to 0.0.0.0/0 (or ::/0), "
                    "allowing SSH connection attempts from anywhere."
                ),
                cis=("CIS AWS 5.2", "AWS FSBP EC2.13"),
                mitre=("T1021.004",),
                evidence={"group_name": sg["name"], "rules": offending},
                remediation_summary=(
                    "Restrict the ingress rule to known admin CIDRs or remove it."
                ),
            )
        )
    return findings
