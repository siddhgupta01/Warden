from warden_agent.detectors import iam_privesc


def test_flags_privesc_user(facts):
    ids = {f.resource_id for f in iam_privesc.detect(facts)}
    assert "warden-lab-dev" in ids


def test_ignores_readonly_user(facts):
    ids = {f.resource_id for f in iam_privesc.detect(facts)}
    assert "warden-lab-readonly" not in ids


def test_mapping_and_evidence(facts):
    finding = next(f for f in iam_privesc.detect(facts) if f.resource_id == "warden-lab-dev")
    assert finding.severity.value == "critical"
    assert "T1098" in finding.mitre
    assert "iam:attachuserpolicy" in finding.evidence["dangerous_actions"]


def test_matcher_wildcard_prefix():
    doc = {"Statement": [{"Effect": "Allow", "Action": "iam:Attach*", "Resource": "*"}]}
    hits = iam_privesc._matched_dangerous(doc)
    assert "iam:attachuserpolicy" in hits


def test_matcher_ignores_deny():
    doc = {"Statement": [{"Effect": "Deny", "Action": "iam:AttachUserPolicy", "Resource": "*"}]}
    assert iam_privesc._matched_dangerous(doc) == set()
