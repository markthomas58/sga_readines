import os
import tempfile
import time

from unittest.mock import patch, MagicMock

from sga_readiness.checker import run_checks
from sga_readiness.checks import Check
from sga_readiness.models import CheckResult, CheckStatus


def _write_yaml(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return f.name


def test_run_checks_all_pass():
    path = _write_yaml("""
checks:
  - name: "MY_VAR set"
    type: config
    env_var: "MY_VAR"
""")
    try:
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            report = run_checks(path)

        assert report.passed is True
        assert len(report.results) == 1
        assert report.results[0].status == CheckStatus.PASS
    finally:
        os.unlink(path)


def test_run_checks_with_failure():
    path = _write_yaml("""
checks:
  - name: "MISSING_VAR"
    type: config
    env_var: "DEFINITELY_NOT_SET_12345"
""")
    try:
        with patch.dict(os.environ, {}, clear=True):
            report = run_checks(path)

        assert report.passed is False
        assert report.results[0].status == CheckStatus.FAIL
    finally:
        os.unlink(path)


def test_run_checks_multiple():
    path = _write_yaml("""
checks:
  - name: "VAR1"
    type: config
    env_var: "VAR1"
  - name: "VAR2"
    type: config
    env_var: "VAR2"
""")
    try:
        with patch.dict(os.environ, {"VAR1": "a", "VAR2": "b"}):
            report = run_checks(path)

        assert report.passed is True
        assert len(report.results) == 2
    finally:
        os.unlink(path)


class _SlowCheck(Check):
    """A check that sleeps for a given duration, for testing parallelism."""

    def __init__(self, name: str, sleep_seconds: float = 0.2):
        super().__init__(name)
        self.sleep_seconds = sleep_seconds

    def run(self) -> CheckResult:
        time.sleep(self.sleep_seconds)
        return CheckResult(name=self.name, status=CheckStatus.PASS)


def test_parallel_preserves_order():
    """Parallel execution returns results in original check order."""
    checks = [_SlowCheck(f"check-{i}", sleep_seconds=0.05) for i in range(5)]

    with patch("sga_readiness.checker.load_config", return_value=checks):
        report = run_checks("dummy.yaml", parallel=True)

    assert [r.name for r in report.results] == [f"check-{i}" for i in range(5)]


def test_sequential_execution():
    """parallel=False still works via the sequential path."""
    checks = [_SlowCheck(f"seq-{i}", sleep_seconds=0.01) for i in range(3)]

    with patch("sga_readiness.checker.load_config", return_value=checks):
        report = run_checks("dummy.yaml", parallel=False)

    assert len(report.results) == 3
    assert all(r.status == CheckStatus.PASS for r in report.results)
    assert [r.name for r in report.results] == [f"seq-{i}" for i in range(3)]


def test_parallel_faster_than_sequential():
    """Parallel execution of I/O-bound checks is faster than sequential."""
    n = 5
    sleep_per_check = 0.2
    checks = [_SlowCheck(f"slow-{i}", sleep_seconds=sleep_per_check) for i in range(n)]

    with patch("sga_readiness.checker.load_config", return_value=checks):
        t0 = time.monotonic()
        report_par = run_checks("dummy.yaml", parallel=True)
        parallel_time = time.monotonic() - t0

    assert report_par.passed is True
    # Sequential would take n * sleep_per_check = 1.0s.
    # Parallel should complete well under that.
    assert parallel_time < n * sleep_per_check * 0.7
