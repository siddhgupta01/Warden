# ADR-0001 — Remote Terraform state via a separate bootstrap module

**Status:** Accepted · **Date:** 2026-07-23 · **Milestone:** M0

## Context
Terraform needs somewhere to store state. Local state on a laptop is fine for a
toy, but this is a security project: state can contain secrets and resource
metadata, and it must be shared, versioned, and locked so two runs can't corrupt
it. The standard answer is an S3 backend with a DynamoDB lock table.

That creates a chicken-and-egg problem: the backend (bucket + table) must exist
*before* any module can use it, but the backend is itself AWS infrastructure we'd
want to manage with Terraform.

## Decision
Split the backend out into `terraform/bootstrap/`, which uses **local state on
purpose** and is applied exactly once. It creates:

- an **S3 bucket** for state — versioned (recover from a bad apply), encrypted at
  rest, and with a full public-access block;
- a **DynamoDB table** (`PAY_PER_REQUEST`) for state locking.

Every other module (`terraform/environment/`, later ones) then declares an `s3`
backend pointing at those resources.

## Why these specific choices
- **SSE-S3 (AES256), not KMS, for the state bucket.** State encryption is
  mandatory, but a customer-managed KMS key adds cost and key-management burden
  for no added protection *at this layer*. KMS is reserved for data resources
  where key policy / rotation actually buys us something. Documented so the
  choice is deliberate, not an oversight.
- **DynamoDB lock table**, not the newer S3-native lockfile. Both work;
  DynamoDB locking is the widely-understood, universally-compatible default and
  is effectively free on-demand at lab scale. (Revisit if we drop DynamoDB
  elsewhere.)
- **`prevent_destroy` on the state bucket.** A `terraform destroy` of the lab
  environment must never be able to delete the store that holds its own state.
- **Default tags on everything.** A security tool should never create anonymous
  resources — every Warden-created object is findable in the console and in Cost
  Explorer.

## Consequences
- One extra manual step at setup (`apply` bootstrap once), which is the accepted
  cost of not having a bootstrapping paradox.
- The bootstrap module's own state lives locally and is git-ignored. Losing it
  only loses the *record* of the bucket/table, not the bucket/table themselves;
  they can be re-imported.
