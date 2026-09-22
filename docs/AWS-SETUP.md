# AWS setup runbook

Follow this when you are ready to stand up the lab in a real AWS account. Every
step is ordered so cost and security controls exist before anything is created.
Nothing here is required until you choose to run it.

## 0. Create the account

Create a new AWS account, or use an existing one you control. On the new
credit-based Free Tier, remember the account can auto-close at 6 months on the
Free plan; choose the plan deliberately.

## 1. Lock down the root user (before anything else)

- Enable MFA on the root user.
- Do not create root access keys. If any exist, delete them.
- Create an IAM admin user (or an Identity Center user) for daily use, with MFA.
- Sign in as that user from now on, not root.

## 2. Turn on billing alerts

In the Billing and Cost Management console, open Billing preferences and enable
"Receive Billing Alerts." AWS does not publish the billing metric until this is
on, so the alarm this project applies would otherwise never fire.

## 3. Configure credentials locally (never in the repo)

Install the AWS CLI, then:

```bash
aws configure
```

This writes your keys to ~/.aws/credentials, outside the project folder.
Terraform reads them from there automatically. You will never put a key in a
Warden file. Verify with:

```bash
aws sts get-caller-identity
```

## 4. Create the remote-state backend (once)

```bash
cd terraform/bootstrap
terraform init
terraform apply
terraform output          # note bucket, lock table, region
```

## 5. Stand up the lab environment

```bash
cd ../environment
cp backend.hcl.example backend.hcl        # fill in from step 4 output
terraform init -backend-config=backend.hcl
cp terraform.tfvars.example terraform.tfvars   # optional: set alarm_email
terraform plan            # review before applying
terraform apply
```

`backend.hcl` and `terraform.tfvars` are git-ignored, so the account ID and any
email stay off GitHub.

## 6. Confirm the targets exist

```bash
terraform output
```

You should see the public bucket name, the SSH-open security group ID, and the
over-privileged dev user name. These are the M1 detection targets.

## 7. Tear down when idle

```bash
terraform destroy
```

This removes the lab environment. The bootstrap backend from step 4 stays (it
has prevent_destroy on the state bucket). Destroy whenever you are not actively
working to keep spend near zero.

## Cost reminders

- Prefer local kind or k3d over EKS in later milestones; the EKS control plane
  costs about $0.10/hr.
- GuardDuty has a 30-day trial, then usage-based billing.
- Run `terraform destroy` when idle. The backend and the current lab targets
  (no instances) cost effectively nothing at rest.
