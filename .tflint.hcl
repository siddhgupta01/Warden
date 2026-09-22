# tflint configuration.
# Correctness-focused linting (invalid values, deprecated syntax, unused
# declarations). Deeper security scanning (tfsec/checkov) is deferred to M6,
# where the intentional lab targets get annotated so their findings do not mask
# real ones.

config {
  call_module_type = "local"
}

plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "aws" {
  enabled = true
  version = "0.37.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
