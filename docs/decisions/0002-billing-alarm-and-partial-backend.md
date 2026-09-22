# ADR-0002: Billing alarm as the first guardrail, and a partial S3 backend

Status: Accepted. Date: 2026-07-23. Milestone: M0.

## Context

Two things must be true before the lab environment is safe to stand up: you must
not get a surprise AWS bill, and you must not leak account identifiers into a
public GitHub repo. This ADR records how the environment module handles both.

## Decision 1: a billing alarm is the first resource

The module ships a CloudWatch EstimatedCharges alarm (default threshold $20)
wired to an SNS topic, before any lab targets exist.

The AWS/Billing metric is published only in us-east-1 regardless of where
resources run, so the alarm and its SNS topic use an aliased us-east-1 provider.
The evaluation period is 6 hours because the billing metric refreshes only a few
times a day. The subscribed email is a variable that defaults to null, so a
personal email never has to be committed; with no address set, the topic is
created with no subscriber. AWS does not emit EstimatedCharges until "Receive
Billing Alerts" is enabled in Billing preferences, a console toggle with no
Terraform equivalent, and that is called out in the code.

## Decision 2: partial backend config keeps the account ID out of git

Terraform's s3 backend block cannot use variables, so the bucket name would
normally be hardcoded, and our bucket name embeds the AWS account ID. Instead the
backend block is left empty and the real values are passed at init from a local,
git-ignored backend.hcl:

    terraform init -backend-config=backend.hcl

A committed backend.hcl.example documents the shape with placeholders, and
.gitignore blocks the real backend.hcl while allowing the example. The repo can
be public without disclosing the account ID.

## Consequences

Init for this module requires the extra -backend-config flag, documented in the
README. The account ID stays private, and anyone cloning the repo supplies their
own, which also makes the module reusable in a different account.
