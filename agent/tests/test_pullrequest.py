import os

import pytest

from warden_agent.engine import Engine
from warden_agent.remediation import pullrequest
from warden_agent.remediation.pullrequest import GitHubError, RemediationPlan


class FakeResp:
    def __init__(self, status_code, data=None, text=""):
        self.status_code = status_code
        self._data = data or {}
        self.text = text

    def json(self):
        return self._data


class FakeSession:
    """Records calls and returns canned successful responses."""

    def __init__(self):
        self.calls = []

    def get(self, url, headers=None):
        self.calls.append(("GET", url))
        return FakeResp(200, {"object": {"sha": "basesha"}})

    def post(self, url, headers=None, json=None):
        self.calls.append(("POST", url, json))
        if url.endswith("/pulls"):
            return FakeResp(201, {"html_url": "https://github.com/o/r/pull/1"})
        return FakeResp(201, {})

    def put(self, url, headers=None, json=None):
        self.calls.append(("PUT", url, json))
        return FakeResp(201, {})


def test_build_plan_has_files_and_body(facts):
    plan = pullrequest.build_plan(Engine.run_on(facts))
    assert plan is not None
    assert len(plan.files) >= 3
    assert plan.branch.startswith("warden/remediation-")
    assert "Review before merging" in plan.pr_body


def test_build_plan_none_when_no_findings():
    assert pullrequest.build_plan([]) is None


def test_write_plan_locally(tmp_path, facts):
    plan = pullrequest.build_plan(Engine.run_on(facts))
    written = pullrequest.write_plan_locally(plan, str(tmp_path))
    assert any(p.endswith("PULL_REQUEST.md") for p in written)
    assert all(os.path.exists(p) for p in written)


def test_open_pull_request_happy_path(facts):
    plan = pullrequest.build_plan(Engine.run_on(facts))
    sess = FakeSession()
    url = pullrequest.open_pull_request(plan, repo="o/r", token="t", session=sess)
    assert url == "https://github.com/o/r/pull/1"
    methods = [c[0] for c in sess.calls]
    assert methods[0] == "GET"  # resolve base branch first
    puts = [c for c in sess.calls if c[0] == "PUT"]
    assert len(puts) == len(plan.files)  # one file upload per fix


def test_open_pull_request_raises_on_api_error():
    plan = RemediationPlan(branch="b", pr_title="t", pr_body="x", files=(("a.tf", "c"),))

    class BadSession:
        def get(self, url, headers=None):
            return FakeResp(404, text="not found")

    with pytest.raises(GitHubError):
        pullrequest.open_pull_request(plan, repo="o/r", token="t", session=BadSession())
