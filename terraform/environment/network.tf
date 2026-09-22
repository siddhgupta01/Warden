# Minimal lab VPC.
#
# A security group needs a VPC, so the lab gets its own small one rather than
# relying on or mutating the account's default VPC. It has no internet gateway,
# NAT, or instances; none are needed for M0, and leaving them out keeps cost at
# zero and makes destroy clean. The subnet exists so the network is realistic
# for later milestones; nothing is placed in it yet.

resource "aws_vpc" "lab" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

resource "aws_subnet" "lab" {
  vpc_id            = aws_vpc.lab.id
  cidr_block        = "10.20.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "${var.name_prefix}-subnet"
  }
}
