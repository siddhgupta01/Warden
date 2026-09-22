# ADR-0001: Remote Terraform state via a separate bootstrap module

Status: Accepted. Date: 2026-07-23. Milestone: M0.

## Context

Terraform needs somewhere to store state. Local state is fine for a toy, but
this is a security project: state can contain secrets and resource metadata, and
it must be shared, versioned, and locked so two runs cannot corrupt it. The
standard answer is an S3 backend with a DynamoDB lock table.

That creates a chicken-and-egg problem: the backend must exist before any module
can use it, but the backend is itself AWS infrastructure we want to manage with
Terraform.

## Decision

Split the backend into `terraform/bootstrap/`, which uses local state on purpose
and is applied once. It creates an S3 bucket for state (versioned, encrypted,
public access fully blocked) and a DynamoDB table (PAY_PER_REQUEST) for locking.
Every other module then declares an s3 backend pointing at those resources.

## Why these choices

SSE-S3 (AES256), not KMS, for the state bucket. Encryption is mandatory, but a
customer-managed KMS key adds cost and key management for no added protection at
this layer. KMS is reserved for data resources where key policy and rotation
actually buy something.

DynamoDB lock table, not the newer S3-native lockfile. Both work; DynamoDB
locking is the widely understood default and is effectively free on-demand at
lab scale.

`prevent_destroy` on the state bucket, so a destroy of the lab environment can
never delete the store that holds its own state.

Default tags on everything, so a security tool never creates anonymous
resources; every object is findable in the console and in Cost Explorer.

## Consequences

One extra manual step at setup (apply bootstrap once), which is the accepted cost
of not having a bootstrapping paradox. The bootstrap module's own state lives
locally and is git-ignored; losing it only loses the record of the bucket and
table, not the resources themselves, which can be re-imported.
