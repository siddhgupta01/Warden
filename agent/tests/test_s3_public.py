from warden_agent.detectors import s3_public


def test_flags_public_bucket(facts):
    ids = {f.resource_id for f in s3_public.detect(facts)}
    assert "warden-lab-public-target-000000000000" in ids


def test_ignores_clean_bucket(facts):
    ids = {f.resource_id for f in s3_public.detect(facts)}
    assert "warden-lab-clean" not in ids


def test_mapping_and_severity(facts):
    finding = next(
        f for f in s3_public.detect(facts) if "public-target" in f.resource_id
    )
    assert finding.severity.value == "high"
    assert "T1530" in finding.mitre
    assert "CIS AWS 2.1.5" in finding.cis
