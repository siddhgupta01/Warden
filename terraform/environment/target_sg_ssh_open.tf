# DELIBERATE MISCONFIGURATION: detection target, not a mistake.
#
# Finding:   Security group allows SSH (22/tcp) from the entire internet.
# Mapped to: CIS AWS 5.2, AWS FSBP EC2.13, MITRE ATT&CK T1021.004 (reachable
#            via T1190).
# Purpose:   Warden (M1) detects the open rule and opens a Terraform PR that
#            scopes ingress down or removes it.
# Note:      No EC2 instance is attached, so cost stays zero. The open ingress
#            rule is itself the finding; it does not need a live host to be a
#            valid detection.

resource "aws_security_group" "ssh_open" {
  name        = "${var.name_prefix}-ssh-open"
  description = "LAB TARGET: intentionally allows SSH from anywhere"
  vpc_id      = aws_vpc.lab.id

  tags = {
    Name          = "${var.name_prefix}-ssh-open"
    WardenTarget  = "true"
    WardenFinding = "sg-ssh-open-world"
  }
}

# The misconfig: 22/tcp open to 0.0.0.0/0.
resource "aws_vpc_security_group_ingress_rule" "ssh_from_anywhere" {
  security_group_id = aws_security_group.ssh_open.id
  description       = "SSH from the entire internet (deliberate finding)"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = "0.0.0.0/0"
}

# Wide-open egress is the common default; tightening egress is a later story.
resource "aws_vpc_security_group_egress_rule" "all_out" {
  security_group_id = aws_security_group.ssh_open.id
  description       = "Allow all outbound"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
