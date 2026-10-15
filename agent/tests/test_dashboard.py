from warden_agent.dashboard import to_html
from warden_agent.engine import Engine


def test_dashboard_is_valid_html_with_findings(facts):
    html = to_html(Engine.run_on(facts))
    assert "<!doctype html>" in html
    assert "<table" in html
    assert "CRITICAL" in html


def test_dashboard_lists_resources_and_severity_tiles(facts):
    html = to_html(Engine.run_on(facts))
    assert "warden-lab-dev" in html
    assert "sev-critical" in html
    assert "sev-high" in html


def test_dashboard_empty():
    html = to_html([])
    assert "No issues detected" in html


def test_dashboard_escapes_html():
    from warden_agent.models import Finding, Severity

    nasty = Finding(
        id="x:1",
        title="<script>alert(1)</script>",
        severity=Severity.LOW,
        resource_type="t",
        resource_id="r",
        region="us-east-1",
        description="d",
    )
    html = to_html([nasty])
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
