"""Shared test fixtures.

A moto-mocked AWS account is planted with the same three misconfigurations the
Terraform targets create, plus clean resources that must NOT be flagged. Because
the scanner talks to AWS through ordinary boto3 calls, moto intercepts them and
the detectors run unchanged, with no real account and no cost.
"""

from __future__ import annotations

import json

import boto3
import pytest
from moto import mock_aws

from warden_agent.scanner import CloudScanner

REGION = "us-east-1"

ALL_BLOCKED = {
    "BlockPublicAcls": True,
    "BlockPublicPolicy": True,
    "IgnorePublicAcls": True,
    "RestrictPublicBuckets": True,
}
NONE_BLOCKED = {k: False for k in ALL_BLOCKED}

PRIVESC_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["iam:AttachUserPolicy", "iam:CreatePolicyVersion"],
            "Resource": "*",
        },
        {"Effect": "Allow", "Action": ["ec2:Describe*"], "Resource": "*"},
    ],
}
READONLY_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Action": ["s3:ListAllMyBuckets"], "Resource": "*"}],
}


@pytest.fixture(autouse=True)
def _aws_credentials(monkeypatch):
    # moto needs credentials present, but they are never used for real.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


def _plant_s3():
    s3 = boto3.client("s3", region_name=REGION)
    s3.create_bucket(Bucket="warden-lab-public-target-000000000000")
    s3.put_public_access_block(
        Bucket="warden-lab-public-target-000000000000",
        PublicAccessBlockConfiguration=NONE_BLOCKED,
    )
    s3.create_bucket(Bucket="warden-lab-clean")
    s3.put_public_access_block(
        Bucket="warden-lab-clean", PublicAccessBlockConfiguration=ALL_BLOCKED
    )


def _plant_security_groups():
    ec2 = boto3.client("ec2", region_name=REGION)
    vpc = ec2.create_vpc(CidrBlock="10.20.0.0/16")["Vpc"]["VpcId"]

    open_sg = ec2.create_security_group(
        GroupName="warden-lab-ssh-open", Description="lab target", VpcId=vpc
    )["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=open_sg,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ],
    )

    scoped_sg = ec2.create_security_group(
        GroupName="warden-lab-ssh-scoped", Description="clean", VpcId=vpc
    )["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=scoped_sg,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "10.0.0.0/8"}],
            }
        ],
    )


def _plant_iam():
    iam = boto3.client("iam")

    iam.create_user(UserName="warden-lab-dev")
    privesc_arn = iam.create_policy(
        PolicyName="warden-lab-dev-overprivileged",
        PolicyDocument=json.dumps(PRIVESC_POLICY),
    )["Policy"]["Arn"]
    iam.attach_user_policy(UserName="warden-lab-dev", PolicyArn=privesc_arn)

    iam.create_user(UserName="warden-lab-readonly")
    ro_arn = iam.create_policy(
        PolicyName="warden-lab-readonly-policy",
        PolicyDocument=json.dumps(READONLY_POLICY),
    )["Policy"]["Arn"]
    iam.attach_user_policy(UserName="warden-lab-readonly", PolicyArn=ro_arn)


@pytest.fixture
def planted_account():
    with mock_aws():
        _plant_s3()
        _plant_security_groups()
        _plant_iam()
        yield


@pytest.fixture
def facts(planted_account):
    return CloudScanner(region=REGION).collect()
