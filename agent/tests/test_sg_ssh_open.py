from warden_agent.detectors import sg_ssh_open


def test_flags_open_ssh(facts):
    names = {f.evidence["group_name"] for f in sg_ssh_open.detect(facts)}
    assert "warden-lab-ssh-open" in names


def test_ignores_scoped_ssh(facts):
    names = {f.evidence["group_name"] for f in sg_ssh_open.detect(facts)}
    assert "warden-lab-ssh-scoped" not in names


def test_mapping_and_severity(facts):
    finding = next(
        f for f in sg_ssh_open.detect(facts) if f.evidence["group_name"] == "warden-lab-ssh-open"
    )
    assert finding.severity.value == "high"
    assert "T1021.004" in finding.mitre
    assert "CIS AWS 5.2" in finding.cis


def test_rule_matcher_all_protocols():
    rule = {"ip_protocol": "-1", "from_port": None, "to_port": None, "cidr_ipv4": ["0.0.0.0/0"], "cidr_ipv6": []}
    assert sg_ssh_open._rule_opens_ssh(rule) is True


def test_rule_matcher_other_port():
    rule = {"ip_protocol": "tcp", "from_port": 443, "to_port": 443, "cidr_ipv4": ["0.0.0.0/0"], "cidr_ipv6": []}
    assert sg_ssh_open._rule_opens_ssh(rule) is False
