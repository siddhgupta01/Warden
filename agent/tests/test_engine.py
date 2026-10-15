from warden_agent.engine import Engine
from warden_agent.remediation import terraform
from warden_agent.report import to_json, to_markdown


def test_engine_finds_all_three_classes(facts):
    findings = Engine.run_on(facts)
    kinds = {f.id.split(":", 1)[0] for f in findings}
    assert kinds == {"s3-public-access", "sg-ssh-open", "iam-privesc"}


def test_engine_sorts_critical_first(facts):
    findings = Engine.run_on(facts)
    assert findings[0].severity.value == "critical"


def test_report_markdown_has_table(facts):
    md = to_markdown(Engine.run_on(facts))
    assert "| Severity |" in md
    assert "MITRE ATT&CK" in md


def test_report_json_roundtrips(facts):
    import json

    data = json.loads(to_json(Engine.run_on(facts)))
    assert all("severity" in row for row in data)


def test_remediation_generated_for_every_finding(facts):
    for f in Engine.run_on(facts):
        proposal = terraform.generate_fix(f)
        assert proposal is not None
        assert proposal.content.strip()
        assert proposal.path.endswith(".tf")


def test_s3_fix_enables_block_public_access(facts):
    s3_finding = next(f for f in Engine.run_on(facts) if f.id.startswith("s3-public-access"))
    content = terraform.generate_fix(s3_finding).content
    assert "block_public_acls       = true" in content
    assert "restrict_public_buckets = true" in content
