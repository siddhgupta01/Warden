"""Detect S3 buckets that do not block public access.

A bucket is flagged when any of the four Block Public Access settings is off (or
the config is missing entirely). This mirrors the target in
terraform/environment/target_s3_public.tf.

CIS AWS 2.1.5, AWS FSBP S3.8, MITRE ATT&CK T1530 (Data from Cloud Storage).
"""

from __future__ import annotations

from ..models import Finding, Severity
from ..scanner import Facts

_PAB_FLAGS = (
    "BlockPublicAcls",
    "BlockPublicPolicy",
    "IgnorePublicAcls",
    "RestrictPublicBuckets",
)


def detect(facts: Facts) -> list[Finding]:
    findings: list[Finding] = []
    for bucket in facts.buckets:
        pab = bucket["public_access_block"]
        fully_blocked = pab is not None and all(pab.get(f) for f in _PAB_FLAGS)
        if fully_blocked:
            continue
        findings.append(
            Finding(
                id=f"s3-public-access:{bucket['name']}",
                title="S3 bucket does not block public access",
                severity=Severity.HIGH,
                resource_type="AWS::S3::Bucket",
                resource_id=bucket["name"],
                region=facts.region,
                description=(
                    "The bucket's Block Public Access configuration is missing or "
                    "has one or more settings disabled, so it can be exposed via "
                    "ACLs or a bucket policy."
                ),
                cis=("CIS AWS 2.1.5", "AWS FSBP S3.8"),
                mitre=("T1530",),
                evidence={"public_access_block": pab},
                remediation_summary=(
                    "Enable all four S3 Block Public Access settings on the bucket."
                ),
            )
        )
    return findings
