"""Collect raw resource facts from AWS.

The scanner is the only part that talks to AWS. Detectors never call boto3
directly; they read the normalized facts this produces. That separation is what
lets the whole detection layer be unit-tested against moto (a fake AWS) with no
real account and no cost: tests set up moto, the scanner reads from it through
ordinary boto3 calls, and detectors run unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from urllib.parse import unquote

import boto3


@dataclass
class Facts:
    """Normalized snapshot of the parts of the account Warden inspects."""

    region: str
    buckets: list[dict] = field(default_factory=list)
    security_groups: list[dict] = field(default_factory=list)
    iam_users: list[dict] = field(default_factory=list)


class CloudScanner:
    def __init__(self, region: str = "us-east-1", session: boto3.Session | None = None):
        self.region = region
        self._session = session or boto3.Session()

    def collect(self) -> Facts:
        return Facts(
            region=self.region,
            buckets=self._buckets(),
            security_groups=self._security_groups(),
            iam_users=self._iam_users(),
        )

    # --- S3 ---------------------------------------------------------------
    def _buckets(self) -> list[dict]:
        s3 = self._session.client("s3", region_name=self.region)
        out = []
        for b in s3.list_buckets().get("Buckets", []):
            name = b["Name"]
            pab = None
            try:
                resp = s3.get_public_access_block(Bucket=name)
                pab = resp["PublicAccessBlockConfiguration"]
            except s3.exceptions.ClientError:
                # No PAB configured at all is itself a public-access risk.
                pab = None
            out.append({"name": name, "public_access_block": pab})
        return out

    # --- EC2 security groups ---------------------------------------------
    def _security_groups(self) -> list[dict]:
        ec2 = self._session.client("ec2", region_name=self.region)
        out = []
        for sg in ec2.describe_security_groups().get("SecurityGroups", []):
            ingress = []
            for perm in sg.get("IpPermissions", []):
                ingress.append(
                    {
                        "ip_protocol": perm.get("IpProtocol"),
                        "from_port": perm.get("FromPort"),
                        "to_port": perm.get("ToPort"),
                        "cidr_ipv4": [r.get("CidrIp") for r in perm.get("IpRanges", [])],
                        "cidr_ipv6": [r.get("CidrIpv6") for r in perm.get("Ipv6Ranges", [])],
                    }
                )
            out.append(
                {
                    "id": sg["GroupId"],
                    "name": sg.get("GroupName"),
                    "vpc_id": sg.get("VpcId"),
                    "ingress": ingress,
                }
            )
        return out

    # --- IAM --------------------------------------------------------------
    def _iam_users(self) -> list[dict]:
        iam = self._session.client("iam")
        out = []
        for u in iam.list_users().get("Users", []):
            user = u["UserName"]
            policies = []

            # Managed policies attached to the user.
            for ap in iam.list_attached_user_policies(UserName=user).get(
                "AttachedPolicies", []
            ):
                arn = ap["PolicyArn"]
                doc = self._managed_policy_document(iam, arn)
                if doc is not None:
                    policies.append({"name": ap["PolicyName"], "arn": arn, "document": doc})

            # Inline policies on the user.
            for pname in iam.list_user_policies(UserName=user).get("PolicyNames", []):
                resp = iam.get_user_policy(UserName=user, PolicyName=pname)
                policies.append(
                    {
                        "name": pname,
                        "arn": None,
                        "document": _as_policy_doc(resp["PolicyDocument"]),
                    }
                )

            out.append({"user": user, "policies": policies})
        return out

    @staticmethod
    def _managed_policy_document(iam, arn: str) -> dict | None:
        try:
            version_id = iam.get_policy(PolicyArn=arn)["Policy"]["DefaultVersionId"]
            doc = iam.get_policy_version(PolicyArn=arn, VersionId=version_id)[
                "PolicyVersion"
            ]["Document"]
            return _as_policy_doc(doc)
        except iam.exceptions.ClientError:
            return None


def _as_policy_doc(doc) -> dict:
    """IAM policy documents come back either as a dict or a URL-encoded JSON
    string depending on the call. Normalize to a dict."""
    if isinstance(doc, dict):
        return doc
    return json.loads(unquote(doc))
